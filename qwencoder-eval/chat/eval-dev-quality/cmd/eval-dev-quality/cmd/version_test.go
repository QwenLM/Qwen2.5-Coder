package cmd

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/symflower/eval-dev-quality/evaluate"
	"github.com/symflower/eval-dev-quality/log"
)

func TestVersionExecute(t *testing.T) {
	logOutput, logger := log.Buffer()

	Execute(logger, []string{"version"})

	expected := fmt.Sprintf("eval-dev-quality version %s - revision %s", evaluate.Version, "development")
	assert.Contains(t, logOutput.String(), expected)
}
