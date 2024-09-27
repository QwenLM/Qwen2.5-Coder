package toolstesting

import (
	"testing"

	pkgerrors "github.com/pkg/errors"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
)

// RequiresTool checks if the tool is installed and up-to-date and fails otherwise.
func RequiresTool(t *testing.T, tool tools.Tool) {
	buffer, logger := log.Buffer()
	if err := tool.CheckVersion(logger, tool.BinaryPath()); err != nil {
		if pkgerrors.Is(err, tools.ErrToolVersionOutdated) {
			t.Logf("%q is outdated, requires at least %s: %+v", tool.ID(), tool.RequiredVersion(), pkgerrors.WithStack(pkgerrors.WithMessage(err, buffer.String())))
		} else {
			t.Logf("%q unusable because of: %+v", tool.ID(), pkgerrors.WithStack(err))
		}

		t.FailNow()
	}
}
