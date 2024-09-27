package tools

import (
	"testing"
)

func TestSymflowerInstall(t *testing.T) {
	ValidateInstallTool(t, NewSymflower())
}
