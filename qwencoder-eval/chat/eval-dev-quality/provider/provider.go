package provider

import (
	"context"

	pkgerrors "github.com/pkg/errors"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
)

// ProviderModelSeparator is the the separator between a provider and a model.
const ProviderModelSeparator = "/"

// Provider defines a provider to query models such as LLMs.
type Provider interface {
	// Available checks if the provider is ready to be used.
	// This might include checking for an installation or making sure an API access token is valid.
	Available(logger *log.Logger) (err error)
	// ID returns the unique ID of this provider.
	ID() (id string)
	// Models returns which models are available to be queried via this provider.
	Models() (models []model.Model, err error)
}

// Providers holds a register of all providers.
var Providers = map[string]Provider{}

// Register adds a provider to the common provider list.
func Register(provider Provider) {
	id := provider.ID()
	if _, ok := Providers[id]; ok {
		panic(pkgerrors.WithMessage(pkgerrors.New("provider was already registered"), id))
	}

	Providers[id] = provider
}

// InjectToken is a provider that needs an access token to authenticate a remote API.
type InjectToken interface {
	// SetToken sets an access token to be used to authenticate a remote API.
	SetToken(token string)
}

// Query is a provider that allows to query a model directly.
type Query interface {
	// Query queries the provider with the given model name.
	Query(ctx context.Context, modelIdentifier string, promptText string) (response string, err error)
}

// Service is a provider that requires background services.
type Service interface {
	// Start starts necessary background services to use this provider and returns a shutdown function.
	Start(logger *log.Logger) (shutdown func() (err error), err error)
}

// Loader is a provider that is able to load and unload models.
type Loader interface {
	// Load loads the given model.
	Load(modelIdentifier string) (err error)
	// Unload unloads the given model.
	Unload(modelIdentifier string) (err error)
}

// Puller is a provider that is capable of pulling models.
type Puller interface {
	// Pull downloads the given model.
	Pull(logger *log.Logger, modelIdentifier string) (err error)
}
