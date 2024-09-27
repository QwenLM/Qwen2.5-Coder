package cmd

import (
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/symflower/eval-dev-quality/task"
	"github.com/zimmski/osutil/bytesutil"
)

func TestReadEvaluationConfiguration(t *testing.T) {
	configurationContent := bytesutil.StringTrimIndentations(`
		{
			"Models": {
				"Selected": [
					"openrouter/claude-3-sonnet",
					"symflower/symbolic-execution"
				],
				"Available": [
					"symflower/symbolic-execution"
				]
			},
			"Repositories": {
				"Selected": [
					"java/plain"
				],
				"Available": {
					"golang/light": [
						"write-tests"
					],
					"golang/mistakes": [
						"code-repair"
					],
					"golang/plain": [
						"write-tests"
					],
					"golang/transpile": [
						"transpile"
					],
					"java/light": [
						"write-tests"
					],
					"java/mistakes": [
						"code-repair"
					],
					"java/plain": [
						"write-tests"
					],
					"java/transpile": [
						"transpile"
					]
				}
			}
		}
	`)

	actualConfiguration, err := ReadEvaluationConfiguration(strings.NewReader(configurationContent))
	require.NoError(t, err)

	assert.Equal(t, &EvaluationConfiguration{
		Models: ModelsConfiguration{
			Available: []string{
				"symflower/symbolic-execution",
			},
			Selected: []string{
				"openrouter/claude-3-sonnet",
				"symflower/symbolic-execution",
			},
		},
		Repositories: RepositoryConfiguration{
			Available: map[string][]task.Identifier{
				filepath.Join("golang", "light"): []task.Identifier{
					"write-tests",
				},
				filepath.Join("golang", "mistakes"): []task.Identifier{
					"code-repair",
				},
				filepath.Join("golang", "plain"): []task.Identifier{
					"write-tests",
				},
				filepath.Join("golang", "transpile"): []task.Identifier{
					"transpile",
				},
				filepath.Join("java", "light"): []task.Identifier{
					"write-tests",
				},
				filepath.Join("java", "mistakes"): []task.Identifier{
					"code-repair",
				},
				filepath.Join("java", "plain"): []task.Identifier{
					"write-tests",
				},
				filepath.Join("java", "transpile"): []task.Identifier{
					"transpile",
				},
			},
			Selected: []string{
				filepath.Join("java", "plain"),
			},
		},
	}, actualConfiguration)
}
