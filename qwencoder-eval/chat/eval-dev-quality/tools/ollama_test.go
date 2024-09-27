package tools

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/log"
	providertesting "github.com/symflower/eval-dev-quality/provider/testing"
	"github.com/symflower/eval-dev-quality/util"
)

func TestOllamaInstall(t *testing.T) {
	if !osutil.IsLinux() {
		t.Skipf("Installation of Ollama is not supported on this OS")
	}

	ValidateInstallTool(t, NewOllama())
}

func TestStartOllama(t *testing.T) {
	if !osutil.IsLinux() {
		t.Skipf("Installation of Ollama is not supported on this OS")
	}

	buffer, logger := log.Buffer()
	defer func() {
		if t.Failed() {
			t.Log(buffer.String())
		}
	}()

	shutdown, err := OllamaStart(logger, OllamaPath, OllamaURL)
	assert.NoError(t, err)

	_, err = OllamaModels(OllamaURL)
	assert.NoError(t, err)

	time.Sleep(3 * time.Second)
	assert.NoError(t, shutdown())
}

func TestOllamaLoading(t *testing.T) {
	if !osutil.IsLinux() {
		t.Skipf("Installation of Ollama is not supported on this OS")
	}

	logBuffer, log := log.Buffer()
	defer func() {
		if t.Failed() {
			t.Logf("Log output:\n%s", logBuffer.String())
		}
	}()

	url := "http://127.0.0.1:11436" // Use a unique URL for these tests, to not cache or get in the way of already running instances.
	shutdown, err := OllamaStart(log, OllamaPath, url)
	require.NoError(t, err)
	defer func() {
		require.NoError(t, shutdown())
	}()
	require.NoError(t, OllamaPull(log, OllamaPath, url, providertesting.OllamaTestModel))

	t.Run("Load Model", func(t *testing.T) {
		assert.NoError(t, OllamaLoad(url, providertesting.OllamaTestModel))

		output, err := util.CommandWithResult(context.Background(), log, &util.Command{
			Command: []string{
				OllamaPath,
				"ps",
			},
			Env: map[string]string{
				"OLLAMA_HOST": url,
			},
		})
		assert.NoError(t, err)
		assert.Contains(t, output, providertesting.OllamaTestModel)
	})
	t.Run("unload Model", func(t *testing.T) {
		assert.NoError(t, OllamaUnload(url, providertesting.OllamaTestModel))

		// Give it a few seconds for the unloading completes.
		time.Sleep(2 * time.Second)

		output, err := util.CommandWithResult(context.Background(), log, &util.Command{
			Command: []string{
				OllamaPath,
				"ps",
			},
			Env: map[string]string{
				"OLLAMA_HOST": url,
			},
		})
		assert.NoError(t, err)
		assert.NotContains(t, output, providertesting.OllamaTestModel)
	})
}
