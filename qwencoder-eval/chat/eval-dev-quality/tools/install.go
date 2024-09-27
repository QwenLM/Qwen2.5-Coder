package tools

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/lockfile"
	"github.com/zimmski/osutil"
)

var (
	// ErrToolVersionOutdated indicates that an installed tool is outdated.
	ErrToolVersionOutdated = errors.New("tool version mismatch")
	// ErrUnsupportedOperatingSystem indicates that the operating system is not supported by the tool.
	ErrUnsupportedOperatingSystem = errors.New("tool is not supported with the operating system")
)

// InstallPathDefault returns the default installation path for tools.
func InstallPathDefault() (installPath string, err error) {
	homePath, err := os.UserHomeDir()
	if err != nil {
		return "", pkgerrors.WithStack(pkgerrors.WithMessage(err, "cannot query home directory"))
	}

	return filepath.Join(homePath, ".eval-dev-quality", "bin"), nil
}

// Install install all basic evaluation tools.
func Install(logger *log.Logger, installPath string) (err error) {
	if err := InstallTool(logger, NewSymflower(), installPath); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, "cannot install Symflower"))
	}

	return nil
}

// InstallTool installs the given tool to the installation path.
func InstallTool(logger *log.Logger, tool Tool, installPath string) (err error) {
	// If the tool's binary is overwritten, at least make sure it is a file path.
	if tool.BinaryPath() != tool.BinaryName() {
		if osutil.FileExists(tool.BinaryPath()) != nil {
			return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("%s binary is not a valid file path", tool.BinaryPath())))
		}

		logger.Printf("Using %q binary %s", tool.ID(), tool.BinaryPath())

		return nil
	}

	installPath, err = filepath.Abs(installPath)
	if err != nil {
		return pkgerrors.WithStack(err)
	}

	if err := os.MkdirAll(installPath, 0755); err != nil {
		return pkgerrors.WithStack(err)
	}

	// Make sure only one process is installing a tool at the same time.
	lock, err := lockfile.New(filepath.Join(installPath, "install"+tool.ID()+".lock"))
	if err != nil {
		return pkgerrors.WithStack(err)
	}
	for {
		if err := lock.TryLock(); err == nil {
			break
		}

		logger.Printf("Try to lock %q for installing %q but need to wait for another process", installPath, tool.ID())
		time.Sleep(time.Second)
	}
	defer func() {
		if e := lock.Unlock(); e != nil {
			err = errors.Join(err, e)
		}
	}()

	// Check if install path is already used for binaries, or add it if not.
	installPathUsed := false
	for _, p := range strings.Split(os.Getenv(osutil.EnvironmentPathIdentifier), string(os.PathListSeparator)) {
		p = filepath.Clean(p)
		if p == installPath {
			installPathUsed = true

			break
		}
	}
	if !installPathUsed {
		if err := os.Setenv(osutil.EnvironmentPathIdentifier, strings.Join([]string{os.Getenv(osutil.EnvironmentPathIdentifier), installPath}, string(os.PathListSeparator))); err != nil { // Add the install path last, so we are not overwriting other binaries.
			return pkgerrors.WithStack(err)
		}
	}

	// Check if the binary can already be used.
	if toolPath, err := exec.LookPath(tool.BinaryName()); err == nil {
		logger.Printf("Checking %q binary %q version", tool.ID(), toolPath)

		err := tool.CheckVersion(logger, toolPath)
		if err == nil || !pkgerrors.Is(err, ErrToolVersionOutdated) {
			return err
		}

		// If the binary got installed by the user, let the user handle the update.
		if filepath.Dir(toolPath) != installPath {
			return pkgerrors.WithStack(fmt.Errorf("%q binary outdated, need at least %q", tool.ID(), tool.RequiredVersion()))
		}

		logger.Printf("Updating %q to %q", tool.ID(), tool.RequiredVersion())
	}

	// Install the tool as it is either outdated or not installed at all.
	logger.Printf("Install %q to %q", tool.ID(), installPath)
	if err := tool.Install(logger, installPath); err != nil {
		return err
	}

	return
}
