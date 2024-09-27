package openrouter

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/avast/retry-go"
	pkgerrors "github.com/pkg/errors"
	"github.com/sashabaranov/go-openai"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/model/llm"
	"github.com/symflower/eval-dev-quality/provider"
	openaiapi "github.com/symflower/eval-dev-quality/provider/openai-api"
)

// Provider holds an "openrouter.ai" provider using its public REST API.
type Provider struct {
	baseURL string
	token   string
}

func init() {
	provider.Register(NewProvider())
}

// NewProvider returns an "openrouter.ai" provider.
func NewProvider() (provider provider.Provider) {
	return &Provider{
		baseURL: "https://openrouter.ai/api/v1",
	}
}

var _ provider.Provider = (*Provider)(nil)

// Available checks if the provider is ready to be used.
// This might include checking for an installation or making sure an API access token is valid.
func (p *Provider) Available(logger *log.Logger) (err error) {
	if p.token == "" {
		return pkgerrors.WithStack(errors.New("missing access token"))
	}

	return nil
}

// ID returns the unique ID of this provider.
func (p *Provider) ID() (id string) {
	return "openrouter"
}

// ModelsList holds a list of models.
type ModelsList struct {
	Models []*model.MetaInformation `json:"data"`
}

// Models returns which models are available to be queried via this provider.
func (p *Provider) Models() (models []model.Model, err error) {
	responseModels, err := p.fetchModels()
	if err != nil {
		return nil, err
	}

	models = make([]model.Model, len(responseModels.Models))
	for i, model := range responseModels.Models {
		model.ID = p.ID() + provider.ProviderModelSeparator + model.ID
		models[i] = llm.NewModelWithMetaInformation(p, model.ID, model)
	}

	return models, nil
}

// fetchModels returns the list of models of the provider.
func (p *Provider) fetchModels() (models ModelsList, err error) {
	modelsURLPath, err := url.JoinPath(p.baseURL, "models")
	if err != nil {
		return ModelsList{}, pkgerrors.WithStack(err)
	}
	request, err := http.NewRequest("GET", modelsURLPath, nil)
	if err != nil {
		return ModelsList{}, pkgerrors.WithStack(err)
	}
	request.Header.Set("Accept", "application/json")

	client := &http.Client{}
	var responseBody []byte
	if err := retry.Do( // Query available models with a retry logic cause "openrouter.ai" has failed us in the past.
		func() error {
			response, err := client.Do(request)
			if err != nil {
				return pkgerrors.WithStack(err)
			}
			defer response.Body.Close()

			if response.StatusCode != http.StatusOK {
				return pkgerrors.Errorf("received status code %d when querying provider models", response.StatusCode)
			}

			responseBody, err = io.ReadAll(response.Body)
			if err != nil {
				return pkgerrors.WithStack(err)
			}

			return nil
		},
		retry.Attempts(3),
		retry.Delay(5*time.Second),
		retry.DelayType(retry.BackOffDelay),
		retry.LastErrorOnly(true),
	); err != nil {
		return ModelsList{}, err
	}

	if err = json.Unmarshal(responseBody, &models); err != nil {
		return ModelsList{}, pkgerrors.WithStack(err)
	}

	return models, nil
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

	return openaiapi.QueryOpenAIAPIModel(ctx, client, modelIdentifier, promptText)
}

// client returns a new client with the current configuration.
func (p *Provider) client() (client *openai.Client) {
	config := openai.DefaultConfig(p.token)
	config.BaseURL = p.baseURL

	return openai.NewClientWithConfig(config)
}
