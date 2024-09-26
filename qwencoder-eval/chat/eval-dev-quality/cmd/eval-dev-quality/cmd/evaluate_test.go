package cmd

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strconv"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate"
	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	evaluatetask "github.com/symflower/eval-dev-quality/evaluate/task"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	providertesting "github.com/symflower/eval-dev-quality/provider/testing"
	"github.com/symflower/eval-dev-quality/task"
	"github.com/symflower/eval-dev-quality/tools"
	toolstesting "github.com/symflower/eval-dev-quality/tools/testing"
	"github.com/symflower/eval-dev-quality/util"
)

// validateReportLinks checks if the Markdown report data contains all the links to other relevant report files.
func validateReportLinks(t *testing.T, data string, modelLogNames []string) {
	assert.Contains(t, data, "](./categories.svg)")
	assert.Contains(t, data, "](./evaluation.csv)")
	assert.Contains(t, data, "evaluation.log")
	for _, m := range modelLogNames {
		assert.Contains(t, data, fmt.Sprintf("](./%s/)", m))
	}
}

// validateSVGContent checks if the SVG data contains all given categories and an axis label for the maximal model count.
func validateSVGContent(t *testing.T, data string, categories []*metrics.AssessmentCategory, maxModelCount uint) {
	for _, category := range categories {
		assert.Contains(t, data, fmt.Sprintf("%s</text>", category.Name))
	}
	assert.Contains(t, data, fmt.Sprintf("%d</text>", maxModelCount))
}

func atoiUint64(t *testing.T, s string) uint64 {
	value, err := strconv.ParseUint(s, 10, 64)
	assert.NoErrorf(t, err, "parsing unsigned integer from: %q", s)

	return uint64(value)
}

// extractMetricsMatch is a regular expression that maps metrics to it's subgroups.
type extractMetricsMatch *regexp.Regexp

// extractMetricsLogsMatch is a regular expression to extract metrics from log messages.
var extractMetricsLogsMatch = extractMetricsMatch(regexp.MustCompile(`score=(\d+), coverage=(\d+), files-executed=(\d+), files-executed-maximum-reachable=(\d+), generate-tests-for-file-character-count=(\d+), processing-time=(\d+), response-character-count=(\d+), response-no-error=(\d+), response-no-excess=(\d+), response-with-code=(\d+)`))

// extractMetricsCSVMatch is a regular expression to extract metrics from CSV rows.
var extractMetricsCSVMatch = extractMetricsMatch(regexp.MustCompile(`(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)`))

// extractMetrics extracts multiple assessment metrics from the given string according to a given regular expression.
func extractMetrics(t *testing.T, regex extractMetricsMatch, data string) (assessments []metrics.Assessments, scores []uint64) {
	matches := (*regexp.Regexp)(regex).FindAllStringSubmatch(data, -1)

	for _, match := range matches {
		assessments = append(assessments, metrics.Assessments{
			metrics.AssessmentKeyCoverage:                           atoiUint64(t, match[2]),
			metrics.AssessmentKeyFilesExecuted:                      atoiUint64(t, match[3]),
			metrics.AssessmentKeyFilesExecutedMaximumReachable:      atoiUint64(t, match[4]),
			metrics.AssessmentKeyGenerateTestsForFileCharacterCount: atoiUint64(t, match[5]),
			metrics.AssessmentKeyProcessingTime:                     atoiUint64(t, match[6]),
			metrics.AssessmentKeyResponseCharacterCount:             atoiUint64(t, match[7]),
			metrics.AssessmentKeyResponseNoError:                    atoiUint64(t, match[8]),
			metrics.AssessmentKeyResponseNoExcess:                   atoiUint64(t, match[9]),
			metrics.AssessmentKeyResponseWithCode:                   atoiUint64(t, match[10]),
		})
		scores = append(scores, atoiUint64(t, match[1]))
	}

	return assessments, scores
}

func validateMetrics(t *testing.T, regex *regexp.Regexp, data string, expectedAssessments []metrics.Assessments, expectedScores []uint64) (actual []metrics.Assessments) {
	require.Equal(t, len(expectedAssessments), len(expectedScores), "expected assessment and scores length")

	actualAssessments, actualScores := extractMetrics(t, regex, data)
	require.Equal(t, len(expectedAssessments), len(actualAssessments), "expected and actual assessment length")
	for i := range actualAssessments {
		metricstesting.AssertAssessmentsEqual(t, expectedAssessments[i], actualAssessments[i])
	}
	assert.Equal(t, expectedScores, actualScores)

	return actualAssessments
}

func TestEvaluateExecute(t *testing.T) {
	if osutil.IsLinux() {
		toolstesting.RequiresTool(t, tools.NewOllama())
	}
	toolstesting.RequiresTool(t, tools.NewSymflower())

	type testCase struct {
		Name string

		Before func(t *testing.T, logger *log.Logger, resultPath string)
		After  func(t *testing.T, logger *log.Logger, resultPath string)

		// Arguments holds the command line arguments.
		// REMARK The "--testdata" and "--result-directory" options are set within the validation logic but specifying them in the argument list here overwrites them.
		Arguments []string

		ExpectedOutputValidate func(t *testing.T, output string, resultPath string)
		ExpectedResultFiles    map[string]func(t *testing.T, filePath string, data string)
		ExpectedPanicContains  string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()

			logOutput, logger := log.Buffer()
			defer func() {
				log.CloseOpenLogFiles()

				if t.Failed() {
					t.Logf("Logging output: %s", logOutput.String())
				}
			}()

			if tc.Before != nil {
				tc.Before(t, logger, temporaryPath)
			}
			if tc.After != nil {
				defer tc.After(t, logger, temporaryPath)
			}

			// Add the temporary path as prefix to the configuration file path if needed.
			if i := slices.Index(tc.Arguments, "--configuration"); i >= 0 {
				tc.Arguments[i+1] = filepath.Join(temporaryPath, tc.Arguments[i+1])
			}

			arguments := append([]string{
				"evaluate",
				"--result-path", filepath.Join(temporaryPath, "result-directory"),
				"--testdata", filepath.Join("..", "..", "..", "testdata"),
			}, tc.Arguments...) // Add the test case arguments last which allows overwriting "--testdata" and "--result-path" as only the last option counts if specified multiple times (https://pkg.go.dev/github.com/jessevdk/go-flags).

			if tc.ExpectedPanicContains == "" {
				assert.NotPanics(t, func() {
					Execute(logger, arguments)
				})
			} else {
				didPanic := true
				var recovered any
				func() {
					defer func() {
						recovered = recover()
					}()

					Execute(logger, arguments)

					didPanic = false
				}()
				assert.True(t, didPanic)
				assert.Contains(t, recovered, tc.ExpectedPanicContains)
			}

			if tc.ExpectedOutputValidate != nil {
				tc.ExpectedOutputValidate(t, logOutput.String(), temporaryPath)
			}

			actualResultFiles, err := osutil.FilesRecursive(temporaryPath)
			require.NoError(t, err)
			if len(tc.ExpectedResultFiles) == 0 && len(actualResultFiles) == 0 {
				return
			}

			for i, p := range actualResultFiles {
				actualResultFiles[i], err = filepath.Rel(temporaryPath, p)
				require.NoError(t, err)
			}
			sort.Strings(actualResultFiles)
			expectedResultFiles := make([]string, 0, len(tc.ExpectedResultFiles))
			for filePath, validate := range tc.ExpectedResultFiles {
				expectedResultFiles = append(expectedResultFiles, filePath)

				if validate != nil {
					data, err := os.ReadFile(filepath.Join(temporaryPath, filePath))
					if assert.NoError(t, err) {
						validate(t, filePath, string(data))
					}
				}
			}
			sort.Strings(expectedResultFiles)
			assert.Equal(t, expectedResultFiles, actualResultFiles)
		})
	}

	t.Run("Language filter", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Single",

			Arguments: []string{
				"--language", "golang",
				"--model", "symflower/symbolic-execution",
				"--repository", filepath.Join("golang", "plain"),
			},

			ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
				actualAssessments := validateMetrics(t, extractMetricsLogsMatch, output, []metrics.Assessments{
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      20,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
						metrics.AssessmentKeyResponseNoExcess:              2,
						metrics.AssessmentKeyResponseWithCode:              2,
					},
				}, []uint64{28})
				// Assert non-deterministic behavior.
				assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(508))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(508))
				assert.Equal(t, 1, strings.Count(output, "Evaluation score for"))
			},
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				filepath.Join("result-directory", "categories.svg"): func(t *testing.T, filePath, data string) {
					validateSVGContent(t, data, []*metrics.AssessmentCategory{metrics.AssessmentCategoryCodeNoExcess}, 1)
				},
				filepath.Join("result-directory", "config.json"): nil,
				filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					assert.Greater(t, actualAssessments[1][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
					assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
				},
				filepath.Join("result-directory", "evaluation.log"): nil,
				filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath, data string) {
					validateReportLinks(t, data, []string{"symflower_symbolic-execution"})
				},
				filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
			},
		})
		validate(t, &testCase{
			Name: "Multiple",

			Arguments: []string{
				"--model", "symflower/symbolic-execution",
				"--repository", filepath.Join("golang", "plain"),
				"--repository", filepath.Join("java", "plain"),
			},

			ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
				actualAssessments := validateMetrics(t, extractMetricsLogsMatch, output, []metrics.Assessments{
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      40,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
						metrics.AssessmentKeyResponseNoExcess:              4,
						metrics.AssessmentKeyResponseWithCode:              4,
					},
				}, []uint64{56})
				// Assert non-deterministic behavior.
				assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(786))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(786))
				assert.Equal(t, 1, strings.Count(output, "Evaluation score for"))
			},
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				filepath.Join("result-directory", "categories.svg"): func(t *testing.T, filePath, data string) {
					validateSVGContent(t, data, []*metrics.AssessmentCategory{metrics.AssessmentCategoryCodeNoExcess}, 1)
				},
				filepath.Join("result-directory", "config.json"): nil,
				filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14, 14, 14})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					assert.Greater(t, actualAssessments[1][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
					assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					assert.Greater(t, actualAssessments[2][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[2][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(139))
					assert.Equal(t, actualAssessments[2][metrics.AssessmentKeyResponseCharacterCount], uint64(139))
					assert.Greater(t, actualAssessments[3][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[3][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(139))
					assert.Equal(t, actualAssessments[3][metrics.AssessmentKeyResponseCharacterCount], uint64(139))
				},
				filepath.Join("result-directory", "evaluation.log"): nil,
				filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath, data string) {
					validateReportLinks(t, data, []string{"symflower_symbolic-execution"})
				},
				filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Contains(t, data, "coverage objects: [{")
				},
				filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "java", "java", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Contains(t, data, "coverage objects: [{")
				},
			},
		})
	})

	t.Run("Repository filter", func(t *testing.T) {
		t.Run("Single", func(t *testing.T) {
			validate(t, &testCase{
				Name: "Single Language",

				Arguments: []string{
					"--language", "golang",
					"--model", "symflower/symbolic-execution",
					"--repository", filepath.Join("golang", "plain"),
				},

				ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
					actualAssessments := validateMetrics(t, extractMetricsLogsMatch, output, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      20,
							metrics.AssessmentKeyFilesExecuted:                 2,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               2,
							metrics.AssessmentKeyResponseNoExcess:              2,
							metrics.AssessmentKeyResponseWithCode:              2,
						},
					}, []uint64{28})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(508))
					assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(508))
					assert.Equal(t, 1, strings.Count(output, "Evaluation score for"))
				},
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					filepath.Join("result-directory", "categories.svg"): func(t *testing.T, filePath, data string) {
						validateSVGContent(t, data, []*metrics.AssessmentCategory{metrics.AssessmentCategoryCodeNoExcess}, 1)
					},
					filepath.Join("result-directory", "config.json"): nil,
					filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
						actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
							metrics.Assessments{
								metrics.AssessmentKeyCoverage:                      10,
								metrics.AssessmentKeyFilesExecuted:                 1,
								metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
								metrics.AssessmentKeyResponseNoError:               1,
								metrics.AssessmentKeyResponseNoExcess:              1,
								metrics.AssessmentKeyResponseWithCode:              1,
							},
							metrics.Assessments{
								metrics.AssessmentKeyCoverage:                      10,
								metrics.AssessmentKeyFilesExecuted:                 1,
								metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
								metrics.AssessmentKeyResponseNoError:               1,
								metrics.AssessmentKeyResponseNoExcess:              1,
								metrics.AssessmentKeyResponseWithCode:              1,
							},
						}, []uint64{14, 14})
						// Assert non-deterministic behavior.
						assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
						assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
						assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
						assert.Greater(t, actualAssessments[1][metrics.AssessmentKeyProcessingTime], uint64(0))
						assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
						assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					},
					filepath.Join("result-directory", "evaluation.log"): nil,
					filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath, data string) {
						validateReportLinks(t, data, []string{"symflower_symbolic-execution"})
					},
					filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
				},
			})
			validate(t, &testCase{
				Name: "Multiple Languages",

				Arguments: []string{
					"--model", "symflower/symbolic-execution",
					"--repository", filepath.Join("golang", "plain"),
				},

				ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
					assert.Regexp(t, `Evaluation score for "symflower/symbolic-execution" \("code-no-excess"\): score=28, coverage=20, files-executed=2, files-executed-maximum-reachable=2, generate-tests-for-file-character-count=508, processing-time=\d+, response-character-count=508, response-no-error=2, response-no-excess=2, response-with-code=2`, output)
					assert.Equal(t, 1, strings.Count(output, "Evaluation score for"))
				},
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					filepath.Join("result-directory", "categories.svg"): func(t *testing.T, filePath, data string) {
						validateSVGContent(t, data, []*metrics.AssessmentCategory{metrics.AssessmentCategoryCodeNoExcess}, 1)
					},
					filepath.Join("result-directory", "config.json"): nil,
					filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
						actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
							metrics.Assessments{
								metrics.AssessmentKeyCoverage:                      10,
								metrics.AssessmentKeyFilesExecuted:                 1,
								metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
								metrics.AssessmentKeyResponseNoError:               1,
								metrics.AssessmentKeyResponseNoExcess:              1,
								metrics.AssessmentKeyResponseWithCode:              1,
							},
							metrics.Assessments{
								metrics.AssessmentKeyCoverage:                      10,
								metrics.AssessmentKeyFilesExecuted:                 1,
								metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
								metrics.AssessmentKeyResponseNoError:               1,
								metrics.AssessmentKeyResponseNoExcess:              1,
								metrics.AssessmentKeyResponseWithCode:              1,
							},
						}, []uint64{14, 14})
						// Assert non-deterministic behavior.
						assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
						assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
						assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
						assert.Greater(t, actualAssessments[1][metrics.AssessmentKeyProcessingTime], uint64(0))
						assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
						assert.Equal(t, actualAssessments[1][metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					},
					filepath.Join("result-directory", "evaluation.log"): nil,
					filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath, data string) {
						validateReportLinks(t, data, []string{"symflower_symbolic-execution"})
					},
					filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
				},
			})
		})
	})
	t.Run("Model filter", func(t *testing.T) {
		t.Run("openrouter.ai", func(t *testing.T) {
			validate(t, &testCase{
				Name: "Unavailable",

				Arguments: []string{
					"--model", "openrouter/auto",
					"--tokens", "openrouter:",
				},

				ExpectedOutputValidate: func(t *testing.T, output, resultPath string) {
					assert.Contains(t, output, "Skipping unavailable provider \"openrouter\"")
				},
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					filepath.Join("result-directory", "evaluation.log"): nil,
				},
				ExpectedPanicContains: "ERROR: model openrouter/auto does not exist",
			})
		})
		t.Run("Ollama", func(t *testing.T) {
			if !osutil.IsLinux() {
				t.Skipf("Installation of Ollama is not supported on this OS")
			}

			{
				validate(t, &testCase{
					Name: "Pulled Model",

					Arguments: []string{
						"--language", "golang",
						"--model", "ollama/" + providertesting.OllamaTestModel,
						"--repository", filepath.Join("golang", "plain"),
					},

					ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
						filepath.Join("result-directory", "categories.svg"): nil,
						filepath.Join("result-directory", "config.json"):    nil,
						filepath.Join("result-directory", "evaluation.csv"): nil,
						filepath.Join("result-directory", "evaluation.log"): func(t *testing.T, filePath, data string) {
							// Since the model is non-deterministic, we can only assert that the model did at least not error.
							assert.Contains(t, data, fmt.Sprintf(`Evaluation score for "ollama/%s"`, providertesting.OllamaTestModel))
							assert.Contains(t, data, "response-no-error=2")
							assert.Contains(t, data, "preloading model")
							assert.Contains(t, data, "unloading model")
						},
						filepath.Join("result-directory", "README.md"): nil,
						filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "ollama_"+log.CleanModelNameForFileSystem(providertesting.OllamaTestModel), "golang", "golang", "plain", "evaluation.log"): nil,
						filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "ollama_"+log.CleanModelNameForFileSystem(providertesting.OllamaTestModel), "golang", "golang", "plain", "response-1.log"): nil,
					},
					ExpectedOutputValidate: func(t *testing.T, output, resultPath string) {
						assert.Contains(t, output, `Starting services for provider "ollama"`)
					},
				})
			}
			{
				validate(t, &testCase{
					Name: "Ollama services are not started",

					Arguments: []string{
						"--language", "golang",
						"--model", "symflower/symbolic-execution",
						"--repository", filepath.Join("golang", "plain"),
					},

					ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
						filepath.Join("result-directory", "categories.svg"): nil,
						filepath.Join("result-directory", "config.json"):    nil,
						filepath.Join("result-directory", "evaluation.csv"): nil,
						filepath.Join("result-directory", "evaluation.log"): nil,
						filepath.Join("result-directory", "README.md"):      nil,
						filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
					},
					ExpectedOutputValidate: func(t *testing.T, output, resultPath string) {
						assert.NotContains(t, output, `Starting services for provider "ollama"`)
					},
				})
			}
		})
		t.Run("OpenAI API", func(t *testing.T) {
			if !osutil.IsLinux() {
				t.Skipf("Installation of Ollama is not supported on this OS")
			}

			{
				var shutdown func() (err error)
				defer func() {
					if shutdown != nil {
						require.NoError(t, shutdown())
					}
				}()
				ollamaOpenAIAPIUrl, err := url.JoinPath(tools.OllamaURL, "v1")
				require.NoError(t, err)
				validate(t, &testCase{
					Name: "Ollama",

					Before: func(t *testing.T, logger *log.Logger, resultPath string) {
						var err error
						shutdown, err = tools.OllamaStart(logger, tools.OllamaPath, tools.OllamaURL)
						require.NoError(t, err)

						require.NoError(t, tools.OllamaPull(logger, tools.OllamaPath, tools.OllamaURL, providertesting.OllamaTestModel))
					},

					Arguments: []string{
						"--language", "golang",
						"--urls", "custom-ollama:" + ollamaOpenAIAPIUrl,
						"--model", "custom-ollama/" + providertesting.OllamaTestModel,
						"--repository", filepath.Join("golang", "plain"),
					},

					ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
						filepath.Join("result-directory", "categories.svg"): nil,
						filepath.Join("result-directory", "config.json"):    nil,
						filepath.Join("result-directory", "evaluation.csv"): nil,
						filepath.Join("result-directory", "evaluation.log"): func(t *testing.T, filePath, data string) {
							// Since the model is non-deterministic, we can only assert that the model did at least not error.
							assert.Contains(t, data, fmt.Sprintf(`Evaluation score for "custom-ollama/%s"`, providertesting.OllamaTestModel))
							assert.Contains(t, data, "response-no-error=2")
						},
						filepath.Join("result-directory", "README.md"): nil,
						filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "custom-ollama_"+log.CleanModelNameForFileSystem(providertesting.OllamaTestModel), "golang", "golang", "plain", "evaluation.log"): nil,
						filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "custom-ollama_"+log.CleanModelNameForFileSystem(providertesting.OllamaTestModel), "golang", "golang", "plain", "response-1.log"): nil,
					},
				})
			}
		})
	})

	t.Run("Runs", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Multiple",

			Arguments: []string{
				"--model", "symflower/symbolic-execution",
				"--repository", filepath.Join("golang", "plain"),
				"--runs=3",
			},

			ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
				actualAssessments := validateMetrics(t, extractMetricsLogsMatch, output, []metrics.Assessments{
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      60,
						metrics.AssessmentKeyFilesExecuted:                 6,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 6,
						metrics.AssessmentKeyResponseNoError:               6,
						metrics.AssessmentKeyResponseNoExcess:              6,
						metrics.AssessmentKeyResponseWithCode:              6,
					},
				}, []uint64{84})
				// Assert non-deterministic behavior.
				assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(1524))
				assert.Equal(t, actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount], uint64(1524))
				assert.Equal(t, 1, strings.Count(output, "Evaluation score for"))
			},
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				filepath.Join("result-directory", "categories.svg"): nil,
				filepath.Join("result-directory", "config.json"):    nil,
				filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14, 14, 14, 14, 14})
					// Assert non-deterministic behavior.
					for _, assessment := range actualAssessments {
						assert.Greater(t, assessment[metrics.AssessmentKeyProcessingTime], uint64(0))
						assert.Equal(t, assessment[metrics.AssessmentKeyGenerateTestsForFileCharacterCount], uint64(254))
						assert.Equal(t, assessment[metrics.AssessmentKeyResponseCharacterCount], uint64(254))
					}
				},
				filepath.Join("result-directory", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Contains(t, data, "Run 1/3")
					assert.Contains(t, data, "Run 2/3")
					assert.Contains(t, data, "Run 3/3")
				},
				filepath.Join("result-directory", "README.md"): nil,
				filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 3, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},
			},
		})
	})

	t.Run("Runtime", func(t *testing.T) {
		// Skip containerized runtime tests if special cases.
		if osutil.IsWindows() {
			t.Skip("Docker runtime not supported on Windows")
		} else if _, err := exec.LookPath("docker"); err != nil {
			t.Skip("Docker runtime not found")
		}

		// Pull the image built for this test instead of building it again.
		dockerImage := ""
		{
			// Get current branch name.
			_, logger := log.Buffer()
			branch, err := util.CommandWithResult(context.Background(), logger, &util.Command{
				Command: []string{
					"git",
					"rev-parse",
					"--short",
					"HEAD",
				},
			})
			require.NoError(t, err)

			if os.Getenv("GITHUB_ACTIONS") == "true" {
				dockerImage = "ghcr.io/symflower/eval-dev-quality:" + strings.TrimSpace(branch)

				// Pull the pre built image.
				_, err = util.CommandWithResult(context.Background(), logger, &util.Command{
					Command: []string{
						"docker",
						"pull",
						dockerImage,
					},
				})
				require.NoError(t, err)
			} else {
				dockerImage = "eval-dev-quality:" + strings.TrimSpace(branch)

				t.Log("Building docker image locally")
				// Build the image locally.
				_, err = util.CommandWithResult(context.Background(), logger, &util.Command{
					Command: []string{
						"docker",
						"build",
						osutil.EnvOrDefault("ROOT_DIR", "."),
						"-t", dockerImage,
					},
				})
				require.NoError(t, err)
			}
		}

		validate(t, &testCase{
			Name: "Docker",

			Arguments: []string{
				"--runtime", "docker",
				"--model", "symflower/symbolic-execution",
				"--model", "symflower/symbolic-execution",
				"--model", "symflower/symbolic-execution",
				"--testdata", "testdata/", // Our own tests set the "testdata" argument to the temporary directory that they create. This temporary directory does not exist in docker, so set the "testdata" manually here to overrule the testing behavior and use the original one.
				"--repository", filepath.Join("golang", "plain"),
				"--repository", filepath.Join("java", "plain"),
				"--runs=1",
				"--parallel=3",
				"--runtime-image=" + dockerImage,
			},

			ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
				actualAssessments := validateMetrics(t, extractMetricsLogsMatch, output, []metrics.Assessments{
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      40,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
						metrics.AssessmentKeyResponseNoExcess:              4,
						metrics.AssessmentKeyResponseWithCode:              4,
					},
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      40,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
						metrics.AssessmentKeyResponseNoExcess:              4,
						metrics.AssessmentKeyResponseWithCode:              4,
					},
					metrics.Assessments{
						metrics.AssessmentKeyCoverage:                      40,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
						metrics.AssessmentKeyResponseNoExcess:              4,
						metrics.AssessmentKeyResponseWithCode:              4,
					},
				}, []uint64{56, 56, 56})
				// Assert non-deterministic behavior.
				assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
				assert.Equal(t, uint64(786), actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount])
				assert.Equal(t, uint64(786), actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount])
				assert.Equal(t, 3, strings.Count(output, "Evaluation score for"))
			},
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				filepath.Join("result-directory", "evaluation.log"): nil,
				filepath.Join("result-directory", "config.json"):    nil,

				// Parallel run 1
				filepath.Join("result-directory", "symflower_symbolic-execution", "categories.svg"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution", "config.json"):    nil,
				filepath.Join("result-directory", "symflower_symbolic-execution", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14, 14, 14})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount])
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount])
				},
				filepath.Join("result-directory", "symflower_symbolic-execution", "evaluation.log"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution", "README.md"):      nil,
				filepath.Join("result-directory", "symflower_symbolic-execution", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},
				filepath.Join("result-directory", "symflower_symbolic-execution", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "java", "java", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},

				// Parallel run 2
				filepath.Join("result-directory", "symflower_symbolic-execution_1", "categories.svg"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_1", "config.json"):    nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_1", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14, 14, 14})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount])
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount])
				},
				filepath.Join("result-directory", "symflower_symbolic-execution_1", "evaluation.log"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_1", "README.md"):      nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_1", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},
				filepath.Join("result-directory", "symflower_symbolic-execution_1", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "java", "java", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},

				// Parallel run 3
				filepath.Join("result-directory", "symflower_symbolic-execution_2", "categories.svg"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_2", "config.json"):    nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_2", "evaluation.csv"): func(t *testing.T, filePath, data string) {
					actualAssessments := validateMetrics(t, extractMetricsCSVMatch, data, []metrics.Assessments{
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
						metrics.Assessments{
							metrics.AssessmentKeyCoverage:                      10,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
							metrics.AssessmentKeyResponseNoError:               1,
							metrics.AssessmentKeyResponseNoExcess:              1,
							metrics.AssessmentKeyResponseWithCode:              1,
						},
					}, []uint64{14, 14, 14, 14})
					// Assert non-deterministic behavior.
					assert.Greater(t, actualAssessments[0][metrics.AssessmentKeyProcessingTime], uint64(0))
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyGenerateTestsForFileCharacterCount])
					assert.Equal(t, uint64(254), actualAssessments[0][metrics.AssessmentKeyResponseCharacterCount])
				},
				filepath.Join("result-directory", "symflower_symbolic-execution_2", "evaluation.log"): nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_2", "README.md"):      nil,
				filepath.Join("result-directory", "symflower_symbolic-execution_2", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},
				filepath.Join("result-directory", "symflower_symbolic-execution_2", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "java", "java", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
					assert.Equal(t, 1, strings.Count(data, `Evaluating model "symflower/symbolic-execution"`))
				},
			},
		})
		{
			relativeResultDirectory := "temp:test:results"
			validate(t, &testCase{
				Name: "Docker with colon in relative results path",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					t.Cleanup(func() {
						if _, err := os.Stat(relativeResultDirectory); err != nil {
							if os.IsNotExist(err) {
								return
							}
							require.NoError(t, err)
						}

						require.NoError(t, os.RemoveAll(relativeResultDirectory))
					})
				},

				Arguments: []string{
					"--runtime", "docker",
					"--model", "symflower/symbolic-execution",
					"--testdata", "testdata/", // Our own tests set the "testdata" argument to the temporary directory that they create. This temporary directory does not exist in docker, so set the "testdata" manually here to overrule the testing behavior and use the original one.
					"--repository", filepath.Join("golang", "plain"),
					"--runs=1",
					"--parallel=1",
					"--runtime-image=" + dockerImage,
					"--result-path", relativeResultDirectory,
				},

				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					assert.FileExists(t, filepath.Join(relativeResultDirectory, "evaluation.log"))
					symflowerLogFilePath := filepath.Join(relativeResultDirectory, "symflower_symbolic-execution", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log")
					require.FileExists(t, symflowerLogFilePath)
					data, err := os.ReadFile(symflowerLogFilePath)
					require.NoError(t, err)
					assert.Contains(t, string(data), `Evaluating model "symflower/symbolic-execution"`)
				},
			})
		}
	})

	// This case checks a beautiful bug where the Markdown export crashed when the current working directory contained a README.md file. While this is not the case during the tests (as the current work directory is the directory of this file), it certainly caused problems when our binary was executed from the repository root (which of course contained a README.md). Therefore, we sadly have to modify the current work directory right within the tests of this case to reproduce the problem and fix it forever.
	validate(t, &testCase{
		Name: "Current work directory contains a README.md",

		Before: func(t *testing.T, logger *log.Logger, resultPath string) {
			if err := os.Remove("README.md"); err != nil {
				if osutil.IsWindows() {
					require.Contains(t, err.Error(), "The system cannot find the file specified")
				} else {
					require.Contains(t, err.Error(), "no such file or directory")
				}
			}
			require.NoError(t, os.WriteFile("README.md", []byte(""), 0644))
		},
		After: func(t *testing.T, logger *log.Logger, resultPath string) {
			require.NoError(t, os.Remove("README.md"))
		},

		Arguments: []string{
			"--language", "golang",
			"--model", "symflower/symbolic-execution",
			"--repository", filepath.Join("golang", "plain"),
		},

		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			filepath.Join("result-directory", "categories.svg"): nil,
			filepath.Join("result-directory", "config.json"):    nil,
			filepath.Join("result-directory", "evaluation.csv"): nil,
			filepath.Join("result-directory", "evaluation.log"): nil,
			filepath.Join("result-directory", "README.md"):      nil,
			filepath.Join("result-directory", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
		},
	})
	validate(t, &testCase{
		Name: "Don't overwrite results path if it already exists",

		Before: func(t *testing.T, logger *log.Logger, resultPath string) {
			require.NoError(t, os.Mkdir(filepath.Join(resultPath, "result-directory"), 0600))
		},

		Arguments: []string{
			"--language", "golang",
			"--model", "symflower/symbolic-execution",
			"--repository", filepath.Join("golang", "plain"),
		},

		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			filepath.Join("result-directory-0", "categories.svg"): nil,
			filepath.Join("result-directory-0", "config.json"):    nil,
			filepath.Join("result-directory-0", "evaluation.csv"): nil,
			filepath.Join("result-directory-0", "evaluation.log"): nil,
			filepath.Join("result-directory-0", "README.md"):      nil,
			filepath.Join("result-directory-0", string(evaluatetask.IdentifierWriteTests), "symflower_symbolic-execution", "golang", "golang", "plain", "evaluation.log"): nil,
		},
	})
}

func TestEvaluateInitialize(t *testing.T) {
	type testCase struct {
		Name string

		Before  func(t *testing.T, workingDirectory string)
		Command *Evaluate

		ValidateCommand       func(t *testing.T, command *Evaluate)
		ValidateContext       func(t *testing.T, context *evaluate.Context)
		ValidateConfiguration func(t *testing.T, config *EvaluationConfiguration)
		ValidateResults       func(t *testing.T, resultsPath string)
		ValidatePanic         string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			require.NotNil(t, tc.Command, "command must be non-nil")

			temporaryDirectory := t.TempDir()
			buffer, logger := log.Buffer()
			defer func() {
				log.CloseOpenLogFiles()

				if t.Failed() {
					t.Logf("Logs:\n%s", buffer.String())
				}
			}()

			if tc.Before != nil {
				tc.Before(t, temporaryDirectory)
			}

			if tc.Command.Configuration != "" {
				tc.Command.Configuration = filepath.Join(temporaryDirectory, tc.Command.Configuration)
			}

			tc.Command.logger = logger
			tc.Command.ResultPath = strings.ReplaceAll(tc.Command.ResultPath, "$TEMP_PATH", temporaryDirectory)

			var cleanup func()

			if tc.ValidatePanic != "" {
				assert.PanicsWithValue(t, tc.ValidatePanic, func() {
					_, _, cleanup = tc.Command.Initialize([]string{})
					defer cleanup()
				})

				return
			}

			var actualEvaluationContext *evaluate.Context
			var actualEvaluationConfiguration *EvaluationConfiguration
			assert.NotPanics(t, func() {
				actualEvaluationContext, actualEvaluationConfiguration, cleanup = tc.Command.Initialize([]string{})
				defer cleanup()
			})

			if tc.ValidateCommand != nil {
				tc.ValidateCommand(t, tc.Command)
			}
			if tc.ValidateContext != nil {
				require.NotNil(t, actualEvaluationContext)
				tc.ValidateContext(t, actualEvaluationContext)
			}
			if tc.ValidateConfiguration != nil {
				require.NotNil(t, actualEvaluationConfiguration)
				tc.ValidateConfiguration(t, actualEvaluationConfiguration)
			}
			if tc.ValidateResults != nil {
				tc.ValidateResults(t, temporaryDirectory)
			}
		})
	}

	// makeValidCommand is a helper to abstract all the default values that have to be set to make a command valid.
	makeValidCommand := func(modify func(command *Evaluate)) *Evaluate {
		c := &Evaluate{
			ExecutionTimeout: 1,
			Parallel:         1,
			QueryAttempts:    1,
			ResultPath:       filepath.Join("$TEMP_PATH", "result-directory"),
			Runs:             1,
			Runtime:          "local",
			TestdataPath:     filepath.Join("..", "..", "..", "testdata"),
		}

		if modify != nil {
			modify(c)
		}

		return c
	}

	validate(t, &testCase{
		Name: "Custom result directory is created",

		Command: makeValidCommand(func(command *Evaluate) {
			command.ResultPath = filepath.Join("$TEMP_PATH", "some-directory")
		}),

		ValidateResults: func(t *testing.T, resultsPath string) {
			assert.DirExists(t, filepath.Join(resultsPath, "some-directory"))
		},
	})
	validate(t, &testCase{
		Name: "Selecting no language defaults to all",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Languages = []string{}
		}),

		ValidateCommand: func(t *testing.T, command *Evaluate) {
			assert.Equal(t, []string{
				"golang",
				"java",
				"ruby",
			}, command.Languages)
		},
		ValidateContext: func(t *testing.T, context *evaluate.Context) {
			assert.Equal(t, []language.Language{
				language.Languages["golang"],
				language.Languages["java"],
				language.Languages["ruby"],
			}, context.Languages)
		},
	})
	validate(t, &testCase{
		Name: "Selecting no model defaults to all",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Models = []string{}
		}),

		// Could also select arbitrary Ollama or new Openrouter models so sanity check that at least symflower is there.
		ValidateCommand: func(t *testing.T, command *Evaluate) {
			assert.Contains(t, command.Models, "symflower/symbolic-execution")
		},
		ValidateContext: func(t *testing.T, context *evaluate.Context) {
			modelIDs := make([]string, len(context.Models))
			for i, model := range context.Models {
				modelIDs[i] = model.ID()
			}
			assert.Contains(t, modelIDs, "symflower/symbolic-execution")
		},
		ValidateConfiguration: func(t *testing.T, config *EvaluationConfiguration) {
			assert.Contains(t, config.Models.Available, "symflower/symbolic-execution")
			assert.Contains(t, config.Models.Selected, "symflower/symbolic-execution")
		},
	})
	validate(t, &testCase{
		Name: "Remove repository if language is not selected",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Repositories = []string{
				filepath.Join("golang", "light"),
				filepath.Join("java", "light"),
			}
			command.Languages = []string{
				"golang",
			}
		}),

		ValidateCommand: func(t *testing.T, command *Evaluate) {
			assert.Equal(t, []string{
				filepath.Join("golang", "light"),
				filepath.Join("golang", "plain"),
			}, command.Repositories)
		},
		ValidateContext: func(t *testing.T, context *evaluate.Context) {
			assert.Equal(t, []string{
				filepath.Join("golang", "light"),
				filepath.Join("golang", "plain"),
			}, context.RepositoryPaths)
		},
		ValidateConfiguration: func(t *testing.T, config *EvaluationConfiguration) {
			if assert.Contains(t, config.Repositories.Available, filepath.Join("golang", "plain")) {
				assert.Equal(t, []task.Identifier{evaluatetask.IdentifierWriteTests}, config.Repositories.Available[filepath.Join("golang", "plain")])
			}
			if assert.Contains(t, config.Repositories.Available, filepath.Join("java", "plain")) {
				assert.Equal(t, []task.Identifier{evaluatetask.IdentifierWriteTests}, config.Repositories.Available[filepath.Join("java", "plain")])
			}
			assert.Contains(t, config.Repositories.Selected, filepath.Join("golang", "plain"))
			assert.NotContains(t, config.Repositories.Selected, filepath.Join("java", "plain"))
		},
	})
	validate(t, &testCase{
		Name: "Remove language if no repository is selected",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Repositories = []string{
				filepath.Join("golang", "light"),
			}
			command.Languages = []string{
				"golang",
				"java",
			}
		}),

		ValidateCommand: func(t *testing.T, command *Evaluate) {
			assert.Equal(t, []string{
				"golang",
			}, command.Languages)
		},
		ValidateContext: func(t *testing.T, context *evaluate.Context) {
			assert.Equal(t, []language.Language{
				language.Languages["golang"],
			}, context.Languages)
		},
	})
	validate(t, &testCase{
		Name: "Selecting no repository defaults to all",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Repositories = []string{}
		}),

		ValidateCommand: func(t *testing.T, command *Evaluate) {
			var repositoryPathsRelative []string
			for _, language := range language.Languages {
				directories, err := os.ReadDir(filepath.Join("..", "..", "..", "testdata", language.ID()))
				require.NoError(t, err)
				for _, directory := range directories {
					repositoryPathsRelative = append(repositoryPathsRelative, filepath.Join(language.ID(), directory.Name()))
				}
			}
			for _, repositoryPathRelative := range repositoryPathsRelative {
				assert.Contains(t, command.Repositories, repositoryPathRelative)
			}
		},
	})
	validate(t, &testCase{
		Name: "Load configuration",

		Before: func(t *testing.T, workingDirectory string) {
			configurationContent := bytesutil.StringTrimIndentations(`
				{
					"Models": {
						"Selected": [
							"symflower/symbolic-execution"
						]
					},
					"Repositories": {
						"Selected": [
							"golang/plain",
							"java/plain"
						]
					}
				}
			`)
			require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "config.json"), []byte(configurationContent), 0700))
		},

		Command: makeValidCommand(func(command *Evaluate) {
			command.Configuration = "config.json"
		}),

		ValidateCommand: func(t *testing.T, command *Evaluate) {
			assert.Equal(t, []string{
				"symflower/symbolic-execution",
			}, command.Models)
			assert.Equal(t, []string{
				filepath.Join("golang", "plain"),
				filepath.Join("java", "plain"),
			}, command.Repositories)
		},
		ValidateConfiguration: func(t *testing.T, config *EvaluationConfiguration) {
			assert.Equal(t, []string{
				"symflower/symbolic-execution",
			}, config.Models.Selected)
			assert.Equal(t, []string{
				filepath.Join("golang", "plain"),
				filepath.Join("java", "plain"),
			}, config.Repositories.Selected)
		},
	})
	validate(t, &testCase{
		Name: "Local runtime does not allow parallel parameter",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Runtime = "local"
			command.Parallel = 2
		}),

		ValidatePanic: "the 'parallel' parameter can't be used with local execution",
	})
	validate(t, &testCase{
		Name: "Attempts parameter hast to be greater then zero",

		Command: makeValidCommand(func(command *Evaluate) {
			command.QueryAttempts = 0
		}),

		ValidatePanic: "number of configured query attempts must be greater than zero",
	})
	validate(t, &testCase{
		Name: "Execution timeout parameter hast to be greater then zero",

		Command: makeValidCommand(func(command *Evaluate) {
			command.ExecutionTimeout = 0
		}),

		ValidatePanic: "execution timeout for compilation and tests must be greater than zero",
	})
	validate(t, &testCase{
		Name: "Runs parameter hast to be greater then zero",

		Command: makeValidCommand(func(command *Evaluate) {
			command.Runs = 0
		}),

		ValidatePanic: "number of configured runs must be greater than zero",
	})

	t.Run("Docker", func(t *testing.T) {
		if osutil.IsDarwin() { // The MacOS runner on Github do not have "docker" in their path and would mess with the test.
			t.Skip("Unsupported OS")
		}

		validate(t, &testCase{
			Name: "Parallel parameter hast to be greater then zero",

			Command: makeValidCommand(func(command *Evaluate) {
				command.Runtime = "docker"
				command.Parallel = 0
			}),

			ValidatePanic: "the 'parallel' parameter has to be greater then zero",
		})
		validate(t, &testCase{
			Name: "Load configuration",

			Command: makeValidCommand(func(command *Evaluate) {
				command.Configuration = "config.json"
				command.Runtime = "docker"
			}),

			ValidatePanic: "the configuration file is not supported in containerized runtimes",
		})
	})
}
