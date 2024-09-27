package cmd

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/log"
)

func TestExecute(t *testing.T) {
	type testCase struct {
		Name string

		Arguments []string

		ExpectedOutput string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()

			Execute(logger, tc.Arguments)

			assert.Equal(t, tc.ExpectedOutput, logOutput.String())
		})
	}

	if osutil.IsWindows() {
		validate(t, &testCase{
			Name: "No arguments should show help",

			ExpectedOutput: bytesutil.StringTrimIndentations(`
				Usage:
				  eval-dev-quality [OPTIONS] [command]

				Command to manage, update and actually execute the ` + "`" + `eval-dev-quality` + "`" + `
				evaluation benchmark.

				Help Options:
				  /?          Show this help message
				  /h, /help   Show this help message

				Available commands:
				  evaluate       Run an evaluation, by default with all defined models, repositories and tasks.
				  install-tools  Checks and installs all tools required for the evaluation benchmark.
				  report         Combines the results of multiple evaluations.
				  version        Display the version information of the binary.
			`),
		})
	} else {
		validate(t, &testCase{
			Name: "No arguments should show help",

			ExpectedOutput: bytesutil.StringTrimIndentations(`
				Usage:
				  eval-dev-quality [OPTIONS] [command]

				Command to manage, update and actually execute the ` + "`" + `eval-dev-quality` + "`" + `
				evaluation benchmark.

				Help Options:
				  -h, --help  Show this help message

				Available commands:
				  evaluate       Run an evaluation, by default with all defined models, repositories and tasks.
				  install-tools  Checks and installs all tools required for the evaluation benchmark.
				  report         Combines the results of multiple evaluations.
				  version        Display the version information of the binary.
			`),
		})
	}
}
