package task

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	tasktesting "github.com/symflower/eval-dev-quality/evaluate/task/testing"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/language/golang"
	"github.com/symflower/eval-dev-quality/language/java"
	"github.com/symflower/eval-dev-quality/language/ruby"
	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
	"github.com/symflower/eval-dev-quality/log"
	modeltesting "github.com/symflower/eval-dev-quality/model/testing"
	"github.com/symflower/eval-dev-quality/task"
	evaltask "github.com/symflower/eval-dev-quality/task"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"
)

func TestTaskWriteTestsRun(t *testing.T) {
	validate := func(t *testing.T, tc *tasktesting.TestCaseTask) {
		t.Run(tc.Name, func(t *testing.T) {
			task, err := TaskForIdentifier(IdentifierWriteTests)
			require.NoError(t, err)
			tc.Task = task

			tc.Validate(t,
				func(logger *log.Logger, testDataPath string, repositoryPathRelative string) (repository evaltask.Repository, cleanup func(), err error) {
					return TemporaryRepository(logger, testDataPath, repositoryPathRelative)
				},
			)
		})
	}

	t.Run("Clear repository on each task file", func(t *testing.T) {
		temporaryDirectoryPath := t.TempDir()

		repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "plain")
		require.NoError(t, os.MkdirAll(repositoryPath, 0700))
		require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "go.mod"), []byte("module plain\n\ngo 1.21.5"), 0600))
		require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "taskA.go"), []byte("package plain\n\nfunc TaskA(){}"), 0600))
		require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "taskB.go"), []byte("package plain\n\nfunc TaskB(){}"), 0600))

		modelMock := modeltesting.NewMockCapabilityWriteTestsNamed(t, "mocked-model")

		// Generate invalid code for the first taskcontext.
		modelMock.RegisterGenerateSuccess(t, "taskA_test.go", "does not compile", metricstesting.AssessmentsWithProcessingTime).Once()
		// Generate valid code for the second taskcontext.
		modelMock.RegisterGenerateSuccess(t, "taskB_test.go", "package plain\n\nimport \"testing\"\n\nfunc TestTaskB(t *testing.T){}", metricstesting.AssessmentsWithProcessingTime).Once()

		validate(t, &tasktesting.TestCaseTask{
			Name: "Plain",

			Model:          modelMock,
			Language:       &golang.Language{},
			TestDataPath:   temporaryDirectoryPath,
			RepositoryPath: filepath.Join("golang", "plain"),

			ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
				IdentifierWriteTests: metrics.Assessments{
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
					metrics.AssessmentKeyResponseNoError:               2,
				},
				IdentifierWriteTestsSymflowerFix: metrics.Assessments{
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
					metrics.AssessmentKeyResponseNoError:               2,
				},
			},
			ExpectedProblemContains: []string{
				"expected 'package', found does",
				"exit status 1",
			},
			ValidateLog: func(t *testing.T, data string) {
				assert.Contains(t, data, "Evaluating model \"mocked-model\"")
				assert.Contains(t, data, "PASS: TestTaskB")
			},
		})
	})

	t.Run("Symflower Fix", func(t *testing.T) {
		t.Run("Go", func(t *testing.T) {
			validateGo := func(t *testing.T, testName string, language language.Language, testFileContent string, expectedAssessments map[evaltask.Identifier]metrics.Assessments, expectedProblems []string, assertTestsPass bool) {
				temporaryDirectoryPath := t.TempDir()
				repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "plain")
				require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "plain"), repositoryPath))

				modelMock := modeltesting.NewMockCapabilityWriteTestsNamed(t, "mocked-model")
				modelMock.RegisterGenerateSuccess(t, "plain_test.go", testFileContent, metricstesting.AssessmentsWithProcessingTime).Once()

				validate(t, &tasktesting.TestCaseTask{
					Name: testName,

					Model:          modelMock,
					Language:       language,
					TestDataPath:   temporaryDirectoryPath,
					RepositoryPath: filepath.Join("golang", "plain"),

					ExpectedRepositoryAssessment: expectedAssessments,
					ExpectedProblemContains:      expectedProblems,
					ValidateLog: func(t *testing.T, data string) {
						assert.Contains(t, data, "Evaluating model \"mocked-model\"")
						if assertTestsPass {
							assert.Contains(t, data, "PASS: TestPlain")
						}
					},
				})
			}
			{
				expectedAssessments := map[evaltask.Identifier]metrics.Assessments{
					IdentifierWriteTests: metrics.Assessments{
						metrics.AssessmentKeyFilesExecuted:                 1,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
						metrics.AssessmentKeyCoverage:                      10,
					},
					IdentifierWriteTestsSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyFilesExecuted:                 1,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
						metrics.AssessmentKeyCoverage:                      10,
					},
				}
				validateGo(t, "Model generated correct test", &golang.Language{}, bytesutil.StringTrimIndentations(`
					package plain

					import "testing"

					func TestPlain(t *testing.T) {
						   plain()
					}
				`), expectedAssessments, nil, true)
			}
			{
				expectedAssessments := map[evaltask.Identifier]metrics.Assessments{
					IdentifierWriteTests: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
					IdentifierWriteTestsSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyFilesExecuted:                 1,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
						metrics.AssessmentKeyCoverage:                      10,
					},
				}
				expectedProblems := []string{
					"imported and not used",
				}
				validateGo(t, "Model generated test with unused import", &golang.Language{}, bytesutil.StringTrimIndentations(`
					package plain

					import (
						"testing"
						"strings"
					)

					func TestPlain(t *testing.T) {
					   	plain()
					}
				`), expectedAssessments, expectedProblems, true)
			}
			{
				expectedAssessments := map[evaltask.Identifier]metrics.Assessments{
					IdentifierWriteTests: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
					IdentifierWriteTestsSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
				}
				expectedProblems := []string{
					"expected declaration, found this",
					"unable to format source code",
				}
				validateGo(t, "Model generated test that is unfixable", &golang.Language{}, bytesutil.StringTrimIndentations(`
					package plain

					this is not valid go code
				`), expectedAssessments, expectedProblems, false)
			}
			{
				expectedAssessments := map[task.Identifier]metrics.Assessments{
					IdentifierWriteTests: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
					IdentifierWriteTestsSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
						metrics.AssessmentKeyResponseNoError:               1,
					},
				}
				expectedProblems := []string{
					"context deadline exceeded",
				}

				languageMock := languagetesting.NewMockLanguageNamed(t, "golang")
				languageMock.On("Files", mock.Anything, mock.Anything).Return([]string{filepath.Join("golang", "plain")}, nil).Once()
				languageMock.On("ExecuteTests", mock.Anything, mock.Anything).Return(nil, nil, context.DeadlineExceeded).Once()

				validateGo(t, "Execution timeout", languageMock, "", expectedAssessments, expectedProblems, false)
			}
		})
	})

	{
		if osutil.IsWindows() {
			t.Skip("Ruby is not tested in the Windows CI")
		}

		temporaryDirectoryPath := t.TempDir()
		repositoryPath := filepath.Join(temporaryDirectoryPath, "ruby", "plain")
		require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "ruby", "plain"), repositoryPath))

		testFileContent := bytesutil.StringTrimIndentations(`
			require_relative "../lib/plain"

			class TestPlain < Minitest::Test
				def test_plain
					plain()
				end
			end
		`)
		modelMock := modeltesting.NewMockCapabilityWriteTestsNamed(t, "mocked-model")
		modelMock.RegisterGenerateSuccess(t, filepath.Join("test", "plain_test.rb"), testFileContent, metricstesting.AssessmentsWithProcessingTime).Maybe()

		validate(t, &tasktesting.TestCaseTask{
			Name: "Ruby",

			Model:          modelMock,
			Language:       &ruby.Language{},
			TestDataPath:   temporaryDirectoryPath,
			RepositoryPath: filepath.Join("ruby", "plain"),

			ExpectedRepositoryAssessment: map[task.Identifier]metrics.Assessments{
				IdentifierWriteTests: metrics.Assessments{
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyCoverage:                      10,
					metrics.AssessmentKeyResponseNoError:               1,
				},
				IdentifierWriteTestsSymflowerFix: metrics.Assessments{
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyCoverage:                      10,
					metrics.AssessmentKeyResponseNoError:               1,
				},
			},
			ExpectedProblemContains: nil,
			ValidateLog: func(t *testing.T, data string) {
				assert.Contains(t, data, "Evaluating model \"mocked-model\"")
			},
		})
	}
}

func TestValidateWriteTestsRepository(t *testing.T) {
	validate := func(t *testing.T, tc *tasktesting.TestCaseValidateRepository) {
		tc.Validate(t, validateWriteTestsRepository)
	}

	t.Run("Go", func(t *testing.T) {
		t.Run("Plain", func(t *testing.T) {
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Well-formed",

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("golang", "plain"),
				Language:       &golang.Language{},
			})
		})
		t.Run("Light", func(t *testing.T) {
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Repository with test files",

				Before: func(repositoryPath string) {
					fileATest, err := os.Create(filepath.Join(repositoryPath, "fileA_test.go"))
					require.NoError(t, err)
					fileATest.Close()
				},

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("golang", "light"),
				Language:       &golang.Language{},
				ExpectedError: func(t *testing.T, err error) {
					assert.ErrorContains(t, err, "must contain only Go source files, but found [fileA_test.go]")
				},
			})
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Well-formed",

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("golang", "light"),
				Language:       &golang.Language{},
			})
		})
	})
	t.Run("Java", func(t *testing.T) {
		t.Run("Plain", func(t *testing.T) {
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Well-formed",

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("java", "plain"),
				Language:       &java.Language{},
			})
		})
		t.Run("Light", func(t *testing.T) {
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Repository with test files",

				Before: func(repositoryPath string) {
					somePackage := filepath.Join(repositoryPath, "src", "test", "java", "com", "eval")
					require.NoError(t, os.MkdirAll(somePackage, 0700))

					fileATest, err := os.Create(filepath.Join(somePackage, "FileATest.java"))
					require.NoError(t, err)
					fileATest.Close()
				},

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("java", "light"),
				Language:       &java.Language{},

				ExpectedError: func(t *testing.T, err error) {
					assert.ErrorContains(t, err, fmt.Sprintf("must contain only Java source files, but found [%s]", filepath.Join("src", "test", "java", "com", "eval", "FileATest.java")))
				},
			})
			validate(t, &tasktesting.TestCaseValidateRepository{
				Name: "Well-formed",

				TestdataPath:   filepath.Join("..", "..", "testdata"),
				RepositoryPath: filepath.Join("java", "light"),
				Language:       &java.Language{},
			})
		})
	})
}
