package openrouter

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	evalprovider "github.com/symflower/eval-dev-quality/provider"
)

func TestProviderModels(t *testing.T) {
	provider := NewProvider()

	models, err := provider.Models()

	require.NoError(t, err)
	assert.NotEmpty(t, models)

	// We prefix the models with the provider name, ensure that this is only done once.
	firstModelID := models[0].ID()
	assert.True(t, strings.HasPrefix(firstModelID, provider.ID()+evalprovider.ProviderModelSeparator))
	assert.Equal(t, 1, strings.Count(firstModelID, provider.ID()))
}
