package symflower

import (
	"context"
	"os"
	"path/filepath"
	"regexp"
	"time"

	pkgerrors "github.com/pkg/errors"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/provider"
	"github.com/symflower/eval-dev-quality/tools"
	"github.com/symflower/eval-dev-quality/util"
)

// defaultSymbolicExecutionTimeout defines the default symbolic execution timeout.
var defaultSymbolicExecutionTimeout = time.Duration(10 * time.Minute)

// Model holds a Symflower model using the locally installed CLI.
type Model struct {
	// symbolicExecutionTimeout defines the symbolic execution timeout.
	symbolicExecutionTimeout time.Duration
}

// NewModel returns a Symflower model.
func NewModel() (model *Model) {
	return &Model{
		symbolicExecutionTimeout: defaultSymbolicExecutionTimeout,
	}
}

// NewModelWithTimeout returns a Symflower model with a given timeout.
func NewModelWithTimeout(timeout time.Duration) (model *Model) {
	return &Model{
		symbolicExecutionTimeout: timeout,
	}
}

var _ model.Model = (*Model)(nil)

// ID returns the unique ID of this model.
func (m *Model) ID() (id string) {
	return "symflower" + provider.ProviderModelSeparator + "symbolic-execution"
}

// MetaInformation returns the meta information of a model.
func (m *Model) MetaInformation() (metaInformation *model.MetaInformation) {
	return nil
}

var _ model.CapabilityWriteTests = (*Model)(nil)

// generateTestsForFile generates test files for the given implementation file in a repository.
func (m *Model) WriteTests(ctx model.Context) (assessment metrics.Assessments, err error) {
	ctxWithTimeout, cancel := context.WithTimeout(context.Background(), m.symbolicExecutionTimeout)
	defer cancel()

	start := time.Now()

	output, err := util.CommandWithResult(ctxWithTimeout, ctx.Logger, &util.Command{
		Command: []string{
			tools.SymflowerPath, "unit-tests",
			"--code-disable-fetch-dependencies",
			"--workspace", ctx.RepositoryPath,
			ctx.FilePath,
		},

		Directory: ctx.RepositoryPath,
	})
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	processingTime := uint64(time.Since(start).Milliseconds())

	characterCount, err := countCharactersOfGeneratedFiles(ctx.RepositoryPath, extractGeneratedFilePaths(output))
	if err != nil {
		return nil, err
	}

	return metrics.Assessments{ // Symflower always generates just source code when it does not fail, so no need to check the assessment properties.
		metrics.AssessmentKeyProcessingTime:                     processingTime,
		metrics.AssessmentKeyGenerateTestsForFileCharacterCount: characterCount,
		metrics.AssessmentKeyResponseCharacterCount:             characterCount,
		metrics.AssessmentKeyResponseNoExcess:                   1,
		metrics.AssessmentKeyResponseWithCode:                   1,
	}, nil
}

// unitTestFilePathsRe defines the regex to search for generated unit test file paths in a log output.
var unitTestFilePathsRe = regexp.MustCompile(`(?m): generated unit test file (.+)$`)

func extractGeneratedFilePaths(output string) (filePaths []string) {
	matches := unitTestFilePathsRe.FindAllStringSubmatch(output, -1)

	for _, match := range matches {
		filePaths = append(filePaths, match[1])
	}

	return filePaths
}

func countCharactersOfGeneratedFiles(repositoryPath string, filePaths []string) (count uint64, err error) {
	for _, filePath := range filePaths {
		fileContent, err := os.ReadFile(filepath.Join(repositoryPath, filePath))
		if err != nil {
			return 0, pkgerrors.WithStack(err)
		}

		count += uint64(len(string(fileContent)))
	}

	return count, nil
}
