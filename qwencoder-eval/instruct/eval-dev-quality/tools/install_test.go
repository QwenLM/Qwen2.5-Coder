package tools

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

// ValidateInstallTool validate the given tool.
func ValidateInstallTool(t *testing.T, tool Tool) {
	temporaryPath := t.TempDir()

	if osutil.IsWindows() {
		t.Setenv("PATH", temporaryPath)
	} else {
		chmodPath, err := exec.LookPath("chmod")
		require.NoError(t, err)
		t.Setenv("PATH", strings.Join([]string{temporaryPath, filepath.Dir(chmodPath)}, string(os.PathListSeparator)))
	}

	t.Run("Not yet installed", func(t *testing.T) {
		toolPath, err := exec.LookPath(tool.BinaryName())
		require.Error(t, err)
		require.Empty(t, toolPath)
	})

	t.Run("Install for first time which should install successfully", func(t *testing.T) {
		logOutput, logger := log.Buffer()
		require.NoError(t, InstallTool(logger, tool, temporaryPath))

		require.Contains(t, logOutput.String(), fmt.Sprintf(`Install %q to`, tool.ID()))
		toolPath, err := exec.LookPath(tool.BinaryName())
		require.NoError(t, err)
		require.NotEmpty(t, toolPath)
	})

	t.Run("Install a second time which should install no new tools", func(t *testing.T) {
		logOutput, logger := log.Buffer()
		require.NoError(t, InstallTool(logger, tool, temporaryPath))

		require.NotContains(t, logOutput.String(), fmt.Sprintf(`Install %q to`, tool.ID()))
		toolPath, err := exec.LookPath(tool.BinaryName())
		require.NoError(t, err)
		require.NotEmpty(t, toolPath)
	})
}
