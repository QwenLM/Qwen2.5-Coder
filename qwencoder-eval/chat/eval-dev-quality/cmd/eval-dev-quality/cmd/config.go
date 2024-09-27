package cmd

import (
	"encoding/json"
	"io"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/task"
	"github.com/zimmski/osutil"
)

// EvaluationConfiguration holds data of how an evaluation was configured.
type EvaluationConfiguration struct {
	// Models holds model configuration data.
	Models ModelsConfiguration
	// Repositories holds repository configuration data.
	Repositories RepositoryConfiguration
}

// ModelsConfiguration holds model data of how an evaluation was configured.
type ModelsConfiguration struct {
	// Selected holds the models selected for an evaluation.
	Selected []string
	// Available holds the models that were available at the time of an evaluation.
	Available []string
}

// RepositoryConfiguration holds repository data of how an evaluation was configured.
type RepositoryConfiguration struct {
	// Selected holds the repositories selected for an evaluation.
	Selected []string
	// Available holds the repositories that were available at the time of an evaluation including their tasks.
	Available map[string][]task.Identifier
}

// convertNamesToOSSpecific converts repository names to OS-specific names.
func (c *RepositoryConfiguration) convertNamesToOSSpecific(oldFileSeparator string, newFileSeparator string) {
	if !osutil.IsWindows() {
		return
	}

	for i, repository := range c.Selected {
		c.Selected[i] = strings.ReplaceAll(repository, oldFileSeparator, newFileSeparator)
	}
	available := make(map[string][]task.Identifier, len(c.Available))
	for repository, tasks := range c.Available {
		available[strings.ReplaceAll(repository, oldFileSeparator, newFileSeparator)] = tasks
	}
	c.Available = available
}

// Write stores the configuration in JSON format.
func (c *EvaluationConfiguration) Write(writer io.Writer) error {
	// Always store in UNIX file format to be cross-OS compatible.
	c.Repositories.convertNamesToOSSpecific("\\", "/")

	encoder := json.NewEncoder(writer)
	if err := encoder.Encode(c); err != nil {
		return pkgerrors.Wrap(err, "writing configuration")
	}

	return nil
}

// ReadEvaluationConfiguration reads an evaluation configuration file.
func ReadEvaluationConfiguration(reader io.Reader) (configuration *EvaluationConfiguration, err error) {
	decoder := json.NewDecoder(reader)
	if err := decoder.Decode(&configuration); err != nil {
		return nil, pkgerrors.Wrap(err, "reading configuration")
	}

	configuration.Repositories.convertNamesToOSSpecific("/", "\\")

	return configuration, nil
}

// NewEvaluationConfiguration creates an empty configuration.
func NewEvaluationConfiguration() *EvaluationConfiguration {
	return &EvaluationConfiguration{
		Repositories: RepositoryConfiguration{
			Available: map[string][]task.Identifier{},
		},
	}
}
