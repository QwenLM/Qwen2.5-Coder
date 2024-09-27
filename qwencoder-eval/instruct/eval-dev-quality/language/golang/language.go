package golang

import (
	"context"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	pkgerrors "github.com/pkg/errors"

	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
	"github.com/symflower/eval-dev-quality/util"
)

// Language holds a Go language to evaluate a repository.
type Language struct{}

func init() {
	language.Register(&Language{})
}

var _ language.Language = (*Language)(nil)

// ID returns the unique ID of this language.
func (l *Language) ID() (id string) {
	return "golang"
}

// Name is the prose name of this language.
func (l *Language) Name() (id string) {
	return "Go"
}

// Files returns a list of relative file paths of the repository that should be evaluated.
func (l *Language) Files(logger *log.Logger, repositoryPath string) (filePaths []string, err error) {
	return language.Files(logger, l, repositoryPath)
}

// ImportPath returns the import path of the given source file.
func (l *Language) ImportPath(projectRootPath string, filePath string) (importPath string) {
	return filepath.Join(filepath.Base(projectRootPath), filepath.Dir(filePath))
}

// TestFilePath returns the file path of a test file given the corresponding file path of the test's source file.
func (l *Language) TestFilePath(projectRootPath string, filePath string) (testFilePath string) {
	return strings.TrimSuffix(filePath, l.DefaultFileExtension()) + l.DefaultTestFileSuffix()
}

// TestFramework returns the human-readable name of the test framework that should be used.
func (l *Language) TestFramework() (testFramework string) {
	return ""
}

// DefaultFileExtension returns the default file extension.
func (l *Language) DefaultFileExtension() string {
	return ".go"
}

// DefaultTestFileSuffix returns the default test file suffix.
func (l *Language) DefaultTestFileSuffix() string {
	return "_test.go"
}

// ExecuteTests invokes the language specific testing on the given repository.
func (l *Language) ExecuteTests(logger *log.Logger, repositoryPath string) (testResult *language.TestResult, problems []error, err error) {
	commandOutput, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			"go",
			"mod",
			"tidy",
		},

		Directory: repositoryPath,
	})
	if err != nil {
		return nil, nil, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput)
	}

	ctx, cancel := context.WithTimeout(context.Background(), language.DefaultExecutionTimeout)
	defer cancel()
	coverageFilePath := filepath.Join(repositoryPath, "coverage.json")
	commandOutput, err = util.CommandWithResult(ctx, logger, &util.Command{
		Command: []string{
			tools.SymflowerPath, "test",
			"--language", "golang",
			"--workspace", repositoryPath,
			"--coverage-file", coverageFilePath,
		},

		Directory: repositoryPath,
	})

	testsTotal, testsPass, e := parseSymflowerTestOutput(commandOutput)
	if e != nil {
		problems = append(problems, pkgerrors.WithMessage(pkgerrors.WithStack(e), commandOutput))
	}
	// If there are test failures, then this is just a soft error since we still are able to receive coverage data.
	if err != nil {
		if testsTotal-testsPass > 0 {
			problems = append(problems, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput))
		} else {
			return nil, nil, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput)
		}
	}

	testResult = &language.TestResult{
		TestsTotal: uint(testsTotal),
		TestsPass:  uint(testsPass),
	}
	testResult.Coverage, err = language.CoverageObjectCountOfFile(logger, coverageFilePath)
	if err != nil {
		return testResult, problems, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput)
	}

	return testResult, problems, nil
}

var languageGoTestSummaryRE = regexp.MustCompile(`DONE (\d+) tests(?:, (\d+) failure)?`)

func parseSymflowerTestOutput(data string) (testsTotal int, testsPass int, err error) {
	testSummary := languageGoTestSummaryRE.FindStringSubmatch(data)
	if len(testSummary) == 0 {
		return 0, 0, pkgerrors.WithMessage(pkgerrors.WithStack(language.ErrCannotParseTestSummary), data)
	}

	testsTotal, err = strconv.Atoi(testSummary[1])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}

	var testsFail int
	if len(testSummary[2]) > 0 {
		if testsFail, err = strconv.Atoi(testSummary[2]); err != nil {
			return 0, 0, pkgerrors.WithStack(err)
		}
	}
	testsPass = testsTotal - testsFail

	return testsTotal, testsPass, nil
}

// Mistakes builds a Go repository and returns the list of mistakes found.
func (l *Language) Mistakes(logger *log.Logger, repositoryPath string) (mistakes []string, err error) {
	output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			"go",
			"build",
		},

		Directory: repositoryPath,
	})
	if err != nil {
		if output != "" {
			return extractMistakes(output), nil
		}

		return nil, pkgerrors.Wrap(err, "no output to extract errors from")
	}

	return nil, nil
}

// mistakesRe defines the structure of a Go compiler error.
var mistakesRe = regexp.MustCompile(`(?m)^.*\.go:\d+:\d+:.*$`)

func extractMistakes(rawMistakes string) (mistakes []string) {
	return mistakesRe.FindAllString(rawMistakes, -1)
}
