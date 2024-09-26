package evaluate

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	evaluatetask "github.com/symflower/eval-dev-quality/evaluate/task"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/language/golang"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	evalmodel "github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/model/llm"
	modeltesting "github.com/symflower/eval-dev-quality/model/testing"
	"github.com/symflower/eval-dev-quality/provider"
	providertesting "github.com/symflower/eval-dev-quality/provider/testing"
	"github.com/symflower/eval-dev-quality/task"
)

var (
	// ErrEmptyResponseFromModel indicates the model returned an empty response.
	ErrEmptyResponseFromModel = errors.New("empty response from model")
)

// file represents a file with path and content.
type file struct {
	Path    string
	Content string
}

// testFiles holds common test files.
var testFiles = map[string]file{
	"plain": file{
		Path: "plain_test.go",
		Content: bytesutil.StringTrimIndentations(`
			package plain

			import "testing"

			func TestFunction(t *testing.T){}
		`),
	},
	"plain-with-assert": file{
		Path: "plain_test.go",
		Content: bytesutil.StringTrimIndentations(`
			package plain

			import (
				"testing"

				"github.com/stretchr/testify/assert"
			)

			func TestFunction(t *testing.T){
				assert.True(t, true)
			}
		`),
	},
}

func TestEvaluate(t *testing.T) {
	type testCase struct {
		Name string

		Before func(t *testing.T, logger *log.Logger, resultPath string)
		After  func(t *testing.T, logger *log.Logger, resultPath string)

		Context *Context

		ExpectedAssessments    metricstesting.AssessmentTuples
		ExpectedTotalScore     uint64
		ExpectedOutputValidate func(t *testing.T, output string, resultPath string)
		ExpectedResultFiles    map[string]func(t *testing.T, filePath string, data string)
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

			resultPath := temporaryPath
			logger = logger.With(log.AttributeKeyResultPath, resultPath)

			tc.Context.Log = logger
			if tc.Context.QueryAttempts == 0 {
				tc.Context.QueryAttempts = 1
			}
			tc.Context.ResultPath = resultPath
			if tc.Context.TestdataPath == "" {
				tc.Context.TestdataPath = filepath.Join("..", "testdata")
			}
			if tc.Context.Runs == 0 {
				tc.Context.Runs = 1
			}

			if tc.Before != nil {
				tc.Before(t, logger, temporaryPath)
			}
			if tc.After != nil {
				defer tc.After(t, logger, temporaryPath)
			}

			assessmentStore, actualTotalScore := Evaluate(tc.Context)

			var actualAssessments metricstesting.AssessmentTuples
			require.NoError(t, assessmentStore.Walk(func(m evalmodel.Model, l language.Language, r string, ti task.Identifier, a metrics.Assessments) error {
				// Normalize assessments.
				if v, ok := a[metrics.AssessmentKeyProcessingTime]; ok {
					if assert.Greater(t, v, uint64(0)) {
						delete(a, metrics.AssessmentKeyProcessingTime)
					}
				}

				actualAssessments = append(actualAssessments, &metricstesting.AssessmentTuple{
					Model:          m,
					Language:       l,
					RepositoryPath: r,
					Task:           ti,
					Assessment:     a,
				})

				return nil
			}))

			assert.ElementsMatch(t, tc.ExpectedAssessments, actualAssessments)
			assert.Equal(t, tc.ExpectedTotalScore, actualTotalScore)

			if tc.ExpectedOutputValidate != nil {
				tc.ExpectedOutputValidate(t, logOutput.String(), temporaryPath)
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

	{
		languageGolang := &golang.Language{}
		mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, "empty-response-model")
		repositoryPath := filepath.Join("golang", "plain")

		validate(t, &testCase{
			Name: "Empty model responses are errors",

			Before: func(t *testing.T, logger *log.Logger, resultPath string) {
				// Set up mocks, when test is running.
				mockedModel.MockCapabilityWriteTests.On("WriteTests", mock.Anything).Return(nil, ErrEmptyResponseFromModel)
			},

			Context: &Context{
				Languages: []language.Language{
					&golang.Language{},
				},

				Models: []evalmodel.Model{
					mockedModel,
				},
			},

			ExpectedAssessments: []*metricstesting.AssessmentTuple{
				&metricstesting.AssessmentTuple{
					Model:          mockedModel,
					Language:       languageGolang,
					RepositoryPath: repositoryPath,
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          mockedModel,
					Language:       languageGolang,
					RepositoryPath: repositoryPath,
					Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
					},
				},
			},
			ExpectedTotalScore: 2,
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				"evaluation.log": nil,
				filepath.Join(string(evaluatetask.IdentifierWriteTests), mockedModel.ID(), "golang", "golang", "plain", "evaluation.log"): nil,
				"evaluation.csv": nil,
			},
		})
	}

	t.Run("Failing model queries", func(t *testing.T) {
		{
			languageGolang := &golang.Language{}
			mockedModelID := "testing-provider/empty-response-model"
			mockedQuery := providertesting.NewMockQuery(t)
			mockedModel := llm.NewModel(mockedQuery, mockedModelID)
			repositoryPath := filepath.Join("golang", "plain")

			validate(t, &testCase{
				Name: "Single try fails",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					mockedQuery.On("Query", mock.Anything, mockedModelID, mock.Anything).Return("", ErrEmptyResponseFromModel)
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedQuery.AssertNumberOfCalls(t, "Query", 1)
				},

				Context: &Context{
					Languages: []language.Language{
						languageGolang,
					},

					Models: []evalmodel.Model{
						mockedModel,
					},
					QueryAttempts: 1,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: metrics.Assessments{
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: metrics.Assessments{
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						},
					},
				},
				ExpectedTotalScore: 2,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
						assert.Contains(t, data, ErrEmptyResponseFromModel.Error())
					},
					"evaluation.csv": nil,
				},
			})
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "testing-provider/empty-response-model"
			mockedQuery := providertesting.NewMockQuery(t)
			mockedModel := llm.NewModel(mockedQuery, mockedModelID)
			repositoryPath := filepath.Join("golang", "plain")

			validate(t, &testCase{
				Name: "Success after retry",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					mockedQuery.On("Query", mock.Anything, mockedModelID, mock.Anything).Return("", ErrEmptyResponseFromModel).Once()
					mockedQuery.On("Query", mock.Anything, mockedModelID, mock.Anything).Return("model-response", nil).Once().After(10 * time.Millisecond) // Simulate a model response delay because our internal safety measures trigger when a query is done in 0 milliseconds.
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedQuery.AssertNumberOfCalls(t, "Query", 2)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},
					QueryAttempts: 3,

					RepositoryPaths: []string{
						repositoryPath,
					},
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable:      1,
							metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 14,
							metrics.AssessmentKeyResponseCharacterCount:             14,
							metrics.AssessmentKeyResponseNoError:                    1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable:      1,
							metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 14,
							metrics.AssessmentKeyResponseCharacterCount:             14,
							metrics.AssessmentKeyResponseNoError:                    1,
						},
					},
				},
				ExpectedTotalScore: 2,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
						assert.Contains(t, data, "Attempt 1/3: "+ErrEmptyResponseFromModel.Error())
					},
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "response-1.log"): nil,
					"evaluation.csv": nil,
				},
			})
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "testing-provider/empty-response-model"
			mockedQuery := providertesting.NewMockQuery(t)
			mockedModel := llm.NewModel(mockedQuery, mockedModelID)
			repositoryPath := filepath.Join("golang", "plain")

			validate(t, &testCase{
				Name: "Immediate success",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					mockedQuery.On("Query", mock.Anything, mockedModelID, mock.Anything).Return("model-response", nil).After(10 * time.Millisecond) // Simulate a model response delay because our internal safety measures trigger when a query is done in 0 milliseconds.
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedQuery.AssertNumberOfCalls(t, "Query", 1)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},
					QueryAttempts: 3,

					RepositoryPaths: []string{
						repositoryPath,
					},
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable:      1,
							metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 14,
							metrics.AssessmentKeyResponseCharacterCount:             14,
							metrics.AssessmentKeyResponseNoError:                    1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable:      1,
							metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 14,
							metrics.AssessmentKeyResponseCharacterCount:             14,
							metrics.AssessmentKeyResponseNoError:                    1,
						},
					},
				},
				ExpectedTotalScore: 2,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): func(t *testing.T, filePath, data string) {
						assert.Contains(t, data, "DONE 0 tests, 1 error")
					},
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "response-1.log"): nil,
					"evaluation.csv": nil,
				},
			})
		}
	})

	t.Run("Failing basic language checks should exclude model", func(t *testing.T) {
		repositoryPlainPath := filepath.Join("golang", "plain")
		repositoryNextPath := filepath.Join("golang", "next")

		temporaryTestdataPath := t.TempDir()
		assert.NoError(t, osutil.CopyTree(filepath.Join("..", "testdata", repositoryPlainPath), filepath.Join(temporaryTestdataPath, repositoryPlainPath)))
		assert.NoError(t, osutil.CopyTree(filepath.Join("..", "testdata", repositoryPlainPath), filepath.Join(temporaryTestdataPath, repositoryNextPath)))
		repositoryNextConfigPath := filepath.Join(temporaryTestdataPath, repositoryNextPath, "go.mod")
		d, err := os.ReadFile(repositoryNextConfigPath)
		require.NoError(t, err)
		d = bytes.ReplaceAll(d, []byte("plain"), []byte("next"))
		require.NoError(t, os.WriteFile(repositoryNextConfigPath, d, 0))

		generateTestsForFilePlainError := errors.New("generateTestsForFile error")

		generateSuccess := func(mockedModel *modeltesting.MockModelCapabilityWriteTests) {
			mockedModel.RegisterGenerateSuccess(t, testFiles["plain"].Path, testFiles["plain"].Content, metricstesting.AssessmentsWithProcessingTime).Once()
		}
		generateError := func(mockedModel *modeltesting.MockModelCapabilityWriteTests) {
			mockedModel.RegisterGenerateError(generateTestsForFilePlainError).Once()
		}

		{
			languageGolang := &golang.Language{}
			mockedModelID := "mocked-generation-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

			validate(t, &testCase{
				Name: "Problems of previous runs shouldn't cancel successive runs",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					{
						// Succeed on both "plain" runs.
						generateSuccess(mockedModel)
						generateSuccess(mockedModel)

						// Error on the first run for the "next" repository.
						generateError(mockedModel)
						// Succeed on the second run for the "next" repository.
						generateSuccess(mockedModel)
					}
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedModel.MockCapabilityWriteTests.AssertNumberOfCalls(t, "WriteTests", 4)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},

					RepositoryPaths: []string{
						repositoryPlainPath,
						repositoryNextPath,
					},
					TestdataPath: temporaryTestdataPath,

					Runs: 2,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryNextPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryNextPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 2,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               2,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 2,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               2,
						},
					},
				},
				ExpectedTotalScore: 0,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "next", "evaluation.log"):  nil,
					"evaluation.csv": nil,
				},
			})
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "mocked-generation-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

			validate(t, &testCase{
				Name: "Solving basic checks once is enough",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					{
						// Succeed on only one "plain" run.
						generateError(mockedModel)
						generateSuccess(mockedModel)

						// Succeed on both "next" runs.
						generateSuccess(mockedModel)
						generateSuccess(mockedModel)
					}
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedModel.MockCapabilityWriteTests.AssertNumberOfCalls(t, "WriteTests", 4)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},

					RepositoryPaths: []string{
						repositoryPlainPath,
						repositoryNextPath,
					},
					TestdataPath: temporaryTestdataPath,

					Runs: 2,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryNextPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 2,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               2,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryNextPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 2,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               2,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               1,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 1,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
							metrics.AssessmentKeyResponseNoError:               1,
						},
					},
				},
				ExpectedTotalScore: 0,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "next", "evaluation.log"):  nil,
					"evaluation.csv": nil,
				},
			})
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "mocked-generation-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

			validate(t, &testCase{
				Name: "Never solving basic checks leads to exclusion",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					// Set up mocks, when test is running.
					{
						// Error on every "plain" run.
						generateError(mockedModel)
						generateError(mockedModel)
					}
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					mockedModel.MockCapabilityWriteTests.AssertNumberOfCalls(t, "WriteTests", 2)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},

					RepositoryPaths: []string{
						repositoryPlainPath,
						repositoryNextPath,
					},
					TestdataPath: temporaryTestdataPath,

					Runs: 2,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPlainPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						},
					},
				},
				ExpectedTotalScore: 0,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					"evaluation.csv": nil,
				},
			})
		}
	})
	t.Run("Runs", func(t *testing.T) {
		generateSuccess := func(mockedModel *modeltesting.MockModelCapabilityWriteTests) {
			mockedModel.RegisterGenerateSuccess(t, testFiles["plain"].Path, testFiles["plain"].Content, metricstesting.AssessmentsWithProcessingTime)
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "mocked-generation-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

			repositoryPath := filepath.Join("golang", "plain")
			validate(t, &testCase{
				Name: "Interleaved",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					generateSuccess(mockedModel)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},

					RepositoryPaths: []string{
						repositoryPath,
					},

					Runs:           3,
					RunsSequential: false,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
				},
				ExpectedTotalScore: 6,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					"evaluation.csv": nil,
				},
				ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
					assert.Contains(t, output, "Run 1/3")
					assert.Contains(t, output, "Run 2/3")
					assert.Contains(t, output, "Run 3/3")
					assert.NotRegexp(t, `Run \d+/\d+ for model`, output)

					assert.Equal(t, 1, strings.Count(output, "Creating temporary repository"), "create only one temporary repository")
				},
			})
		}
		{
			languageGolang := &golang.Language{}
			mockedModelID := "mocked-generation-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

			repositoryPath := filepath.Join("golang", "plain")
			validate(t, &testCase{
				Name: "Sequential",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					generateSuccess(mockedModel)
				},

				Context: &Context{
					Languages: []language.Language{
						&golang.Language{},
					},

					Models: []evalmodel.Model{
						mockedModel,
					},

					RepositoryPaths: []string{
						repositoryPath,
					},

					Runs:           3,
					RunsSequential: true,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
				},
				ExpectedTotalScore: 6,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					"evaluation.csv": nil,
				},
				ExpectedOutputValidate: func(t *testing.T, output string, resultPath string) {
					assert.Contains(t, output, "Run 1/3 for model")
					assert.Contains(t, output, "Run 2/3 for model")
					assert.Contains(t, output, "Run 3/3 for model")
					assert.NotRegexp(t, `Run \d+/\d+$`, output)

					assert.Equal(t, 1, strings.Count(output, "Creating temporary repository"), "create only one temporary repository")
				},
			})
		}
	})

	t.Run("Preloading", func(t *testing.T) {
		generateSuccess := func(mockedModel *modeltesting.MockModelCapabilityWriteTests) {
			mockedModel.RegisterGenerateSuccess(t, testFiles["plain"].Path, testFiles["plain"].Content, metricstesting.AssessmentsWithProcessingTime)
		}

		{
			// Setup provider and model mocking.
			languageGolang := &golang.Language{}
			mockedModelID := "testing-provider/testing-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)
			mockedProviderID := "testing-provider"
			mockedProvider := providertesting.NewMockProviderNamedWithModels(t, mockedProviderID, []model.Model{mockedModel})
			mockedLoader := providertesting.NewMockLoader(t)
			embeddedProvider := &struct {
				provider.Provider
				provider.Loader
			}{
				Provider: mockedProvider,
				Loader:   mockedLoader,
			}
			repositoryPath := filepath.Join("golang", "plain")

			validate(t, &testCase{
				Name: "Once for combined runs",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					generateSuccess(mockedModel)
					mockedLoader.On("Load", mockedModelID).Return(nil)
					mockedLoader.On("Unload", mockedModelID).Return(nil)
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					delete(provider.Providers, mockedProviderID)

					mockedLoader.AssertNumberOfCalls(t, "Load", 1)
					mockedLoader.AssertNumberOfCalls(t, "Unload", 1)
				},

				Context: &Context{
					Languages: []language.Language{
						languageGolang,
					},

					Models: []evalmodel.Model{
						mockedModel,
					},
					ProviderForModel: map[evalmodel.Model]provider.Provider{
						mockedModel: embeddedProvider,
					},

					RepositoryPaths: []string{
						repositoryPath,
					},

					Runs:           3,
					RunsSequential: true,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
				},
				ExpectedTotalScore: 6,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					"evaluation.csv": nil,
				},
			})
		}
		{
			// Setup provider and model mocking.
			languageGolang := &golang.Language{}
			mockedModelID := "testing-provider/testing-model"
			mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)
			mockedProviderID := "testing-provider"
			mockedProvider := providertesting.NewMockProviderNamedWithModels(t, mockedProviderID, []model.Model{mockedModel})
			mockedLoader := providertesting.NewMockLoader(t)
			embeddedProvider := &struct {
				provider.Provider
				provider.Loader
			}{
				Provider: mockedProvider,
				Loader:   mockedLoader,
			}
			repositoryPath := filepath.Join("golang", "plain")
			validate(t, &testCase{
				Name: "Multiple times for interleaved runs",

				Before: func(t *testing.T, logger *log.Logger, resultPath string) {
					generateSuccess(mockedModel)
					mockedLoader.On("Load", mockedModelID).Return(nil)
					mockedLoader.On("Unload", mockedModelID).Return(nil)
				},
				After: func(t *testing.T, logger *log.Logger, resultPath string) {
					delete(provider.Providers, "testing-provider")

					mockedLoader.AssertNumberOfCalls(t, "Load", 3)
					mockedLoader.AssertNumberOfCalls(t, "Unload", 3)
				},

				Context: &Context{
					Languages: []language.Language{
						languageGolang,
					},

					Models: []evalmodel.Model{
						mockedModel,
					},
					ProviderForModel: map[evalmodel.Model]provider.Provider{
						mockedModel: embeddedProvider,
					},

					RepositoryPaths: []string{
						repositoryPath,
					},

					Runs: 3,
				},

				ExpectedAssessments: []*metricstesting.AssessmentTuple{
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTests,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
					&metricstesting.AssessmentTuple{
						Model:          mockedModel,
						Language:       languageGolang,
						RepositoryPath: repositoryPath,
						Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
						Assessment: map[metrics.AssessmentKey]uint64{
							metrics.AssessmentKeyCoverage:                      0,
							metrics.AssessmentKeyFilesExecuted:                 3,
							metrics.AssessmentKeyFilesExecutedMaximumReachable: 3,
							metrics.AssessmentKeyResponseNoError:               3,
						},
					},
				},
				ExpectedTotalScore: 6,
				ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
					"evaluation.log": nil,
					filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
					"evaluation.csv": nil,
				},
			})
		}
	})
	{
		// Setup provider and model mocking.
		languageGolang := &golang.Language{}
		mockedModelID := "testing-provider/testing-model"
		mockedModel := modeltesting.NewMockCapabilityWriteTestsNamed(t, mockedModelID)

		repositoryPath := filepath.Join("golang", "plain")

		validate(t, &testCase{
			Name: "Download Go dependencies",

			Before: func(t *testing.T, logger *log.Logger, resultPath string) {
				mockedModel.RegisterGenerateSuccess(t, testFiles["plain-with-assert"].Path, testFiles["plain-with-assert"].Content, metricstesting.AssessmentsWithProcessingTime)
			},

			Context: &Context{
				Languages: []language.Language{
					languageGolang,
				},

				Models: []evalmodel.Model{
					mockedModel,
				},

				RepositoryPaths: []string{
					repositoryPath,
				},

				Runs: 1,
			},

			ExpectedAssessments: []*metricstesting.AssessmentTuple{
				&metricstesting.AssessmentTuple{
					Model:          mockedModel,
					Language:       languageGolang,
					RepositoryPath: repositoryPath,
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: map[metrics.AssessmentKey]uint64{
						metrics.AssessmentKeyCoverage:                      0,
						metrics.AssessmentKeyFilesExecuted:                 1,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          mockedModel,
					Language:       languageGolang,
					RepositoryPath: repositoryPath,
					Task:           evaluatetask.IdentifierWriteTestsSymflowerFix,
					Assessment: map[metrics.AssessmentKey]uint64{
						metrics.AssessmentKeyCoverage:                      0,
						metrics.AssessmentKeyFilesExecuted:                 1,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
				},
			},
			ExpectedTotalScore: 2,
			ExpectedResultFiles: map[string]func(t *testing.T, filePath string, data string){
				"evaluation.log": nil,
				filepath.Join(string(evaluatetask.IdentifierWriteTests), log.CleanModelNameForFileSystem(mockedModelID), "golang", "golang", "plain", "evaluation.log"): nil,
				"evaluation.csv": nil,
			},
		})
	}
}
