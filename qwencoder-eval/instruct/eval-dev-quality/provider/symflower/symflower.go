package symflower

import (
	pkgerrors "github.com/pkg/errors"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/model/symflower"
	"github.com/symflower/eval-dev-quality/provider"
	"github.com/symflower/eval-dev-quality/tools"
)

// Provider holds a Symflower provider.
type Provider struct{}

func init() {
	provider.Register(&Provider{})
}

// NewProvider returns a Symflower provider.
func NewProvider() (provider provider.Provider) {
	return &Provider{}
}

var _ provider.Provider = (*Provider)(nil)

// Available checks if the provider is ready to be used.
// This might include checking for an installation or making sure an API access token is valid.
func (p *Provider) Available(logger *log.Logger) (err error) {
	if err := tools.NewSymflower().CheckVersion(logger, tools.SymflowerPath); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, `"Symflower" version check unsuccessful`))
	}

	return nil
}

// ID returns the unique ID of this provider.
func (p *Provider) ID() (id string) {
	return "symflower"
}

// Models returns which models are available to be queried via this provider.
func (p *Provider) Models() (models []model.Model, err error) {
	return []model.Model{
		symflower.NewModel(),
	}, nil
}
