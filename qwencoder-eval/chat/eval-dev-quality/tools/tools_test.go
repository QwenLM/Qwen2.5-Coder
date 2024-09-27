package tools

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestInstallPathDefault(t *testing.T) {
	installPath, err := InstallPathDefault()
	assert.NoError(t, err)
	assert.NotEmpty(t, installPath)
}
