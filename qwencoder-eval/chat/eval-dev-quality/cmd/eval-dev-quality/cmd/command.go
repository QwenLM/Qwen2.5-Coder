package cmd

import (
	"github.com/jessevdk/go-flags"
	"github.com/symflower/eval-dev-quality/log"
)

// Command holds the root command.
type Command struct {
	Evaluate     `command:"evaluate" description:"Run an evaluation, by default with all defined models, repositories and tasks."`
	InstallTools `command:"install-tools" description:"Checks and installs all tools required for the evaluation benchmark."`
	Report       `command:"report" description:"Combines the results of multiple evaluations."`
	Version      `command:"version" description:"Display the version information of the binary."`
}

// Execute executes the root command.
func Execute(logger *log.Logger, arguments []string) {
	var parser = flags.NewNamedParser("eval-dev-quality", flags.Default)
	parser.LongDescription = "Command to manage, update and actually execute the `eval-dev-quality` evaluation benchmark."
	if _, err := parser.AddGroup("Common command options", "", &Command{}); err != nil {
		logger.Panicf("Could not add arguments group: %+v", err)
	}

	// Print the help, when there is no active command.
	parser.SubcommandsOptional = true

	parser.CommandHandler = func(command flags.Commander, args []string) (err error) {
		if command == nil {
			return nil
		}

		if c, ok := command.(SetLogger); ok {
			c.SetLogger(logger)
		}

		if c, ok := command.(SetArguments); ok {
			c.SetArguments(arguments)
		}

		return command.Execute(args)
	}

	if _, err := parser.ParseArgs(arguments); err != nil {
		if e, ok := err.(*flags.Error); ok && e.Type == flags.ErrHelp {
			return
		}

		logger.Panicf("Could not parse arguments: %+v", err)
	}
	if parser.Active == nil {
		logger.SetFlags(log.FlagMessageOnly)
		parser.WriteHelp(logger.Writer())
	}
}

// SetLogger defines a command that allows to set its logger.
type SetLogger interface {
	// SetLogger sets the logger of the command.
	SetLogger(logger *log.Logger)
}

// SetArguments defines a command that allows to set its arguments.
type SetArguments interface {
	// SetArguments sets the commands arguments.
	SetArguments(args []string)
}
