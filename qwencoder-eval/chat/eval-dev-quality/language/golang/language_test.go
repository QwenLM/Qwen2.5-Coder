package golang

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/language"
	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
	"github.com/symflower/eval-dev-quality/log"
)

func TestLanguageFiles(t *testing.T) {
	type testCase struct {
		Name string

		Language *Language

		RepositoryPath string

		ExpectedFilePaths []string
		ExpectedError     error
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(logOutput.String())
				}
			}()

			if tc.Language == nil {
				tc.Language = &Language{}
			}
			actualFilePaths, actualError := tc.Language.Files(logger, tc.RepositoryPath)

			assert.Equal(t, tc.ExpectedFilePaths, actualFilePaths)
			assert.Equal(t, tc.ExpectedError, actualError)
		})
	}

	validate(t, &testCase{
		Name: "Plain",

		RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "plain"),

		ExpectedFilePaths: []string{
			"plain.go",
		},
	})
}

func TestLanguageExecute(t *testing.T) {
	validate := func(t *testing.T, tc *languagetesting.TestCaseExecuteTests) {
		if tc.Language == nil {
			tc.Language = &Language{}
		}

		tc.Validate(t)
	}

	validate(t, &languagetesting.TestCaseExecuteTests{
		Name: "No test files",

		RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "plain"),

		ExpectedTestResult: &language.TestResult{
			Coverage: 0,
		},
		ExpectedErrorText: "exit status 1",
	})

	t.Run("With test file", func(t *testing.T) {
		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Valid",

			RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "plain"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "plain_test.go"), []byte(bytesutil.StringTrimIndentations(`
					package plain

					import (
						"testing"
					)

					func TestPlain(t *testing.T) {
						plain()
					}
				`)), 0660))
			},

			ExpectedTestResult: &language.TestResult{
				TestsTotal: 1,
				TestsPass:  1,

				Coverage: 1,
			},
		})

		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Failing tests",

			RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "light"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "simpleIfElse_test.go"), []byte(bytesutil.StringTrimIndentations(`
					package light

					import (
						"testing"
					)

					func TestSimpleIfElse(t *testing.T) {
						simpleIfElse(1) // Get some coverage...
						t.Fail() // ...and then fail.
					}
				`)), 0660))
			},

			ExpectedTestResult: &language.TestResult{
				TestsTotal: 1,
				TestsPass:  0,

				Coverage: 1,
			},
			ExpectedProblemTexts: []string{
				"exit status 1", // Test execution fails.
			},
		})

		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Syntax error",

			RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "plain"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				require.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "plain_test.go"), []byte(bytesutil.StringTrimIndentations(`
					foobar
				`)), 0660))
			},

			ExpectedErrorText: "exit status 1",
		})
	})
}

func TestMistakes(t *testing.T) {
	type testCase struct {
		Name string

		RepositoryPath string

		ExpectedMistakes []string
	}

	validate := func(t *testing.T, tc *languagetesting.TestCaseMistakes) {
		tc.Validate(t)
	}

	validate(t, &languagetesting.TestCaseMistakes{
		Name: "Function without opening bracket",

		Language:       &Language{},
		RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "mistakes", "openingBracketMissing"),

		ExpectedMistakes: []string{
			"." + string(os.PathSeparator) + "openingBracketMissing.go" + ":4:2: syntax error: non-declaration statement outside function body",
		},
	})
}

func TestExtractMistakes(t *testing.T) {
	type testCase struct {
		Name string

		RawMistakes string

		ExpectedMistakes []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualMistakes := extractMistakes(tc.RawMistakes)

			assert.Equal(t, tc.ExpectedMistakes, actualMistakes)
		})
	}

	validate(t, &testCase{
		Name: "Single mistake",

		RawMistakes: bytesutil.StringTrimIndentations(`
			foobar
			# foobar
			./foobar.go:4:2: syntax error: non-declaration statement outside function body
		`),

		ExpectedMistakes: []string{
			"./foobar.go:4:2: syntax error: non-declaration statement outside function body",
		},
	})
	validate(t, &testCase{
		Name: "Multiple mistakes",

		RawMistakes: bytesutil.StringTrimIndentations(`
			foobar
			# foobar
			./foobar.go:3:1: expected 'IDENT', found 'func'
			./foobar.go:4:2: syntax error: non-declaration statement outside function body
			./foobar.go:5:1: missing return
		`),

		ExpectedMistakes: []string{
			"./foobar.go:3:1: expected 'IDENT', found 'func'",
			"./foobar.go:4:2: syntax error: non-declaration statement outside function body",
			"./foobar.go:5:1: missing return",
		},
	})
}

func TestParseSymflowerTestOutput(t *testing.T) {
	type testCase struct {
		Name string

		Data string

		ExpectedTestsTotal int
		ExpectedTestsPass  int
		ExpectedErr        error
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualTestsTotal, actualTestsPass, actualErr := parseSymflowerTestOutput(bytesutil.StringTrimIndentations(tc.Data))

			assert.Equal(t, tc.ExpectedTestsTotal, actualTestsTotal)
			assert.Equal(t, tc.ExpectedTestsPass, actualTestsPass)
			assert.Equal(t, tc.ExpectedErr, actualErr)
		})
	}

	validate(t, &testCase{
		Name: "Passing tests only",

		Data: `
			=== RUN   TestSymflowerIsSorted
			=== RUN   TestSymflowerIsSorted/#00
			--- PASS: TestSymflowerIsSorted/#00 (0.00s)
			=== RUN   TestSymflowerIsSorted/#01
			--- PASS: TestSymflowerIsSorted/#01 (0.00s)
			=== RUN   TestSymflowerIsSorted/#02
			--- PASS: TestSymflowerIsSorted/#02 (0.00s)
			=== RUN   TestSymflowerIsSorted/#03
			--- PASS: TestSymflowerIsSorted/#03 (0.00s)
			=== RUN   TestSymflowerIsSorted/#04
			--- PASS: TestSymflowerIsSorted/#04 (0.00s)
			--- PASS: TestSymflowerIsSorted (0.00s)
			PASS
			coverage: 100.0% of statements
			ok      isSorted        0.003s

			DONE 6 tests in 0.281s
		`,

		ExpectedTestsTotal: 6,
		ExpectedTestsPass:  6,
	})
	validate(t, &testCase{
		Name: "Failing tests",

		Data: `
			=== RUN   TestSymflowerIsSorted
			=== RUN   TestSymflowerIsSorted/#00
				isSorted_test.go:22:
							Error Trace:    /home/andreas/repos/eval-dev-quality/testdata/golang/transpile/isSorted/isSorted_test.go:22
							Error:          Not equal:
											expected: true
											actual  : false
							Test:           TestSymflowerIsSorted/#00
			--- FAIL: TestSymflowerIsSorted/#00 (0.00s)
			=== RUN   TestSymflowerIsSorted/#01
			--- PASS: TestSymflowerIsSorted/#01 (0.00s)
			=== RUN   TestSymflowerIsSorted/#02
			--- PASS: TestSymflowerIsSorted/#02 (0.00s)
			=== RUN   TestSymflowerIsSorted/#03
			--- PASS: TestSymflowerIsSorted/#03 (0.00s)
			=== RUN   TestSymflowerIsSorted/#04
			--- PASS: TestSymflowerIsSorted/#04 (0.00s)
			--- FAIL: TestSymflowerIsSorted (0.00s)
			FAIL
			coverage: 100.0% of statements
			exit status 1
			FAIL    isSorted        0.002s

			=== Failed
			=== FAIL: . TestSymflowerIsSorted/#00 (0.00s)
				isSorted_test.go:22:
							Error Trace:    /home/andreas/repos/eval-dev-quality/testdata/golang/transpile/isSorted/isSorted_test.go:22
							Error:          Not equal:
											expected: true
											actual  : false
							Test:           TestSymflowerIsSorted/#00

			=== FAIL: . TestSymflowerIsSorted (0.00s)

			DONE 6 tests, 2 failures in 0.288s
		`,

		ExpectedTestsTotal: 6,
		ExpectedTestsPass:  4,
	})
}
