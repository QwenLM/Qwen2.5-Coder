package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/symflower/eval-dev-quality/evaluate/report"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"
)

var claudeEvaluationCSVFileContent = bytesutil.StringTrimIndentations(`
	openrouter/anthropic/claude-2.0,golang,golang/light,write-tests,1,1,1,1,1,1,1,1,1,1,1
	openrouter/anthropic/claude-2.0,golang,golang/plain,write-tests,2,2,2,2,2,2,2,2,2,2,2
	openrouter/anthropic/claude-2.0,java,java/light,write-tests,3,3,3,3,3,3,3,3,3,3,3
	openrouter/anthropic/claude-2.0,java,java/plain,write-tests,4,4,4,4,4,4,4,4,4,4,4
`)

var gemmaEvaluationCSVFileContent = bytesutil.StringTrimIndentations(`
	openrouter/google/gemma-7b-it,golang,golang/light,write-tests,5,5,5,5,5,5,5,5,5,5,5
	openrouter/google/gemma-7b-it,golang,golang/plain,write-tests,6,6,6,6,6,6,6,6,6,6,6
	openrouter/google/gemma-7b-it,java,java/light,write-tests,7,7,7,7,7,7,7,7,7,7,7
	openrouter/google/gemma-7b-it,java,java/plain,write-tests,8,8,8,8,8,8,8,8,8,8,8
`)

var gpt4EvaluationCSVFileContent = bytesutil.StringTrimIndentations(`
	openrouter/openai/gpt-4,golang,golang/light,write-tests,9,9,9,9,9,9,9,9,9,9,9
	openrouter/openai/gpt-4,golang,golang/plain,write-tests,10,10,10,10,10,10,10,10,10,10,10
	openrouter/openai/gpt-4,java,java/light,write-tests,11,11,11,11,11,11,11,11,11,11,11
	openrouter/openai/gpt-4,java,java/plain,write-tests,12,12,12,12,12,12,12,12,12,12,12
`)

// validateMarkdownLinks checks if the Markdown report data contains all the links to other relevant report files.
func validateMarkdownLinks(t *testing.T, data string, modelLogNames []string, logFiles []string) {
	assert.Contains(t, data, "](./categories.svg)")
	assert.Contains(t, data, "](./evaluation.csv)")

	for _, logFile := range logFiles {
		assert.Contains(t, data, logFile)
	}
	for _, m := range modelLogNames {
		assert.Contains(t, data, fmt.Sprintf("](./%s/)", m))
	}
}

func TestReportExecute(t *testing.T) {
	type testCase struct {
		Name string

		Before func(t *testing.T, logger *log.Logger, workingDirectory string)

		Arguments func(workingDirectory string) []string

		ExpectedResultFiles   map[string]func(t *testing.T, filePath string, data string)
		ExpectedPanicContains string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()

			resultPath := filepath.Join(temporaryPath, "result-directory")
			require.NoError(t, osutil.MkdirAll(resultPath))

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

			arguments := append([]string{
				"report",
				"--result-path", resultPath,
			}, tc.Arguments(temporaryPath)...)

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

			actualResultFiles, err := osutil.FilesRecursive(temporaryPath)
			require.NoError(t, err)
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

	validate(t, &testCase{
		Name: "Evaluation path does not exist",

		Arguments: func(workingDirectory string) []string {
			return []string{
				"--evaluation-path", filepath.Join("some", "file.csv"),
			}
		},

		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			filepath.Join("result-directory", "evaluation.csv"): nil,
		},
		ExpectedPanicContains: `the path needs to end with "evaluation.csv"`,
	})
	validate(t, &testCase{
		Name: "Single file",

		Before: func(t *testing.T, logger *log.Logger, workingDirectory string) {
			evaluationFileContent := fmt.Sprintf("%s\n%s", strings.Join(report.EvaluationHeader(), ","), claudeEvaluationCSVFileContent)
			require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.csv"), []byte(evaluationFileContent), 0700))
			require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.log"), []byte(`log`), 0700))
		},

		Arguments: func(workingDirectory string) []string {
			return []string{
				"--evaluation-path", filepath.Join(workingDirectory, "evaluation.csv"),
			}
		},

		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			"evaluation.csv": nil,
			filepath.Join("result-directory", "categories.svg"): nil,
			filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath string, data string) {
				validateMarkdownLinks(t, data, []string{"openrouter_anthropic_claude-2.0"}, []string{"evaluation.log"})
			},
			filepath.Join("evaluation.log"): nil,
			filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
				expectedContent := fmt.Sprintf("%s\n%s", strings.Join(report.EvaluationHeader(), ","), claudeEvaluationCSVFileContent)
				assert.Equal(t, expectedContent, data)
			},
			filepath.Join("result-directory", "meta.csv"): func(t *testing.T, filePath, data string) {
				records := strings.Split(data, "\n")
				// Check if there are at least 3 records, excluding the CSV header.
				require.Greater(t, len(records[1:]), 3)
				// Check if the records are different.
				uniqueRecords := map[string]bool{}
				for _, record := range records[1:4] {
					uniqueRecords[record] = true
				}
				assert.Equal(t, len(uniqueRecords), 3)
			},
		},
	})
	validate(t, &testCase{
		Name: "Multiple files",

		Before: func(t *testing.T, logger *log.Logger, workingDirectory string) {
			evaluationFileHeader := strings.Join(report.EvaluationHeader(), ",")
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "claude"), fmt.Sprintf("%s\n%s", evaluationFileHeader, claudeEvaluationCSVFileContent))
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "gemma"), fmt.Sprintf("%s\n%s", evaluationFileHeader, gemmaEvaluationCSVFileContent))
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "openrouter", "gpt4"), fmt.Sprintf("%s\n%s", evaluationFileHeader, gpt4EvaluationCSVFileContent))
		},

		Arguments: func(workingDirectory string) []string {
			return []string{
				"--evaluation-path", filepath.Join(workingDirectory, "docs", "v5", "claude", "evaluation.csv"),
				"--evaluation-path", filepath.Join(workingDirectory, "docs", "v5", "gemma", "evaluation.csv"),
				"--evaluation-path", filepath.Join(workingDirectory, "docs", "v5", "openrouter", "gpt4", "evaluation.csv"),
			}
		},

		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			filepath.Join("docs", "v5", "claude", "evaluation.csv"):             nil,
			filepath.Join("docs", "v5", "claude", "evaluation.log"):             nil,
			filepath.Join("docs", "v5", "gemma", "evaluation.csv"):              nil,
			filepath.Join("docs", "v5", "gemma", "evaluation.log"):              nil,
			filepath.Join("docs", "v5", "openrouter", "gpt4", "evaluation.csv"): nil,
			filepath.Join("docs", "v5", "openrouter", "gpt4", "evaluation.log"): nil,
			filepath.Join("result-directory", "categories.svg"):                 nil,
			filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath string, data string) {
				validateMarkdownLinks(t, data, []string{
					"openrouter_anthropic_claude-2.0",
					"openrouter_google_gemma-7b-it",
					"openrouter_openai_gpt-4",
				}, []string{
					filepath.Join("claude", "evaluation.log"),
					filepath.Join("gemma", "evaluation.log"),
					filepath.Join("gpt4", "evaluation.log"),
				})
			},
			filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
				expectedContent := fmt.Sprintf("%s\n%s%s%s", strings.Join(report.EvaluationHeader(), ","), claudeEvaluationCSVFileContent, gemmaEvaluationCSVFileContent, gpt4EvaluationCSVFileContent)
				assert.Equal(t, expectedContent, data)
			},
			filepath.Join("result-directory", "meta.csv"): nil,
		},
	})
	validate(t, &testCase{
		Name: "Multiple files with glob pattern",

		Before: func(t *testing.T, logger *log.Logger, workingDirectory string) {
			evaluationFileHeader := strings.Join(report.EvaluationHeader(), ",")
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "claude"), fmt.Sprintf("%s\n%s", evaluationFileHeader, claudeEvaluationCSVFileContent))
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "gemma"), fmt.Sprintf("%s\n%s", evaluationFileHeader, gemmaEvaluationCSVFileContent))
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "gpt4"), fmt.Sprintf("%s\n%s", evaluationFileHeader, gpt4EvaluationCSVFileContent))
		},

		Arguments: func(workingDirectory string) []string {
			return []string{
				"--evaluation-path", filepath.Join(workingDirectory, "docs", "v5", "*", "evaluation.csv"),
			}
		},
		ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
			filepath.Join("docs", "v5", "claude", "evaluation.csv"): nil,
			filepath.Join("docs", "v5", "claude", "evaluation.log"): nil,
			filepath.Join("docs", "v5", "gemma", "evaluation.csv"):  nil,
			filepath.Join("docs", "v5", "gemma", "evaluation.log"):  nil,
			filepath.Join("docs", "v5", "gpt4", "evaluation.csv"):   nil,
			filepath.Join("docs", "v5", "gpt4", "evaluation.log"):   nil,
			filepath.Join("result-directory", "categories.svg"):     nil,
			filepath.Join("result-directory", "README.md"): func(t *testing.T, filePath string, data string) {
				validateMarkdownLinks(t, data, []string{
					"openrouter_anthropic_claude-2.0",
					"openrouter_google_gemma-7b-it",
					"openrouter_openai_gpt-4",
				}, []string{
					filepath.Join("claude", "evaluation.log"),
					filepath.Join("gemma", "evaluation.log"),
					filepath.Join("gpt4", "evaluation.log"),
				})
			},
			filepath.Join("result-directory", "evaluation.csv"): func(t *testing.T, filePath, data string) {
				expectedContent := fmt.Sprintf("%s\n%s%s%s", strings.Join(report.EvaluationHeader(), ","), claudeEvaluationCSVFileContent, gemmaEvaluationCSVFileContent, gpt4EvaluationCSVFileContent)
				assert.Equal(t, expectedContent, data)
			},
			filepath.Join("result-directory", "meta.csv"): nil,
		},
	})
}

func TestPathsFromGlobPattern(t *testing.T) {
	type testCase struct {
		Name string

		Before func(workingDirectory string)

		EvaluationGlobPattern string

		ExpectedEvaluationFilePaths []string
		ExpectedErrText             string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryDirectory := t.TempDir()

			tc.EvaluationGlobPattern = filepath.Join(temporaryDirectory, tc.EvaluationGlobPattern)

			for i, evaluationFilePath := range tc.ExpectedEvaluationFilePaths {
				tc.ExpectedEvaluationFilePaths[i] = filepath.Join(temporaryDirectory, evaluationFilePath)
			}

			if tc.Before != nil {
				tc.Before(temporaryDirectory)
			}

			actualEvaluationFilePaths, actualErr := pathsFromGlobPattern(tc.EvaluationGlobPattern)
			if len(tc.ExpectedErrText) > 0 {
				assert.ErrorContains(t, actualErr, tc.ExpectedErrText)
			} else {
				require.NoError(t, actualErr)
			}

			assert.ElementsMatch(t, tc.ExpectedEvaluationFilePaths, actualEvaluationFilePaths)
		})
	}

	validate(t, &testCase{
		Name: "File is not an evaluation file",

		Before: func(workingDirectory string) {
			file, err := os.Create(filepath.Join(workingDirectory, "not-an-evaluation.csv"))
			require.NoError(t, err)
			file.Close()
		},

		EvaluationGlobPattern: "not-an-evaluation.csv",

		ExpectedErrText: `the path needs to end with "evaluation.csv"`,
	})
	validate(t, &testCase{
		Name: "Simple",

		Before: func(workingDirectory string) {
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "evaluation.csv"), "")
		},

		EvaluationGlobPattern: "evaluation.csv",

		ExpectedEvaluationFilePaths: []string{
			"evaluation.csv",
		},
	})
	validate(t, &testCase{
		Name: "Glob pattern",

		Before: func(workingDirectory string) {
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "modelA"), "")
			evaluationFileWithContent(t, filepath.Join(workingDirectory, "docs", "v5", "modelB"), "")
		},

		EvaluationGlobPattern: filepath.Join("docs", "v5", "*", "evaluation.csv"),

		ExpectedEvaluationFilePaths: []string{
			filepath.Join("docs", "v5", "modelA", "evaluation.csv"),
			filepath.Join("docs", "v5", "modelB", "evaluation.csv"),
		},
	})
}

func evaluationFileWithContent(t *testing.T, workingDirectory string, content string) {
	require.NoError(t, os.MkdirAll(workingDirectory, 0700))
	require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.csv"), []byte(content), 0700))
	require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.log"), []byte(`log`), 0700))
}

func TestCollectAllEvaluationLogFiles(t *testing.T) {
	type testCase struct {
		Name string

		Before func(workingDirectory string)

		EvaluationCSVFilePaths []string

		ExpectedEvaluationLogFilePaths []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryDirectory := t.TempDir()

			if tc.Before != nil {
				tc.Before(temporaryDirectory)
			}

			for i, evaluationFilePath := range tc.EvaluationCSVFilePaths {
				tc.EvaluationCSVFilePaths[i] = filepath.Join(temporaryDirectory, evaluationFilePath)
			}

			actualEvaluationLogFilePaths := collectAllEvaluationLogFiles(tc.EvaluationCSVFilePaths)

			assert.Equal(t, tc.ExpectedEvaluationLogFilePaths, actualEvaluationLogFilePaths)
		})
	}

	validate(t, &testCase{
		Name: "No log files",

		Before: func(workingDirectory string) {
			require.NoError(t, osutil.MkdirAll(filepath.Join(workingDirectory, "someModel")))

			file, err := os.Create(filepath.Join(workingDirectory, "someModel", "evaluation.csv"))
			require.NoError(t, err)
			file.Close()
		},

		EvaluationCSVFilePaths: []string{
			filepath.Join("someModel", "evaluation.csv"),
		},

		ExpectedEvaluationLogFilePaths: nil,
	})
	validate(t, &testCase{
		Name: "Single log file",

		Before: func(workingDirectory string) {
			createEvaluationDirectoryWithLogFiles(t, filepath.Join(workingDirectory, "someModel"))
		},

		EvaluationCSVFilePaths: []string{
			filepath.Join("someModel", "evaluation.csv"),
		},

		ExpectedEvaluationLogFilePaths: []string{
			filepath.Join("someModel", "evaluation.log"),
		},
	})
	validate(t, &testCase{
		Name: "Multiple log files",

		Before: func(workingDirectory string) {
			createEvaluationDirectoryWithLogFiles(t, filepath.Join(workingDirectory, "someModelA"))
			createEvaluationDirectoryWithLogFiles(t, filepath.Join(workingDirectory, "someModelB"))
		},

		EvaluationCSVFilePaths: []string{
			filepath.Join("someModelA", "evaluation.csv"),
			filepath.Join("someModelB", "evaluation.csv"),
		},

		ExpectedEvaluationLogFilePaths: []string{
			filepath.Join("someModelA", "evaluation.log"),
			filepath.Join("someModelB", "evaluation.log"),
		},
	})
}

func createEvaluationDirectoryWithLogFiles(t *testing.T, workingDirectory string) {
	require.NoError(t, osutil.MkdirAll(workingDirectory))

	file, err := os.Create(filepath.Join(workingDirectory, "evaluation.csv"))
	require.NoError(t, err)
	file.Close()

	file, err = os.Create(filepath.Join(workingDirectory, "evaluation.log"))
	require.NoError(t, err)
	file.Close()
}
