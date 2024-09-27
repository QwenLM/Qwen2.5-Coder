package symflower

import (
	"context"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/language/golang"
	"github.com/symflower/eval-dev-quality/language/java"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/tools"
	toolstesting "github.com/symflower/eval-dev-quality/tools/testing"
)

func TestModelGenerateTestsForFile(t *testing.T) {
	toolstesting.RequiresTool(t, tools.NewSymflower())

	type testCase struct {
		Name string

		Model    *Model
		Language language.Language

		RepositoryPath   string
		RepositoryChange func(t *testing.T, repositoryPath string)
		FilePath         string

		ExpectedAssessment   metrics.Assessments
		ExpectedCoverage     uint64
		ExpectedError        error
		ExpectedErrorHandler func(err error)
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

			if tc.RepositoryChange != nil {
				tc.RepositoryChange(t, repositoryPath)
			}

			if tc.Model == nil {
				tc.Model = NewModel()
			}
			ctx := model.Context{
				Language: tc.Language,

				RepositoryPath: repositoryPath,
				FilePath:       tc.FilePath,

				Logger: logger,
			}
			actualAssessment, actualError := tc.Model.WriteTests(ctx)

			if tc.ExpectedError != nil {
				assert.ErrorIs(t, tc.ExpectedError, actualError)
			} else if tc.ExpectedErrorHandler != nil {
				tc.ExpectedErrorHandler(actualError)
			} else {
				require.NoError(t, actualError)

				metricstesting.AssertAssessmentsEqual(t, tc.ExpectedAssessment, actualAssessment)

				actualTestResult, actualProblems, err := tc.Language.ExecuteTests(logger, repositoryPath)
				require.NoError(t, err)
				require.Empty(t, actualProblems)
				assert.Equal(t, tc.ExpectedCoverage, actualTestResult.Coverage)
			}
		})
	}

	validate(t, &testCase{
		Name: "Go",

		Language: &golang.Language{},

		RepositoryPath: filepath.Join("..", "..", "testdata", "golang", "plain"),
		FilePath:       "plain.go",

		ExpectedAssessment: metrics.Assessments{
			metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 254,
			metrics.AssessmentKeyResponseCharacterCount:             254,
			metrics.AssessmentKeyResponseNoExcess:                   1,
			metrics.AssessmentKeyResponseWithCode:                   1,
		},
		ExpectedCoverage: 1,
	})
	validate(t, &testCase{
		Name: "Java",

		Language: &java.Language{},

		RepositoryPath: filepath.Join("..", "..", "testdata", "java", "plain"),
		FilePath:       filepath.Join("src", "main", "java", "com", "eval", "Plain.java"),

		ExpectedAssessment: metrics.Assessments{
			metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 139,
			metrics.AssessmentKeyResponseCharacterCount:             139,
			metrics.AssessmentKeyResponseNoExcess:                   1,
			metrics.AssessmentKeyResponseWithCode:                   1,
		},
		ExpectedCoverage: 1,
	})
	t.Run("Timeout", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Timeout",

			Model:    NewModelWithTimeout(time.Duration(1 * time.Millisecond)),
			Language: &java.Language{},

			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "light"),
			FilePath:       filepath.Join("src", "main", "java", "com", "eval", "Knapsack.java"),

			ExpectedErrorHandler: func(err error) {
				if osutil.IsWindows() {
					isProcessKilled := strings.Contains(err.Error(), context.DeadlineExceeded.Error()) || strings.Contains(err.Error(), "exit status 1")
					assert.True(t, err != nil && isProcessKilled)
				} else {
					assert.ErrorContains(t, err, "signal: killed")
				}
			},
		})
	})
}

func TestExtractGeneratedFilePaths(t *testing.T) {
	type testCase struct {
		Name string

		Output string

		ExpectedFilePaths []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualSlice := extractGeneratedFilePaths(tc.Output)

			assert.Equal(t, tc.ExpectedFilePaths, actualSlice)
		})
	}

	validate(t, &testCase{
		Name: "Simple",

		Output: `src/main/java/com/eval/Plain.java: generated unit test file src/test/java/com/eval/PlainSymflowerTest.java`,

		ExpectedFilePaths: []string{
			`src/test/java/com/eval/PlainSymflowerTest.java`,
		},
	})
	validate(t, &testCase{
		Name: "Full output",

		Output: `2024/04/25 20:13:49 Evaluating model "symflower/symbolic-execution" using language "java" and repository "java/plain"
2024/04/25 20:13:49 $ symflower unit-tests --code-disable-fetch-dependencies --workspace /tmp/eval-dev-quality1527239031/plain src/main/java/com/eval/Plain.java
Analyzing workspace /tmp/eval-dev-quality1527239031/plain/
Search for Java files
Load dependency stdlib:@dev
Found 1 Java files
Found 0 problems in Java files
src/main/java/com/eval/Plain.java: found 1 symbols
src/main/java/com/eval/Plain.java: com.eval.Plain.plain: computing test cases
src/main/java/com/eval/Plain.java: com.eval.Plain.plain: computed 1 unit tests
src/main/java/com/eval/Plain.java: com.eval.Plain.plain: found 0 problems
Symflower's table driven test style is not supported, switching to basic style
src/main/java/com/eval/Plain.java: generated unit test file src/test/java/com/eval/PlainSymflowerTest.java
src/test/java/com/eval/Foo.java: generated unit test file src/test/java/com/eval/Foo.java
src/test/java/com/eval/Bar.java: generated unit test file src/test/java/com/eval/Bar.java
src/test/java/com/eval/FooBar.java: generated unit test file src/test/java/com/eval/FooBar.java
Analyzed 1 out of 1 source files
Had 0 errors that block a full analysis
Generated 1 test
Found 0 potential problems
[0;34mGive us your feedback and let us know how we can improve Symflower at hello@symflower.com or https://github.com/symflower/symflower. Thanks so much for youhelp![0m
2024/04/25 20:13:52 $ symflower test --language java --workspace /tmp/eval-dev-quality1527239031/plain
Total coverage 100.000000%
[0;34mGive us your feedback and let us know how we can improve Symflower at hello@symflower.com or https://github.com/symflower/symflower. Thanks so much for youhelp![0m
2024/04/25 20:13:58 Evaluated model "symflower/symbolic-execution" using language "java" and repository "java/plain": encountered 0 problems: []`,

		ExpectedFilePaths: []string{
			"src/test/java/com/eval/PlainSymflowerTest.java",
			"src/test/java/com/eval/Foo.java",
			"src/test/java/com/eval/Bar.java",
			"src/test/java/com/eval/FooBar.java",
		},
	})
}

func TestCountCharactersOfGeneratedFiles(t *testing.T) {
	if osutil.IsWindows() {
		t.Skip("Files created on Windows have different line endings")
	}

	type testCase struct {
		Name string

		RepositoryPath string
		FilePaths      []string

		ExpectedCount uint64
		ErrorValidate func(err error)
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()
			repositoryPath := filepath.Join(temporaryPath, filepath.Base(tc.RepositoryPath))
			require.NoError(t, osutil.CopyTree(tc.RepositoryPath, repositoryPath))

			actualCount, actualErr := countCharactersOfGeneratedFiles(tc.RepositoryPath, tc.FilePaths)
			if tc.ErrorValidate != nil {
				tc.ErrorValidate(actualErr)
			} else if actualErr != nil {
				t.Fatal(actualErr)
			}

			assert.Equal(t, tc.ExpectedCount, actualCount)
		})
	}

	validate(t, &testCase{
		Name: "File does not exist",

		RepositoryPath: filepath.Join("..", "..", "testdata"),
		FilePaths: []string{
			filepath.Join("file", "does", "not", "exist"),
		},

		ExpectedCount: 0,
		ErrorValidate: func(err error) {
			assert.ErrorContains(t, err, "no such file or directory")
		},
	})
	validate(t, &testCase{
		Name: "Go",

		RepositoryPath: filepath.Join("..", "..", "testdata"),
		FilePaths: []string{
			filepath.Join("golang", "plain", "plain.go"),
		},

		ExpectedCount: 102,
	})
	validate(t, &testCase{
		Name: "Java",

		RepositoryPath: filepath.Join("..", "..", "testdata"),
		FilePaths: []string{
			filepath.Join("java", "plain", "src", "main", "java", "com", "eval", "Plain.java"),
		},

		ExpectedCount: 67,
	})
	validate(t, &testCase{
		Name: "Go and Java",

		RepositoryPath: filepath.Join("..", "..", "testdata"),
		FilePaths: []string{
			filepath.Join("golang", "plain", "plain.go"),
			filepath.Join("java", "plain", "src", "main", "java", "com", "eval", "Plain.java"),
		},

		ExpectedCount: 169,
	})
}
