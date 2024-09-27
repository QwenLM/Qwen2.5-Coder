package tools

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/util"
	"github.com/zimmski/osutil"
)

// symflower holds the "Symflower" tool.
type symflower struct{}

func init() {
	Register(NewSymflower())
}

// NewSymflower returns a new Symflower tool.
func NewSymflower() Tool {
	return &symflower{}
}

var _ Tool = &symflower{}

// ID returns the unique ID of this tool.
func (*symflower) ID() (id string) {
	return "symflower"
}

// BinaryName returns the name of the tool's binary.
func (*symflower) BinaryName() string {
	return "symflower" + osutil.BinaryExtension()
}

// SymflowerPath holds the file path to the Symflower binary or the command name that should be executed.
var SymflowerPath = "symflower" + osutil.BinaryExtension()

// BinaryPath returns the file path of the tool's binary or the command name that should be executed.
// The binary path might also be just the binary name in case the tool is expected to be on the system path.
func (*symflower) BinaryPath() string {
	return SymflowerPath
}

// CheckVersion checks if the tool's version is compatible with the required version.
func (*symflower) CheckVersion(logger *log.Logger, binaryPath string) (err error) {
	symflowerVersionOutput, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{binaryPath, "version"},
	})
	if err != nil {
		return pkgerrors.WithStack(err)
	}

	// Development version of symflower is always OK to use.
	if strings.Contains(symflowerVersionOutput, " development on") {
		if !strings.Contains(symflowerVersionOutput, "symflower-local development on") {
			return pkgerrors.WithStack(errors.New("allow symflower binary to be used concurrently with its shared folder"))
		}

		return nil
	}

	m := regexp.MustCompile(`symflower v(\d+) on`).FindStringSubmatch(symflowerVersionOutput)
	if m == nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(errors.New("cannot find version"), symflowerVersionOutput))
	}

	// Currently the symflower version is only one integer, so do a poor-man's version comparision.
	symflowerVersionInstalled, err := strconv.ParseUint(m[1], 10, 64)
	if err != nil {
		return pkgerrors.WithStack(err)
	}
	symflowerVersionWanted, err := strconv.ParseUint(SymflowerVersionRequired, 10, 64)
	if err != nil {
		return pkgerrors.WithStack(err)
	}

	// Binary is installed in a compatible version.
	if symflowerVersionInstalled >= symflowerVersionWanted {
		return nil
	}

	return pkgerrors.WithStack(ErrToolVersionOutdated)
}

// SymflowerVersionRequired holds the version of Symflower required for this revision of the evaluation.
const SymflowerVersionRequired = "39758"

// RequiredVersion returns the required version of the tool.
func (*symflower) RequiredVersion() string {
	return SymflowerVersionRequired
}

// Install installs the tool's binary to the given install path.
func (*symflower) Install(logger *log.Logger, installPath string) (err error) {
	osIdentifier := runtime.GOOS
	var architectureIdentifier string
	switch a := runtime.GOARCH; a {
	case "386":
		architectureIdentifier = "x86"
	case "amd64":
		architectureIdentifier = "x86_64"
	case "arm":
		architectureIdentifier = "arm"
	case "arm64":
		architectureIdentifier = "arm64"
	default:
		return pkgerrors.WithStack(fmt.Errorf("unkown architecture %s", a))
	}

	symflowerDownloadURL := "https://download.symflower.com/local/v" + SymflowerVersionRequired + "/symflower-" + osIdentifier + "-" + architectureIdentifier + osutil.BinaryExtension()
	symflowerInstallPath := filepath.Join(installPath, "symflower"+osutil.BinaryExtension())
	logger.Printf("Install \"symflower\" to %s from %s", symflowerInstallPath, symflowerDownloadURL)
	if err := osutil.DownloadFileWithProgress(symflowerDownloadURL, symflowerInstallPath); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("cannot download to %s from %s", symflowerInstallPath, symflowerDownloadURL)))
	}

	// Non-Windows binaries need to be made executable because the executable bit is not set for downloads.
	if !osutil.IsWindows() {
		if _, err := util.CommandWithResult(context.Background(), logger, &util.Command{
			Command: []string{"chmod", "+x", symflowerInstallPath},
		}); err != nil {
			return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("cannot make %s executable", symflowerInstallPath)))
		}
	}

	return nil
}
