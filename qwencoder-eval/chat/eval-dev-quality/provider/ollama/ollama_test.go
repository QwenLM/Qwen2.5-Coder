package ollama

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/log"
	providertesting "github.com/symflower/eval-dev-quality/provider/testing"
	"github.com/symflower/eval-dev-quality/tools"
	toolstesting "github.com/symflower/eval-dev-quality/tools/testing"
)

func TestProviderStart(t *testing.T) {
	if !osutil.IsLinux() {
		t.Skipf("Installation of Ollama is not supported on this OS")
	}
	toolstesting.RequiresTool(t, tools.NewOllama())

	type testCase struct {
		Name string

		Before func(t *testing.T, logger *log.Logger, p *Provider) (cleanup func())

		ValidateLogs func(t *testing.T, output string)
	}

	url := "http://127.0.0.1:11435" // Use a unique URL for these tests, to not cache or get in the way of already running instances.

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			buffer, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(buffer.String())
				}
			}()

			provider := NewProvider().(*Provider)
			if tc.Before != nil {
				cleanup := tc.Before(t, logger, provider)
				if cleanup != nil {
					defer cleanup()
				}
			}

			provider.SetURL(url)

			shutdown, actualErr := provider.Start(logger)
			assert.NoError(t, actualErr)

			_, actualError := provider.Models()
			assert.NoError(t, actualError)

			if shutdown != nil {
				assert.NoError(t, shutdown())
			}

			if tc.ValidateLogs != nil {
				tc.ValidateLogs(t, buffer.String())
			}

			// Wait briefly to ensure all ports are freshly available for the next test case.
			time.Sleep(time.Second)
		})
	}

	validate(t, &testCase{
		Name: "Startup",

		ValidateLogs: func(t *testing.T, output string) {
			assert.Contains(t, output, "Starting new Ollama service on")
			assert.NotContains(t, output, "could not start Ollama service")
		},
	})
	validate(t, &testCase{
		Name: "Already running",

		Before: func(t *testing.T, logger *log.Logger, p *Provider) (cleanup func()) {
			shutdown, err := tools.OllamaStart(logger, tools.OllamaPath, url)
			require.NoError(t, err)

			return func() {
				assert.NoError(t, shutdown())
			}
		},

		ValidateLogs: func(t *testing.T, output string) {
			assert.Contains(t, output, "Reusing existing Ollama service on")
		},
	})
}

func TestProviderModels(t *testing.T) {
	if !osutil.IsLinux() {
		t.Skipf("Installation of Ollama is not supported on this OS")
	}
	toolstesting.RequiresTool(t, tools.NewOllama())

	type testCase struct {
		Name string

		LocalModels []string

		ExpectedModels []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			buffer, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(buffer.String())
				}
			}()

			provider := NewProvider().(*Provider)

			shutdown, err := provider.Start(logger)
			require.NoError(t, err)
			defer func() {
				require.NoError(t, shutdown())
			}()

			for _, modelName := range tc.LocalModels {
				require.NoError(t, tools.OllamaPull(logger, tools.OllamaPath, tools.OllamaURL, modelName))
			}

			actualModels, actualError := provider.Models()
			assert.NoError(t, actualError)

			modelNames := make([]string, len(actualModels))
			for i, model := range actualModels {
				modelNames[i] = model.ID()
			}
			for _, expectedModel := range tc.ExpectedModels {
				assert.Contains(t, modelNames, expectedModel)
			}

		})
	}

	validate(t, &testCase{
		Name: "Local Model",

		LocalModels: []string{
			providertesting.OllamaTestModel,
		},

		ExpectedModels: []string{
			"ollama/" + providertesting.OllamaTestModel,
		},
	})
}
