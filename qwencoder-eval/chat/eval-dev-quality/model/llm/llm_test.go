package llm

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

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
	"github.com/symflower/eval-dev-quality/language/java"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	providertesting "github.com/symflower/eval-dev-quality/provider/testing"
)

func TestModelGenerateTestsForFile(t *testing.T) {
	type testCase struct {
		Name string

		SetupMock func(mockedProvider *providertesting.MockQuery)

		Language          language.Language
		ModelID           string
		SourceFileContent string
		SourceFilePath    string

		ExpectedAssessment      metrics.Assessments
		ExpectedTestFileContent string
		ExpectedTestFilePath    string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(logOutput.String())
				}
			}()

			temporaryPath := t.TempDir()
			temporaryPath = filepath.Join(temporaryPath, "native")
			require.NoError(t, os.Mkdir(temporaryPath, 0755))

			require.NoError(t, os.WriteFile(filepath.Join(temporaryPath, tc.SourceFilePath), []byte(bytesutil.StringTrimIndentations(tc.SourceFileContent)), 0644))

			mock := providertesting.NewMockQuery(t)
			tc.SetupMock(mock)
			llm := NewModel(mock, tc.ModelID)

			ctx := model.Context{
				Language: tc.Language,

				RepositoryPath: temporaryPath,
				FilePath:       tc.SourceFilePath,

				Logger: logger,
			}
			actualAssessment, actualError := llm.WriteTests(ctx)
			assert.NoError(t, actualError)
			metricstesting.AssertAssessmentsEqual(t, tc.ExpectedAssessment, actualAssessment)

			actualTestFileContent, err := os.ReadFile(filepath.Join(temporaryPath, tc.ExpectedTestFilePath))
			assert.NoError(t, err)

			assert.Equal(t, strings.TrimSpace(bytesutil.StringTrimIndentations(tc.ExpectedTestFileContent)), string(actualTestFileContent))
		})
	}

	sourceFileContent := `
		package native

		func main() {}
	`
	sourceFilePath := "simple.go"
	promptMessage, err := llmGenerateTestForFilePrompt(&llmSourceFilePromptContext{
		Language: &golang.Language{},

		Code:       bytesutil.StringTrimIndentations(sourceFileContent),
		FilePath:   sourceFilePath,
		ImportPath: "native",
	})
	require.NoError(t, err)
	validate(t, &testCase{
		Name: "Simple",

		SetupMock: func(mockedProvider *providertesting.MockQuery) {
			mockedProvider.On("Query", mock.Anything, "model-id", promptMessage).Return(bytesutil.StringTrimIndentations(`
					`+"```"+`
					package native

					func TestMain() {}
					`+"```"+`
				`), nil)
		},

		Language:          &golang.Language{},
		ModelID:           "model-id",
		SourceFileContent: sourceFileContent,
		SourceFilePath:    sourceFilePath,

		ExpectedAssessment: metrics.Assessments{
			metrics.AssessmentKeyResponseNoExcess:                   1,
			metrics.AssessmentKeyResponseWithCode:                   1,
			metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 34,
			metrics.AssessmentKeyResponseCharacterCount:             43,
		},
		ExpectedTestFileContent: `
			package native

			func TestMain() {}
		`,
		ExpectedTestFilePath: "simple_test.go",
	})
}

func TestModelRepairSourceCodeFile(t *testing.T) {
	type testCase struct {
		Name string

		SetupMock func(t *testing.T, mockedProvider *providertesting.MockQuery)

		Language       language.Language
		RepositoryPath string
		SourceFilePath string

		Mistakes []string

		ExpectedAssessment        metrics.Assessments
		ExpectedSourceFileContent string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(logOutput.String())
				}
			}()

			temporaryPath := t.TempDir()
			repositoryPath := filepath.Join(temporaryPath, filepath.Base(tc.RepositoryPath))
			require.NoError(t, osutil.CopyTree(tc.RepositoryPath, repositoryPath))

			modelID := "some-model"
			mock := providertesting.NewMockQuery(t)
			tc.SetupMock(t, mock)
			llm := NewModel(mock, modelID)

			ctx := model.Context{
				Language: tc.Language,

				RepositoryPath: repositoryPath,
				FilePath:       tc.SourceFilePath,

				Arguments: &evaluatetask.TaskArgumentsCodeRepair{
					Mistakes: tc.Mistakes,
				},

				Logger: logger,
			}
			actualAssessment, actualError := llm.RepairCode(ctx)
			assert.NoError(t, actualError)
			metricstesting.AssertAssessmentsEqual(t, tc.ExpectedAssessment, actualAssessment)

			actualSourceFileContent, err := os.ReadFile(filepath.Join(repositoryPath, tc.SourceFilePath))
			assert.NoError(t, err)

			assert.Equal(t, strings.TrimSpace(bytesutil.StringTrimIndentations(tc.ExpectedSourceFileContent)), string(actualSourceFileContent))
		})
	}
	t.Run("Go", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Opening bracket is missing",

			SetupMock: func(t *testing.T, mockedProvider *providertesting.MockQuery) {
				mockedProvider.On("Query", mock.Anything, "some-model", mock.Anything).Return(bytesutil.StringTrimIndentations(`
					`+"```"+`
					package openingBracketMissing
					func openingBracketMissing(x int) int {
						if x > 0 {
							return 1
						}
						if x < 0 {
							return -1
						}
						return 0
					}
					`+"```"+`
				`), nil)
			},

			Language:       &golang.Language{},
			RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "mistakes", "openingBracketMissing"),
			SourceFilePath: "openingBracketMissing.go",

			Mistakes: []string{
				"./openingBracketMissing.go:4:2: syntax error: non-declaration statement outside function body",
			},

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedSourceFileContent: `
				package openingBracketMissing
				func openingBracketMissing(x int) int {
					if x > 0 {
						return 1
					}
					if x < 0 {
						return -1
					}
					return 0
				}
			`,
		})
	})
	t.Run("Java", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Opening bracket is missing",

			SetupMock: func(t *testing.T, mockedProvider *providertesting.MockQuery) {
				mockedProvider.On("Query", mock.Anything, "some-model", mock.Anything).Return(bytesutil.StringTrimIndentations(`
					`+"```"+`
					package com.eval;
					public class OpeningBracketMissing {
						public static int openingBracketMissing(int x) {
							if (x > 0) {
								return 1;
							}
							if (x < 0) {
								return -1;
							}
							return 0;
						}
					}
					`+"```"+`
				`), nil)
			},

			Language:       &java.Language{},
			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "mistakes", "openingBracketMissing"),
			SourceFilePath: filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java"),

			Mistakes: []string{
				"/src/main/java/com/eval/OpeningBracketMissing.java:[12,17] illegal start of type",
				"/src/main/java/com/eval/OpeningBracketMissing.java:[14,1] class, interface, or enum expected",
			},

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedSourceFileContent: `
				package com.eval;
				public class OpeningBracketMissing {
					public static int openingBracketMissing(int x) {
						if (x > 0) {
							return 1;
						}
						if (x < 0) {
							return -1;
						}
						return 0;
					}
				}
			`,
		})
	})
}

func TestLLMGenerateTestForFilePrompt(t *testing.T) {
	type testCase struct {
		Name string

		Data *llmSourceFilePromptContext

		ExpectedMessage string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualMessage, actualErr := llmGenerateTestForFilePrompt(tc.Data)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedMessage, actualMessage)
		})
	}

	validate(t, &testCase{
		Name: "Plain",

		Data: &llmSourceFilePromptContext{
			Language: &golang.Language{},

			Code: bytesutil.StringTrimIndentations(`
					package increment

					func increment(i int) int
						return i + 1
					}
				`),
			FilePath:   filepath.Join("path", "to", "increment.go"),
			ImportPath: "increment",
		},

		ExpectedMessage: bytesutil.StringTrimIndentations(`
			Given the following Go code file "path/to/increment.go" with package "increment", provide a test file for this code.
			The tests should produce 100 percent code coverage and must compile.
			The response must contain only the test code in a fenced code block and nothing else.

			` + "```" + `golang
			package increment

			func increment(i int) int
				return i + 1
			}
			` + "```" + `
		`),
	})
}

func TestLLMCodeRepairSourceFilePrompt(t *testing.T) {
	type testCase struct {
		Name string

		Data *llmCodeRepairSourceFilePromptContext

		ExpectedMessage string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualMessage, actualErr := llmCodeRepairSourceFilePrompt(tc.Data)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedMessage, actualMessage)
		})
	}

	validate(t, &testCase{
		Name: "Plain",

		Data: &llmCodeRepairSourceFilePromptContext{
			llmSourceFilePromptContext: llmSourceFilePromptContext{
				Language: &golang.Language{},

				Code: bytesutil.StringTrimIndentations(`
					package increment

					func increment(i int) int
						return i + 1
					}
				`),
				FilePath:   filepath.Join("path", "to", "increment.go"),
				ImportPath: "increment",
			},
			Mistakes: []string{
				"path/to/increment.go:3:1: expected 'IDENT', found 'func'",
				"path/to/increment.go: syntax error: non-declaration statement outside function body",
				"path/to/increment.go: missing return",
			},
		},

		ExpectedMessage: bytesutil.StringTrimIndentations(`
			Given the following Go code file "path/to/increment.go" with package "increment" and a list of compilation errors, modify the code such that the errors are resolved.
			The response must contain only the source code in a fenced code block and nothing else.

			` + "```" + `golang
			package increment

			func increment(i int) int
				return i + 1
			}
			` + "```" + `

			The list of compilation errors is the following:
			- path/to/increment.go:3:1: expected 'IDENT', found 'func'
			- path/to/increment.go: syntax error: non-declaration statement outside function body
			- path/to/increment.go: missing return
		`),
	})
}

func TestLLMTranspileSourceFilePrompt(t *testing.T) {
	type testCase struct {
		Name string

		Data *llmTranspileSourceFilePromptContext

		ExpectedMessage string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualMessage, actualErr := llmTranspileSourceFilePrompt(tc.Data)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedMessage, actualMessage)
		})
	}

	validate(t, &testCase{
		Name: "Transpile Go into Java",

		Data: &llmTranspileSourceFilePromptContext{
			llmSourceFilePromptContext: llmSourceFilePromptContext{
				Language: &java.Language{},

				Code: bytesutil.StringTrimIndentations(`
					package com.eval;

					class Foobar {
						static int foobar(int i) {}
					}
				`),
				FilePath:   "Foobar.java",
				ImportPath: "com.eval",
			},
			OriginLanguage: &golang.Language{},
			OriginFileContent: bytesutil.StringTrimIndentations(`
				package foobar

				func foobar(i int) int {
					return i + 1
				}
			`),
		},

		ExpectedMessage: bytesutil.StringTrimIndentations(`
			Given the following Go code file, transpile it into a Java code file.
			The response must contain only the transpiled Java source code in a fenced code block and nothing else.

			` + "```" + `golang
			package foobar

			func foobar(i int) int {
				return i + 1
			}
			` + "```" + `

			The transpiled Java code file must have the package "com.eval" and the following signature:

			` + "```" + `java
			package com.eval;

			class Foobar {
				static int foobar(int i) {}
			}
			` + "```" + `
		`),
	})
}

func TestModelTranspile(t *testing.T) {
	type testCase struct {
		Name string

		SetupMock func(t *testing.T, mockedProvider *providertesting.MockQuery)

		Language       language.Language
		OriginLanguage language.Language

		RepositoryPath string
		OriginFilePath string
		StubFilePath   string

		ExpectedAssessment      metrics.Assessments
		ExpectedStubFileContent string
	}

	validate := func(t *testing.T, tc *testCase) {
		logOutput, logger := log.Buffer()
		defer func() {
			if t.Failed() {
				t.Log(logOutput.String())
			}
		}()

		temporaryPath := t.TempDir()
		repositoryPath := filepath.Join(temporaryPath, filepath.Base(tc.RepositoryPath))
		require.NoError(t, osutil.CopyTree(tc.RepositoryPath, repositoryPath))

		modelID := "some-model"
		mock := providertesting.NewMockQuery(t)
		tc.SetupMock(t, mock)
		llm := NewModel(mock, modelID)

		ctx := model.Context{
			Language: tc.Language,

			RepositoryPath: repositoryPath,
			FilePath:       tc.StubFilePath,

			Arguments: &evaluatetask.TaskArgumentsTranspile{
				OriginLanguage: tc.OriginLanguage,
				OriginFilePath: tc.OriginFilePath,
			},

			Logger: logger,
		}

		actualAssessment, actualError := llm.Transpile(ctx)
		assert.NoError(t, actualError)
		metricstesting.AssertAssessmentsEqual(t, tc.ExpectedAssessment, actualAssessment)

		actualStubFileContent, err := os.ReadFile(filepath.Join(repositoryPath, tc.StubFilePath))
		assert.NoError(t, err)

		assert.Equal(t, strings.TrimSpace(tc.ExpectedStubFileContent), string(actualStubFileContent))
	}

	t.Run("Transpile Java into Go", func(t *testing.T) {
		transpiledFileContent := bytesutil.StringTrimIndentations(`
			package binarySearch

			func binarySearch(a []int, x int) int {
				index := -1

				min := 0
				max := len(a) - 1

				for index == -1 && min <= max {
					m := (min + max) / 2

					if x == a[m] {
						index = m
					} else if x < a[m] {
						max = m - 1
					} else {
						min = m + 1
					}
				}

				return index
			}
		`)
		validate(t, &testCase{
			Name: "Binary search",

			SetupMock: func(t *testing.T, mockedProvider *providertesting.MockQuery) {
				mockedProvider.On("Query", mock.Anything, "some-model", mock.Anything).Return("```\n"+transpiledFileContent+"```\n", nil)
			},

			Language:       &golang.Language{},
			OriginLanguage: &java.Language{},

			RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "transpile", "binarySearch"),
			OriginFilePath: filepath.Join("implementation", "BinarySearch.java"),
			StubFilePath:   filepath.Join("binarySearch.go"),

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedStubFileContent: transpiledFileContent,
		})
	})
	t.Run("Transpile Go into Java", func(t *testing.T) {
		transpiledFileContent := bytesutil.StringTrimIndentations(`
			package com.eval;

			class BinarySearch {
				static int binarySearch(int[] a, int x) {
					int index = -1;

					int min = 0;
					int max = a.length - 1;

					while (index == -1 && min <= max) {
						int m = (min + max) / 2;

						if (x == a[m]) {
							index = m;
						} else if (x < a[m]) {
							max = m - 1;
						} else {
							min = m + 1;
						}
					}

					return index;
				}
			}
		`)
		validate(t, &testCase{
			Name: "Binary Search",

			SetupMock: func(t *testing.T, mockedProvider *providertesting.MockQuery) {
				mockedProvider.On("Query", mock.Anything, "some-model", mock.Anything).Return("```\n"+transpiledFileContent+"```\n", nil)
			},

			Language:       &java.Language{},
			OriginLanguage: &golang.Language{},

			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "transpile", "binarySearch"),
			OriginFilePath: filepath.Join("implementation", "binarySearch.go"),
			StubFilePath:   filepath.Join("src", "main", "java", "com", "eval", "BinarySearch.java"),

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedStubFileContent: transpiledFileContent,
		})
	})
}
