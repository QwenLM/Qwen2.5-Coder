package cmd

import (
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
)

// InstallTools holds the "install-tools" command.
type InstallTools struct {
	// InstallToolsPath determines where tools for the evaluation are installed.
	InstallToolsPath string `long:"install-tools-path" description:"Install tools for the evaluation into this path."`

	// logger holds the logger of the command.
	logger *log.Logger
}

var _ SetLogger = (*InstallTools)(nil)

// SetLogger sets the logger of the command.
func (command *InstallTools) SetLogger(logger *log.Logger) {
	command.logger = logger
}

// Execute executes the command.
func (command *InstallTools) Execute(args []string) (err error) {
	if command.InstallToolsPath == "" {
		command.InstallToolsPath, err = tools.InstallPathDefault()
		if err != nil {
			command.logger.Panicf("ERROR: %s", err)
		}
	}

	if err := tools.InstallAll(command.logger, command.InstallToolsPath); err != nil {
		command.logger.Panicf("ERROR: installing all tools unsuccessful: %s", err)
	}

	return nil
}
