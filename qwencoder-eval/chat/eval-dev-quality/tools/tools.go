package tools

import (
	"errors"
	"fmt"
	"sort"

	pkgerrors "github.com/pkg/errors"
	"golang.org/x/exp/maps"

	"github.com/symflower/eval-dev-quality/log"
)

// Tools holds a register of all tools.
var Tools = map[string]Tool{}

// Register adds a tool to the common tool list.
func Register(tool Tool) {
	id := tool.ID()
	if _, ok := Tools[id]; ok {
		panic(pkgerrors.WithMessage(pkgerrors.New("tool was already registered"), id))
	}

	Tools[id] = tool
}

// Tool defines an external tool.
type Tool interface {
	// ID returns the unique ID of this tool.
	ID() (id string)
	// BinaryName returns the name of the tool's binary.
	BinaryName() string
	// BinaryPath returns the file path of the tool's binary or the command name that should be executed.
	// The binary path might also be just the binary name in case the tool is expected to be on the system path.
	BinaryPath() string

	// CheckVersion checks if the tool's version is compatible with the required version.
	CheckVersion(logger *log.Logger, binaryPath string) error
	// RequiredVersion returns the required version of the tool.
	RequiredVersion() string

	// Install installs the tool's binary to the given install path.
	Install(logger *log.Logger, installPath string) error
}

// InstallAll installs all tools.
func InstallAll(logger *log.Logger, installPath string) (err error) {
	var installErrors []error
	toolKeys := maps.Keys(Tools)
	sort.Strings(toolKeys)
	for _, toolID := range toolKeys {
		tool := Tools[toolID]

		if err := InstallTool(logger, tool, installPath); err != nil {
			// Log if a tool is not supported by the operating system, but do not fail as it is not a necessary tool.
			if pkgerrors.Is(err, ErrUnsupportedOperatingSystem) {
				logger.Printf("WARNING: tool %s is not supported by the operating system", tool.ID())

				continue
			}

			err = pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("cannot install %q", tool.ID())))
			installErrors = append(installErrors, err)
		}
	}

	if len(installErrors) > 0 {
		return errors.Join(installErrors...)
	}

	return nil
}

// InstallEvaluation installs all basic evaluation tools.
func InstallEvaluation(logger *log.Logger, installPath string) (err error) {
	if err := InstallTool(logger, NewSymflower(), installPath); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, "cannot install Symflower"))
	}

	return nil
}
