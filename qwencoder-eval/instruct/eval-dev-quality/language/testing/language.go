package languagetesting

import (
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	language "github.com/symflower/eval-dev-quality/language"
	log "github.com/symflower/eval-dev-quality/log"
	"github.com/zimmski/osutil"
)

type TestCaseExecuteTests struct {
	Name string

	Language language.Language

	RepositoryPath   string
	RepositoryChange func(t *testing.T, repositoryPath string)

	ExpectedTestResult   *language.TestResult
	ExpectedProblemTexts []string
	ExpectedError        error
	ExpectedErrorText    string
}

func (tc *TestCaseExecuteTests) Validate(t *testing.T) {
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

		actualTestResult, actualProblems, actualError := tc.Language.ExecuteTests(logger, repositoryPath)

		require.Equal(t, len(tc.ExpectedProblemTexts), len(actualProblems), "the number of expected problems need to match the number of actual problems")
		for i, expectedProblemText := range tc.ExpectedProblemTexts {
			assert.ErrorContains(t, actualProblems[i], expectedProblemText)
		}

		if tc.ExpectedError != nil {
			assert.ErrorIs(t, actualError, tc.ExpectedError)
		} else if actualError != nil && tc.ExpectedErrorText != "" {
			assert.ErrorContains(t, actualError, tc.ExpectedErrorText)
		} else {
			assert.NoError(t, actualError)
			assert.Equal(t, tc.ExpectedTestResult, actualTestResult)
		}
	})
}

type TestCaseMistakes struct {
	Name string

	Language       language.Language
	RepositoryPath string

	ExpectedMistakes         []string
	ExpectedMistakesContains func(t *testing.T, mistakes []string)
}

func (tc *TestCaseMistakes) Validate(t *testing.T) {
	t.Run(tc.Name, func(t *testing.T) {
		temporaryPath := t.TempDir()
		repositoryPath := filepath.Join(temporaryPath, filepath.Base(tc.RepositoryPath))
		require.NoError(t, osutil.CopyTree(tc.RepositoryPath, repositoryPath))

		buffer, logger := log.Buffer()
		defer func() {
			if t.Failed() {
				t.Log(buffer.String())
			}
		}()

		actualMistakes, actualErr := tc.Language.Mistakes(logger, repositoryPath)
		require.NoError(t, actualErr)

		if tc.ExpectedMistakesContains != nil {
			tc.ExpectedMistakesContains(t, actualMistakes)
		} else {
			assert.Equal(t, tc.ExpectedMistakes, actualMistakes)
		}
	})
}
