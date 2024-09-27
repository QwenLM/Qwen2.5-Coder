package task

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	tasktesting "github.com/symflower/eval-dev-quality/evaluate/task/testing"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/language/golang"
	"github.com/symflower/eval-dev-quality/language/java"
	"github.com/symflower/eval-dev-quality/language/ruby"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	modeltesting "github.com/symflower/eval-dev-quality/model/testing"
	evaltask "github.com/symflower/eval-dev-quality/task"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"
)

func TestTaskTranspileRun(t *testing.T) {
	validate := func(t *testing.T, tc *tasktesting.TestCaseTask) {
		t.Run(tc.Name, func(t *testing.T) {
			task, err := TaskForIdentifier(IdentifierTranspile)
			require.NoError(t, err)
			tc.Task = task

			tc.Validate(t,
				func(logger *log.Logger, testDataPath string, repositoryPathRelative string) (repository evaltask.Repository, cleanup func(), err error) {
					return TemporaryRepository(logger, testDataPath, repositoryPathRelative)
				},
			)
		})
	}

	validateContext := func(t *testing.T, c model.Context) {
		arguments, ok := c.Arguments.(*TaskArgumentsTranspile)
		require.True(t, ok, fmt.Sprintf("%T != TaskArgumentsTranspile", arguments))
		assert.True(t, strings.HasPrefix(arguments.OriginFilePath, "implementation"+string(os.PathSeparator)), fmt.Sprintf("%q must be a relative path", arguments.OriginFilePath))
	}

	t.Run("Transpile into Go", func(t *testing.T) {
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "transpile", "cascadingIfElse")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "transpile", "cascadingIfElse"), repositoryPath))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := "cascadingIfElse.go"
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				package cascadingIfElse

			 	func cascadingIfElse(i int) int {
			 		if i == 1 {
			 			return 2
			 		} else if i == 3 {
			 			return 4
			 		} else {
			 			return 5
			 		}
			 	}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Single test case",

				Model:          modelMock,
				Language:       &golang.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("golang", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  80,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  80,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#00")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#01")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#02")
				},
			})
		}
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "transpile")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "transpile", "cascadingIfElse"), filepath.Join(repositoryPath, "cascadingIfElse")))
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "transpile", "isSorted"), filepath.Join(repositoryPath, "isSorted")))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := "cascadingIfElse.go"
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				package cascadingIfElse

				func cascadingIfElse(i int) int {
					if i == 1 {
						return 2
					} else if i == 3 {
						return 4
					} else {
						return 5
					}
				}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			transpiledSourceFilePath = "isSorted.go"
			transpiledSourceFileContent = bytesutil.StringTrimIndentations(`
				package isSorted

				func isSorted(a []int) bool {
					i := 0
					for i < len(a)-1 && a[i] <= a[i+1] {
						i++
					}

					return i == len(a)-1
				}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Multiple test cases",

				Model:          modelMock,
				Language:       &golang.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("golang", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  200,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  200,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#00")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#01")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#02")

					assert.Contains(t, data, "PASS: TestSymflowerIsSorted/#00")
					assert.Contains(t, data, "PASS: TestSymflowerIsSorted/#01")
					assert.Contains(t, data, "PASS: TestSymflowerIsSorted/#02")
					assert.Contains(t, data, "PASS: TestSymflowerIsSorted/#03")
					assert.Contains(t, data, "PASS: TestSymflowerIsSorted/#04")
				},
			})
		}
	})
	t.Run("Transpile into Java", func(t *testing.T) {
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "java", "transpile", "cascadingIfElse")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "java", "transpile", "cascadingIfElse"), repositoryPath))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := filepath.Join("src", "main", "java", "com", "eval", "CascadingIfElse.java")
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				package com.eval;

				class CascadingIfElse {
					static int cascadingIfElse(int i) {
						if (i == 1) {
							return 2;
						} else if (i == 3) {
							return 4;
						} else {
							return 5;
						}
					}
				}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Single test case",

				Model:          modelMock,
				Language:       &java.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("java", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  60,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  60,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "BUILD SUCCESS")
				},
			})
		}
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "java", "transpile")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "java", "transpile", "cascadingIfElse"), filepath.Join(repositoryPath, "cascadingIfElse")))
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "java", "transpile", "isSorted"), filepath.Join(repositoryPath, "isSorted")))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := filepath.Join("src", "main", "java", "com", "eval", "CascadingIfElse.java")
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				package com.eval;

				class CascadingIfElse {
					static int cascadingIfElse(int i) {
						if (i == 1) {
							return 2;
						} else if (i == 3) {
							return 4;
						} else {
							return 5;
						}
					}
				}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			transpiledSourceFilePath = filepath.Join("src", "main", "java", "com", "eval", "IsSorted.java")
			transpiledSourceFileContent = bytesutil.StringTrimIndentations(`
				package com.eval;

				class IsSorted {
					static boolean isSorted(int[] a) {
						int i = 0;
						while (i < a.length - 1 && a[i] <= a[i + 1]) {
							i++;
						}

						return i == a.length - 1;
					}
				}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Multiple test cases",

				Model:          modelMock,
				Language:       &java.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("java", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  160,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  160,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "BUILD SUCCESS")
				},
			})
		}
	})
	t.Run("Symflower fix", func(t *testing.T) {
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "transpile", "cascadingIfElse")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "transpile", "cascadingIfElse"), repositoryPath))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := "cascadingIfElse.go"
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				package cascadingIfElse

				import "strings"

			 	func cascadingIfElse(i int) int {
			 		if i == 1 {
			 			return 2
			 		} else if i == 3 {
			 			return 4
			 		} else {
			 			return 5
			 		}
			 	}
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Model generated test with unused import",

				Model:          modelMock,
				Language:       &golang.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("golang", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  0,
						metrics.AssessmentKeyResponseNoError:               2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  80,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
				},
				ExpectedProblemContains: []string{
					"imported and not used",
					"imported and not used",
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#00")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#01")
					assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse/#02")
				},
			})
		}
	})
	t.Run("Transpile into Ruby", func(t *testing.T) {
		if osutil.IsWindows() {
			t.Skip("Ruby is not tested in the Windows CI")
		}

		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "ruby", "transpile", "cascadingIfElse")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "ruby", "transpile", "cascadingIfElse"), repositoryPath))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := filepath.Join("lib", "cascading_if_else.rb")
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				def cascading_if_else(i)
					if i == 1
						return 2
					elsif i == 3
						return 4
					else
						return 5
					end
				end
			`)
			modelMock.RegisterGenerateSuccess(t, func(t *testing.T, c model.Context) {
				arguments, ok := c.Arguments.(*TaskArgumentsTranspile)
				require.True(t, ok, fmt.Sprintf("%T != TaskArgumentsTranspile", arguments))
				assert.True(t, strings.HasPrefix(arguments.OriginFilePath, "implementation/"), fmt.Sprintf("%q must be a relative path", arguments.OriginFilePath))

				// This assertion checks explicitly that stub files are not overwritten, now that we added a third language with Ruby.
				content, err := os.ReadFile(filepath.Join(c.RepositoryPath, c.FilePath))
				require.NoError(t, err)
				assert.Equal(t, bytesutil.StringTrimIndentations(`
					# @param [Integer] i
					# @return [Integer]
					def cascading_if_else(i)
					end
				`), string(content))
			}, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Single test case",

				Model:          modelMock,
				Language:       &ruby.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("ruby", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  60,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  60,
						metrics.AssessmentKeyFilesExecuted:                 2,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
						metrics.AssessmentKeyResponseNoError:               2,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Contains(t, data, "3 runs, 3 assertions, 0 failures, 0 errors, 0 skips")
				},
			})
		}
		{
			temporaryDirectoryPath := t.TempDir()

			repositoryPath := filepath.Join(temporaryDirectoryPath, "ruby", "transpile")
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "ruby", "transpile", "cascadingIfElse"), filepath.Join(repositoryPath, "cascadingIfElse")))
			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "ruby", "transpile", "isSorted"), filepath.Join(repositoryPath, "isSorted")))

			modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

			transpiledSourceFilePath := filepath.Join("lib", "cascading_if_else.rb")
			transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
				def cascading_if_else(i)
					if i == 1
						return 2
					elsif i == 3
						return 4
					else
						return 5
					end
				end
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			transpiledSourceFilePath = filepath.Join("lib", "sort.rb")
			transpiledSourceFileContent = bytesutil.StringTrimIndentations(`
				def is_sorted(a)
					i = 0
					while i < a.length - 1 && a[i] <= a[i + 1]
					i += 1
					end

					return i == a.length - 1
				end
			`)
			modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Times(2)

			validate(t, &tasktesting.TestCaseTask{
				Name: "Multiple test cases",

				Model:          modelMock,
				Language:       &ruby.Language{},
				TestDataPath:   temporaryDirectoryPath,
				RepositoryPath: filepath.Join("ruby", "transpile"),

				ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
					IdentifierTranspile: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  160,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
					IdentifierTranspileSymflowerFix: metrics.Assessments{
						metrics.AssessmentKeyTestsPassing:                  160,
						metrics.AssessmentKeyFilesExecuted:                 4,
						metrics.AssessmentKeyFilesExecutedMaximumReachable: 4,
						metrics.AssessmentKeyResponseNoError:               4,
					},
				},
				ValidateLog: func(t *testing.T, data string) {
					assert.Equal(t, 2, strings.Count(data, "3 runs, 3 assertions, 0 failures, 0 errors, 0 skips"))
				},
			})
		}
	})

	{
		temporaryDirectoryPath := t.TempDir()

		repositoryPath := filepath.Join(temporaryDirectoryPath, "golang", "transpile", "cascadingIfElse")
		require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", "golang", "transpile", "cascadingIfElse"), repositoryPath))

		modelMock := modeltesting.NewMockCapabilityTranspileNamed(t, "mocked-model")

		transpiledSourceFilePath := "cascadingIfElse_.go"
		transpiledSourceFileContent := bytesutil.StringTrimIndentations(`
			invalid-code
		`)
		modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Once()

		transpiledSourceFilePath = "cascadingIfElse.go"
		transpiledSourceFileContent = bytesutil.StringTrimIndentations(`
			package cascadingIfElse

			func cascadingIfElse(i int) int {
				if i == 1 {
					return 2
				} else if i == 3 {
					return 4
				} else {
					return 5
				}
			}
		`)
		modelMock.RegisterGenerateSuccess(t, validateContext, transpiledSourceFilePath, transpiledSourceFileContent, metricstesting.AssessmentsWithProcessingTime).Once()

		validate(t, &tasktesting.TestCaseTask{
			Name: "Reset repository after each origin language",

			Model:          modelMock,
			Language:       &golang.Language{},
			TestDataPath:   temporaryDirectoryPath,
			RepositoryPath: filepath.Join("golang", "transpile"),

			ExpectedRepositoryAssessment: map[evaltask.Identifier]metrics.Assessments{
				IdentifierTranspile: metrics.Assessments{
					metrics.AssessmentKeyTestsPassing:                  40,
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
					metrics.AssessmentKeyResponseNoError:               2,
				},
				IdentifierTranspileSymflowerFix: metrics.Assessments{
					metrics.AssessmentKeyTestsPassing:                  40,
					metrics.AssessmentKeyFilesExecuted:                 1,
					metrics.AssessmentKeyFilesExecutedMaximumReachable: 2,
					metrics.AssessmentKeyResponseNoError:               2,
				},
			},
			ExpectedProblemContains: []string{
				"expected 'package', found invalid",
				"A fatal error happened. Please take a look at the logs", // This is `symflower fix` unable to read the broken Go file.
			},
			ValidateLog: func(t *testing.T, data string) {
				assert.Contains(t, data, "expected 'package', found invalid")
				assert.Contains(t, data, "PASS: TestSymflowerCascadingIfElse")
			},
		})
	}
}

func TestValidateTranspileRepository(t *testing.T) {
	validate := func(t *testing.T, tc *tasktesting.TestCaseValidateRepository) {
		tc.Validate(t, validateTranspileRepository)
	}

	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Package does not contain implementation folder",

		Before: func(repositoryPath string) {
			require.NoError(t, os.MkdirAll(filepath.Join(repositoryPath, "somePackage"), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			var errorMessage string
			if osutil.IsWindows() {
				errorMessage = "The system cannot find the file specified"
			} else {
				errorMessage = "no such file or directory"
			}
			assert.ErrorContains(t, err, errorMessage)
		},
	})
	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Implementation folder contains multiple files of the same language",

		Before: func(repositoryPath string) {
			require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "balancedBrackets", "implementation", "Class.java"), []byte(`content`), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			assert.ErrorContains(t, err, "must contain only one source file per language")
		},
	})
	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Implementation folder does not contain all required languages",

		Before: func(repositoryPath string) {
			implementationPath := filepath.Join(repositoryPath, "somePackage", "implementation")
			require.NoError(t, os.MkdirAll(implementationPath, 0700))
			require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "Class.java"), []byte(`content`), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			assert.ErrorContains(t, err, "must contain source files for every language to prevent imbalance")
		},
	})
	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Implementation folder must contain only files",

		Before: func(repositoryPath string) {
			require.NoError(t, os.MkdirAll(filepath.Join(repositoryPath, "somePackage", "implementation", "someFolder"), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			assert.ErrorContains(t, err, "must contain only source code files to transpile, but found one directory")
		},
	})
	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Implementation folder must contain only source files",

		Before: func(repositoryPath string) {
			implementationFolderPath := filepath.Join(repositoryPath, "somePackage", "implementation")
			require.NoError(t, os.MkdirAll(implementationFolderPath, 0700))
			require.NoError(t, os.WriteFile(filepath.Join(implementationFolderPath, "ClassTest.java"), []byte(`content`), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			assert.ErrorContains(t, err, "must contain source files, but found a test file")
		},
	})
	validate(t, &tasktesting.TestCaseValidateRepository{
		Name: "Unsupported language",

		Before: func(repositoryPath string) {
			implementationFolderPath := filepath.Join(repositoryPath, "somePackage", "implementation")
			require.NoError(t, os.MkdirAll(implementationFolderPath, 0700))
			require.NoError(t, os.WriteFile(filepath.Join(implementationFolderPath, "file.unsupported"), []byte(`content`), 0700))
		},

		TestdataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "transpile"),
		Language:       &golang.Language{},

		ExpectedError: func(t *testing.T, err error) {
			assert.ErrorContains(t, err, "the language extension \".unsupported\" is not supported")
		},
	})
	t.Run("Go", func(t *testing.T) {
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Package without source file",

			Before: func(repositoryPath string) {
				implementationPath := filepath.Join(repositoryPath, "somePackage", "implementation")
				require.NoError(t, os.MkdirAll(implementationPath, 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "Class.java"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.rb"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("golang", "transpile"),
			Language:       &golang.Language{},

			ExpectedError: func(t *testing.T, err error) {
				assert.ErrorContains(t, err, "must contain exactly one Go source file")
			},
		})
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Package without test file",

			Before: func(repositoryPath string) {
				implementationPath := filepath.Join(repositoryPath, "somePackage", "implementation")
				require.NoError(t, os.MkdirAll(implementationPath, 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "Class.java"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.rb"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "somePackage", "file.go"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("golang", "transpile"),
			Language:       &golang.Language{},

			ExpectedError: func(t *testing.T, err error) {
				assert.ErrorContains(t, err, "must contain exactly one Go test file")
			},
		})
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Well-formed",

			Before: func(repositoryPath string) {
				require.NoError(t, osutil.MkdirAll(filepath.Join(repositoryPath, ".git")))
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, ".git", "index"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("golang", "transpile"),
			Language:       &golang.Language{},
		})
	})
	t.Run("Java", func(t *testing.T) {
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Package without source file",

			Before: func(repositoryPath string) {
				implementationPath := filepath.Join(repositoryPath, "somePackage", "implementation")
				require.NoError(t, os.MkdirAll(implementationPath, 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.go"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.rb"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("java", "transpile"),
			Language:       &java.Language{},

			ExpectedError: func(t *testing.T, err error) {
				assert.ErrorContains(t, err, "must contain exactly one Java source file")
			},
		})
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Package without test file",

			Before: func(repositoryPath string) {
				implementationPath := filepath.Join(repositoryPath, "somePackage", "implementation")
				require.NoError(t, os.MkdirAll(implementationPath, 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.go"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(implementationPath, "file.rb"), []byte(`content`), 0700))
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "somePackage", "Class.java"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("java", "transpile"),
			Language:       &java.Language{},

			ExpectedError: func(t *testing.T, err error) {
				assert.ErrorContains(t, err, "must contain exactly one Java test file")
			},
		})
		validate(t, &tasktesting.TestCaseValidateRepository{
			Name: "Well-formed",

			Before: func(repositoryPath string) {
				require.NoError(t, osutil.MkdirAll(filepath.Join(repositoryPath, ".git")))
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, ".git", "index"), []byte(`content`), 0700))
			},

			TestdataPath:   filepath.Join("..", "..", "testdata"),
			RepositoryPath: filepath.Join("java", "transpile"),
			Language:       &java.Language{},
		})
	})
}

func TestTaskTranspileUnpackTranspilerPackage(t *testing.T) {
	type testCase struct {
		Name string

		DestinationLanguage language.Language

		RepositoryPath string
		PackagePath    string

		ExpectedOriginFilePathsWithLanguage map[string]language.Language
		ExpectedStubFilePath                string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Logf("Logging output: %s", logOutput.String())
				}
			}()

			temporaryDirectory := t.TempDir()

			require.NoError(t, osutil.CopyTree(filepath.Join("..", "..", "testdata", tc.RepositoryPath), filepath.Join(temporaryDirectory, "testdata", tc.RepositoryPath)))

			repository, cleanup, err := TemporaryRepository(logger, filepath.Join(temporaryDirectory, "testdata"), tc.RepositoryPath)
			require.NoError(t, err)
			defer cleanup()

			taskTranspile := TaskTranspile{}
			ctx := evaltask.Context{
				Language:   tc.DestinationLanguage,
				Repository: repository,
			}
			actualOriginFilePathsWithLanguage, actualStubFilePath, actualErr := taskTranspile.unpackTranspilerPackage(ctx, logger, tc.PackagePath)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedOriginFilePathsWithLanguage, actualOriginFilePathsWithLanguage)
			assert.Equal(t, tc.ExpectedStubFilePath, actualStubFilePath)
		})
	}

	t.Run("Go", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Transpile",

			DestinationLanguage: &golang.Language{},

			RepositoryPath: filepath.Join("golang", "transpile"),
			PackagePath:    "binarySearch",

			ExpectedOriginFilePathsWithLanguage: map[string]language.Language{
				filepath.Join("implementation", "BinarySearch.java"): &java.Language{},
				filepath.Join("implementation", "binary_search.rb"):  &ruby.Language{},
			},
			ExpectedStubFilePath: "binarySearch.go",
		})
	})
	t.Run("Java", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Transpile",

			DestinationLanguage: &java.Language{},

			RepositoryPath: filepath.Join("java", "transpile"),
			PackagePath:    "isSorted",

			ExpectedOriginFilePathsWithLanguage: map[string]language.Language{
				filepath.Join("implementation", "isSorted.go"): &golang.Language{},
				filepath.Join("implementation", "sort.rb"):     &ruby.Language{},
			},
			ExpectedStubFilePath: filepath.Join("src", "main", "java", "com", "eval", "IsSorted.java"),
		})
	})
}
