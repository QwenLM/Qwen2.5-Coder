package log

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"
)

func TestLoggerWith(t *testing.T) {
	type testCase struct {
		Name string

		Do func(logger *Logger, temporaryPath string)

		ExpectedLogOutput string
		ExpectedFiles     map[string]string
	}

	cleanOutput := func(data string, temporaryPath string) (newData string) {
		newData = strings.ReplaceAll(data, temporaryPath, "$TEMPORARY_PATH")
		newData = strings.ReplaceAll(newData, "\\", "/")

		return newData
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			defer func() {
				CloseOpenLogFiles()
			}()

			logOutput := new(bytesutil.SynchronizedBuffer)
			logger := newLoggerWithWriter(logOutput, FlagMessageOnly)

			temporaryPath := t.TempDir()

			tc.Do(logger, temporaryPath)

			actualResultFiles, err := osutil.FilesRecursive(temporaryPath)
			require.NoError(t, err)
			for i, p := range actualResultFiles {
				actualResultFiles[i], err = filepath.Rel(temporaryPath, p)
				require.NoError(t, err)
			}
			sort.Strings(actualResultFiles)
			var expectedResultFiles []string
			for filePath, expectedData := range tc.ExpectedFiles {
				expectedResultFiles = append(expectedResultFiles, filePath)

				data, err := os.ReadFile(filepath.Join(temporaryPath, filePath))
				require.NoError(t, err)

				actualData := string(data)
				actualData = cleanOutput(actualData, temporaryPath)
				expectedData = bytesutil.StringTrimIndentations(expectedData)
				assert.Equal(t, expectedData, actualData)
			}
			sort.Strings(expectedResultFiles)
			assert.Equal(t, expectedResultFiles, actualResultFiles)

			expectedLogOutput := bytesutil.StringTrimIndentations(tc.ExpectedLogOutput)
			assert.Equal(t, expectedLogOutput, cleanOutput(logOutput.String(), temporaryPath))
		})
	}

	validate(t, &testCase{
		Name: "New log file for Result path",

		Do: func(logger *Logger, temporaryPath string) {
			logger = logger.With(AttributeKeyResultPath, temporaryPath)

			logger.Info("Every log file")
		},

		ExpectedLogOutput: `
			Spawning new log file at $TEMPORARY_PATH/evaluation.log
			Every log file
		`,
		ExpectedFiles: map[string]string{
			"evaluation.log": `
				Every log file
			`,
		},
	})
	validate(t, &testCase{
		Name: "New log file for Language-Model-Repository-Task",

		Do: func(logger *Logger, temporaryPath string) {
			logger = logger.With(AttributeKeyResultPath, temporaryPath)
			logger = logger.With(AttributeKeyLanguage, "languageA")
			logger = logger.With(AttributeKeyModel, "modelA")
			logger = logger.With(AttributeKeyRepository, "repositoryA")
			logger = logger.With(AttributeKeyTask, "taskA")

			logger.Info("Every log file")
		},

		ExpectedLogOutput: `
			Spawning new log file at $TEMPORARY_PATH/evaluation.log
			Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
			Every log file
		`,
		ExpectedFiles: map[string]string{
			"evaluation.log": `
				Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
				Every log file
			`,
			filepath.Join("taskA", "modelA", "languageA", "repositoryA", "evaluation.log"): `
				Every log file
			`,
		},
	})

	validate(t, &testCase{
		Name: "New log file for two tasks",

		Do: func(logger *Logger, temporaryPath string) {
			logger = logger.With(AttributeKeyResultPath, temporaryPath)
			logger = logger.With(AttributeKeyLanguage, "languageA")
			logger = logger.With(AttributeKeyModel, "modelA")
			logger = logger.With(AttributeKeyRepository, "repositoryA")

			loggerA := logger.With(AttributeKeyTask, "taskA")
			_ = logger.With(AttributeKeyTask, "taskB")

			loggerA.Info("Only in A log files")
		},

		ExpectedLogOutput: `
			Spawning new log file at $TEMPORARY_PATH/evaluation.log
			Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
			Spawning new log file at $TEMPORARY_PATH/taskB/modelA/languageA/repositoryA/evaluation.log
			Only in A log files
		`,
		ExpectedFiles: map[string]string{
			"evaluation.log": `
				Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
				Spawning new log file at $TEMPORARY_PATH/taskB/modelA/languageA/repositoryA/evaluation.log
				Only in A log files
			`,
			filepath.Join("taskA", "modelA", "languageA", "repositoryA", "evaluation.log"): `
				Only in A log files
			`,
			filepath.Join("taskB", "modelA", "languageA", "repositoryA", "evaluation.log"): "",
		},
	})
	validate(t, &testCase{
		Name: "New log file for two repositories",

		Do: func(logger *Logger, temporaryPath string) {
			logger = logger.With(AttributeKeyResultPath, temporaryPath)
			logger = logger.With(AttributeKeyLanguage, "languageA")
			logger = logger.With(AttributeKeyModel, "modelA")

			loggerA := logger.With(AttributeKeyRepository, "repositoryA")
			_ = loggerA.With(AttributeKeyTask, "taskA")

			loggerB := logger.With(AttributeKeyRepository, "repositoryB")
			_ = loggerB.With(AttributeKeyTask, "taskA")

		},

		ExpectedLogOutput: `
			Spawning new log file at $TEMPORARY_PATH/evaluation.log
			Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
			Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryB/evaluation.log
		`,
		ExpectedFiles: map[string]string{
			"evaluation.log": `
				Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
				Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryB/evaluation.log
			`,
			filepath.Join("taskA", "modelA", "languageA", "repositoryA", "evaluation.log"): "",
			filepath.Join("taskA", "modelA", "languageA", "repositoryB", "evaluation.log"): "",
		},
	})

	t.Run("Artifacts", func(t *testing.T) {
		validate(t, &testCase{
			Name: "Response",

			Do: func(logger *Logger, temporaryPath string) {
				logger = logger.With(AttributeKeyResultPath, temporaryPath)
				logger = logger.With(AttributeKeyLanguage, "languageA")
				logger = logger.With(AttributeKeyModel, "modelA")
				logger = logger.With(AttributeKeyRepository, "repositoryA")
				logger = logger.With(AttributeKeyTask, "taskA")
				logger = logger.With(AttributeKeyRun, "1")

				logger.PrintWith("Artifact content", Attribute(AttributeKeyArtifact, "response"))
				logger.Print("No artifact content")
			},

			ExpectedLogOutput: `
				Spawning new log file at $TEMPORARY_PATH/evaluation.log
				Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
				Artifact content
				No artifact content
			`,
			ExpectedFiles: map[string]string{
				"evaluation.log": `
					Spawning new log file at $TEMPORARY_PATH/taskA/modelA/languageA/repositoryA/evaluation.log
					Artifact content
					No artifact content
				`,
				filepath.Join("taskA", "modelA", "languageA", "repositoryA", "evaluation.log"): `
					Artifact content
					No artifact content
				`,
				filepath.Join("taskA", "modelA", "languageA", "repositoryA", "response-1.log"): `
					Artifact content
				`,
			},
		})
	})
}

func TestCleanModelNameForFileSystem(t *testing.T) {
	type testCase struct {
		Name string

		ModelName string

		ExpectedModelNameCleaned string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualModelNameCleaned := CleanModelNameForFileSystem(tc.ModelName)

			assert.Equal(t, tc.ExpectedModelNameCleaned, actualModelNameCleaned)
		})
	}

	validate(t, &testCase{
		Name: "Simple",

		ModelName: "openrouter/anthropic/claude-2.0:beta",

		ExpectedModelNameCleaned: "openrouter_anthropic_claude-2.0_beta",
	})
}
