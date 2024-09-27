package providertesting

import (
	"testing"

	"github.com/stretchr/testify/mock"
	"github.com/symflower/eval-dev-quality/model"
)

// NewMockProviderNamedWithModels returns a new mocked provider with models.
func NewMockProviderNamedWithModels(t *testing.T, id string, models []model.Model) *MockProvider {
	m := NewMockProvider(t)
	m.On("Available", mock.Anything).Return(nil).Maybe()
	m.On("ID").Return(id).Maybe()
	m.On("Models").Return(models, nil).Maybe()

	return m
}

// OllamaTestModel holds the smallest Ollama model that we use for testing.
const OllamaTestModel = "qwen:0.5b"
