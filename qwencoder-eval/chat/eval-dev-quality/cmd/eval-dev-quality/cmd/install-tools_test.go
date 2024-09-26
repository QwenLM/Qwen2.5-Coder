package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/log"
)

func TestInstallTools(t *testing.T) {
	type testCase struct {
		Name string

		ExpectedInstalledToolNames []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()

			if osutil.IsWindows() {
				t.Setenv("PATH", temporaryPath)
			} else {
				chmodPath, err := exec.LookPath("chmod")
				require.NoError(t, err)
				t.Setenv("PATH", strings.Join([]string{temporaryPath, filepath.Dir(chmodPath)}, string(os.PathListSeparator)))
			}

			t.Run("Not yet installed", func(t *testing.T) {
				for _, toolName := range tc.ExpectedInstalledToolNames {
					toolPath, err := exec.LookPath(toolName)
					require.Error(t, err)
					require.Empty(t, toolPath)
				}
			})

			t.Run("Install for first time which should install successfully", func(t *testing.T) {
				logOutput, logger := log.Buffer()
				Execute(logger, []string{
					"install-tools",
					"--install-tools-path", temporaryPath,
				})

				for _, toolName := range tc.ExpectedInstalledToolNames {
					require.Contains(t, logOutput.String(), fmt.Sprintf(`Install %q to`, toolName))
					toolPath, err := exec.LookPath(toolName)
					require.NoError(t, err)
					require.NotEmpty(t, toolPath)
				}
			})

			t.Run("Install a second time which should install no new tools", func(t *testing.T) {
				logOutput, logger := log.Buffer()
				Execute(logger, []string{
					"install-tools",
					"--install-tools-path", temporaryPath,
				})

				for _, toolName := range tc.ExpectedInstalledToolNames {
					require.NotContains(t, logOutput.String(), fmt.Sprintf(`Install %q to`, toolName))
					toolPath, err := exec.LookPath(toolName)
					require.NoError(t, err)
					require.NotEmpty(t, toolPath)
				}
			})
		})
	}

	if osutil.IsLinux() {
		validate(t, &testCase{
			Name: "Default",

			ExpectedInstalledToolNames: []string{
				"ollama" + osutil.BinaryExtension(),
				"symflower" + osutil.BinaryExtension(),
			},
		})
	}
}
