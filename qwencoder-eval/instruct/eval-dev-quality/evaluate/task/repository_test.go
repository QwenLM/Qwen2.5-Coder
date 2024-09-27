package task

import (
	"context"
	"os"
	"path/filepath"
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/task"
	"github.com/symflower/eval-dev-quality/util"
)

func TestTemporaryRepository(t *testing.T) {
	type testCase struct {
		Name string

		TestDataPath   string
		RepositoryPath string

		ExpectedTempPathRegex string
		ExpectedErr           error
		ValidateAfter         func(t *testing.T, logger *log.Logger, repositoryPath string)
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logBuffer, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Logf("Log Output:\n%s", logBuffer.String())
				}
			}()

			actualTemporaryRepository, cleanup, actualErr := TemporaryRepository(logger, tc.TestDataPath, tc.RepositoryPath)
			defer cleanup()

			assert.Regexp(t, regexp.QuoteMeta(filepath.Clean(os.TempDir())+string(os.PathSeparator))+tc.ExpectedTempPathRegex, actualTemporaryRepository, actualTemporaryRepository)
			assert.Equal(t, tc.ExpectedErr, actualErr)

			if tc.ValidateAfter != nil {
				tc.ValidateAfter(t, logger, actualTemporaryRepository.dataPath)
			}
		})
	}

	validate(t, &testCase{
		Name: "Create temporary path with git repository",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		ExpectedTempPathRegex: `eval-dev-quality\d+[\/\\]plain`,
		ExpectedErr:           nil,
		ValidateAfter: func(t *testing.T, logger *log.Logger, repositoryPath string) {
			output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
				Command: []string{
					"git",
					"log",
				},

				Directory: repositoryPath,
			})
			require.NoError(t, err)
			assert.Contains(t, output, "Author: dummy-name-temporary-repository")
		},
	})
}

func TestResetTemporaryRepository(t *testing.T) {
	type testCase struct {
		Name string

		TestDataPath   string
		RepositoryPath string

		ExpectedErr    error
		MutationBefore func(t *testing.T, path string)
		ValidateAfter  func(t *testing.T, path string)
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			_, logger := log.Buffer()
			temporaryRepository, cleanup, err := TemporaryRepository(logger, tc.TestDataPath, tc.RepositoryPath)
			assert.NoError(t, err)
			defer cleanup()

			tc.MutationBefore(t, temporaryRepository.dataPath)

			actualErr := temporaryRepository.Reset(logger)
			assert.Equal(t, tc.ExpectedErr, actualErr)

			tc.ValidateAfter(t, temporaryRepository.dataPath)
		})
	}

	validate(t, &testCase{
		Name: "Reset new file",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		ExpectedErr: nil,
		MutationBefore: func(t *testing.T, path string) {
			assert.NoError(t, os.WriteFile(filepath.Join(path, "foo"), []byte("foo"), 0600))
		},
		ValidateAfter: func(t *testing.T, path string) {
			assert.Error(t, osutil.FileExists(filepath.Join(path, "foo")))
		},
	})

	validate(t, &testCase{
		Name: "Reset modified file",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		ExpectedErr: nil,
		MutationBefore: func(t *testing.T, path string) {
			assert.NoError(t, os.WriteFile(filepath.Join(path, "plain.go"), []byte("foo"), 0600))
		},
		ValidateAfter: func(t *testing.T, path string) {
			content, err := os.ReadFile(filepath.Join(path, "plain.go"))
			require.NoError(t, err)
			assert.NotContains(t, string(content), "foo")
		},
	})
}

func TestRepositoryLoadConfiguration(t *testing.T) {
	type testCase struct {
		Name string

		TestDataPath   string
		RepositoryPath string

		ExpectedErrorText string
		MutationBefore    func(t *testing.T, path string)
		ValidateAfter     func(t *testing.T, repository *Repository)
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()
			temporaryRepositoryPath := filepath.Join(temporaryPath, tc.RepositoryPath)
			require.NoError(t, osutil.CopyTree(filepath.Join(tc.TestDataPath, tc.RepositoryPath), temporaryRepositoryPath))

			if tc.MutationBefore != nil {
				tc.MutationBefore(t, temporaryRepositoryPath)
			}

			_, logger := log.Buffer()
			actualRepository, cleanup, actualErr := TemporaryRepository(logger, temporaryPath, tc.RepositoryPath)
			defer cleanup()
			if tc.ExpectedErrorText != "" {
				assert.ErrorContains(t, actualErr, tc.ExpectedErrorText)
			} else {
				assert.NoError(t, actualErr)
			}

			if tc.ValidateAfter != nil {
				tc.ValidateAfter(t, actualRepository)
			}
		})
	}

	validate(t, &testCase{
		Name: "No configuration file",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		MutationBefore: func(t *testing.T, repositoryPath string) {
			assert.NoError(t, os.Remove(filepath.Join(repositoryPath, "repository.json")))
		},

		ValidateAfter: func(t *testing.T, repository *Repository) {
			assert.Equal(t, AllIdentifiers, repository.Tasks)
		},
	})
	validate(t, &testCase{
		Name: "Specify known task",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		ValidateAfter: func(t *testing.T, repository *Repository) {
			expectedTaskIdentifiers := []task.Identifier{
				IdentifierWriteTests,
			}
			assert.Equal(t, expectedTaskIdentifiers, repository.Tasks)
		},
	})
	validate(t, &testCase{
		Name: "Specify unknown task",

		TestDataPath:   filepath.Join("..", "..", "testdata"),
		RepositoryPath: filepath.Join("golang", "plain"),

		ExpectedErrorText: "task identifier \"unknown-task\" unknown",
		MutationBefore: func(t *testing.T, repositoryPath string) {
			configuration := bytesutil.StringTrimIndentations(`
				{
					"tasks": [
						"write-tests",
						"unknown-task"
					]
				}
			`)
			assert.NoError(t, os.WriteFile(filepath.Join(repositoryPath, "repository.json"), []byte(configuration), 0600))
		},
	})
}
