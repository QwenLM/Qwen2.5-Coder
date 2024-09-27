package openaiapi

import (
	"context"
	"strings"

	"github.com/sashabaranov/go-openai"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/provider"
)

// Provider holds a generic "OpenAI API" provider.
type Provider struct {
	baseURL string
	token   string
	id      string
	models  []model.Model
}

// NewProvider returns a generic "OpenAI API" provider.
func NewProvider(id string, baseURL string) (provider *Provider) {
	return &Provider{
		baseURL: baseURL,
		id:      id,
	}
}

var _ provider.Provider = (*Provider)(nil)

// Available checks if the provider is ready to be used.
// This might include checking for an installation or making sure an API access token is valid.
func (p *Provider) Available(logger *log.Logger) (err error) {
	return nil // We cannot know if a custom provider requires an API.
}

// ID returns the unique ID of this provider.
func (p *Provider) ID() (id string) {
	return p.id
}

// Models returns which models are available to be queried via this provider.
func (p *Provider) Models() (models []model.Model, err error) {
	return p.models, nil
}

// AddModel manually adds a model to the provider.
func (p *Provider) AddModel(m model.Model) {
	p.models = append(p.models, m)
}

var _ provider.InjectToken = (*Provider)(nil)

// SetToken sets a potential token to be used in case the provider needs to authenticate a remote API.
func (p *Provider) SetToken(token string) {
	p.token = token
}

var _ provider.Query = (*Provider)(nil)

// Query queries the provider with the given model name.
func (p *Provider) Query(ctx context.Context, modelIdentifier string, promptText string) (response string, err error) {
	client := p.client()
	modelIdentifier = strings.TrimPrefix(modelIdentifier, p.ID()+provider.ProviderModelSeparator)

	return QueryOpenAIAPIModel(ctx, client, modelIdentifier, promptText)
}

// client returns a new client with the current configuration.
func (p *Provider) client() (client *openai.Client) {
	config := openai.DefaultConfig(p.token)
	config.BaseURL = p.baseURL

	return openai.NewClientWithConfig(config)
}
