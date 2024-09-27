package toolstesting

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
	"github.com/symflower/eval-dev-quality/util"
)

func TestRequiresTool(t *testing.T) {
	type testCase struct {
		Name string

		Invocation func(t *testing.T)

		ExpectedFailure string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			// This test runs "go test" on itself again in a subprocess to check if a crash actually happens (https://go.dev/talks/2014/testing.slide#23).
			if os.Getenv("INNER_INVOCATION_"+tc.Name) == "1" {
				tc.Invocation(t)

				return
			}

			buffer, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Logf("Logs:\n%s", buffer.String())
				}
			}()

			output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
				Command: []string{
					os.Args[0],
					filepath.Join("tools", "testing"),
					"-test.run=", "TestRequiresTool/" + tc.Name,
				},
				Env: map[string]string{
					"INNER_INVOCATION_" + tc.Name: "1",
				},
			})
			if tc.ExpectedFailure != "" {
				assert.Error(t, err)
				assert.Contains(t, output, tc.ExpectedFailure)
			} else {
				assert.NoError(t, err, output)
			}
		})
	}

	validate(t, &testCase{
		Name: "Version Up-To-Date",

		Invocation: func(t *testing.T) {
			mockTool := NewMockToolNamed(t, "some-tool")
			mockTool.On("CheckVersion", mock.Anything, mock.Anything).Return(nil).Once()

			RequiresTool(t, mockTool)
		},
	})
	validate(t, &testCase{
		Name: "Version Outdated",

		Invocation: func(t *testing.T) {
			mockTool := NewMockToolNamed(t, "some-tool")
			mockTool.On("CheckVersion", mock.Anything, mock.Anything).Return(tools.ErrToolVersionOutdated).Once()
			mockTool.On("RequiredVersion").Return("some-version").Once()

			RequiresTool(t, mockTool)
		},

		ExpectedFailure: `"some-tool" is outdated, requires at least some-version`,
	})
	validate(t, &testCase{
		Name: "Tool Unusable",

		Invocation: func(t *testing.T) {
			mockTool := NewMockToolNamed(t, "some-tool")
			mockTool.On("CheckVersion", mock.Anything, mock.Anything).Return(errors.New("some-error")).Once()

			RequiresTool(t, mockTool)
		},

		ExpectedFailure: `"some-tool" unusable because of: some-error`,
	})
}
