package ruby

import (
	"context"
	"path/filepath"
	"regexp"
	"strings"

	"os"
	"strconv"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
	"github.com/symflower/eval-dev-quality/util"
)

// Language holds a Ruby language to evaluate a repository.
type Language struct{}

func init() {
	language.Register(&Language{})
}

var _ language.Language = (*Language)(nil)

// ID returns the unique ID of this language.
func (l *Language) ID() (id string) {
	return "ruby"
}

// Name is the prose name of this language.
func (l *Language) Name() (id string) {
	return "Ruby"
}

// Files returns a list of relative file paths of the repository that should be evaluated.
func (l *Language) Files(logger *log.Logger, repositoryPath string) (filePaths []string, err error) {
	return language.Files(logger, l, repositoryPath)
}

// ImportPath returns the import path of the given source file.
func (l *Language) ImportPath(projectRootPath string, filePath string) (importPath string) {
	return "../lib/" + strings.TrimSuffix(filepath.Base(filePath), l.DefaultFileExtension())
}

// TestFilePath returns the file path of a test file given the corresponding file path of the test's source file.
func (l *Language) TestFilePath(projectRootPath string, filePath string) (testFilePath string) {
	filePath = strings.ReplaceAll(filePath, "lib", "test")

	return strings.TrimSuffix(filePath, l.DefaultFileExtension()) + l.DefaultTestFileSuffix()
}

// TestFramework returns the human-readable name of the test framework that should be used.
func (l *Language) TestFramework() (testFramework string) {
	return "Minitest"
}

// DefaultFileExtension returns the default file extension.
func (l *Language) DefaultFileExtension() string {
	return ".rb"
}

// DefaultTestFileSuffix returns the default test file suffix.
func (l *Language) DefaultTestFileSuffix() string {
	return "_test.rb"
}

// ExecuteTests invokes the language specific testing on the given repository.
func (l *Language) ExecuteTests(logger *log.Logger, repositoryPath string) (testResult *language.TestResult, problems []error, err error) {
	ctx, cancel := context.WithTimeout(context.Background(), language.DefaultExecutionTimeout)
	defer cancel()

	if err := injectCoverageTracking(repositoryPath); err != nil {
		return nil, nil, err
	}

	coverageFilePath := filepath.Join(repositoryPath, "coverage.json")
	commandOutput, err := util.CommandWithResult(ctx, logger, &util.Command{
		Command: []string{
			tools.SymflowerPath, "test",
			"--language", "ruby",
			"--workspace", repositoryPath,
			"--coverage-file", coverageFilePath,
		},

		Directory: repositoryPath,
	})
	if err != nil {
		return nil, nil, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput)
	}

	testsTotal, testsPass, err := parseSymflowerTestOutput(commandOutput)
	if err != nil {
		return nil, nil, err
	}

	testResult = &language.TestResult{
		TestsTotal: uint(testsTotal),
		TestsPass:  uint(testsPass),
	}

	testResult.Coverage, err = language.CoverageObjectCountOfFile(logger, coverageFilePath)
	if err != nil {
		return nil, nil, pkgerrors.WithMessage(pkgerrors.WithStack(err), commandOutput)
	}

	return testResult, problems, nil
}

var languageRakeTestSummaryRE = regexp.MustCompile(`(\d+) runs, \d+ assertions, (\d+) failures, (\d+) errors, (\d+) skips`)

func parseSymflowerTestOutput(data string) (testsTotal int, testsPass int, err error) {
	testSummary := languageRakeTestSummaryRE.FindStringSubmatch(data)
	if len(testSummary) == 0 {
		return 0, 0, pkgerrors.WithMessage(pkgerrors.WithStack(language.ErrCannotParseTestSummary), data)
	}

	testsTotal, err = strconv.Atoi(testSummary[1])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}
	testsFailure, err := strconv.Atoi(testSummary[2])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}
	testsErrors, err := strconv.Atoi(testSummary[3])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}
	testsSkips, err := strconv.Atoi(testSummary[4])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}

	// The "assertions" cannot be used to calculate the passing tests, cause they also include failed assertions.
	return testsTotal, testsTotal - testsFailure - testsErrors - testsSkips, nil
}

// injectCoverageTracking injects our custom coverage tracking logic into a ruby project.
func injectCoverageTracking(repositoryPath string) error {
	// Add relative import to our special test initialization to every test file so we can track coverage.
	testDirectoryEntries, err := os.ReadDir(filepath.Join(repositoryPath, "test"))
	if err != nil {
		return pkgerrors.WithMessage(err, "reading test directory")
	}
	for _, entry := range testDirectoryEntries {
		if entry.IsDir() {
			continue
		}
		filePath := filepath.Join(repositoryPath, "test", entry.Name())

		fileContent, err := os.ReadFile(filePath)
		if err != nil {
			return pkgerrors.WithStack(err)
		}

		// Only add the import if it does not exist already.
		if strings.Contains(string(fileContent), "require_relative \"test_init\"") {
			continue
		}
		if err := os.WriteFile(filePath, append([]byte("require_relative \"test_init\"\n"), fileContent...), 0644); err != nil {
			return pkgerrors.WithStack(err)
		}
	}
	// Write the special init file to setup coverage tracking. In case it exists already, it will just be re-written.
	if err := os.WriteFile(filepath.Join(repositoryPath, "test", "test_init.rb"), []byte(bytesutil.StringTrimIndentations(`
		# Set up coverage.
		require "simplecov"
		SimpleCov.start do
			add_filter "/test/" # Exclude files in test folder.
		end
		require "simplecov_json_formatter"
		SimpleCov.formatter = SimpleCov::Formatter::JSONFormatter

		# Set up minitest.
		require "minitest/autorun"
	`)), 0644); err != nil {
		return pkgerrors.WithMessage(err, "writing ruby test init file")
	}

	return nil
}

// mistakesErrorRe defines the structure of the error messages when running tests.
var mistakesErrorRe = regexp.MustCompile(`\d\) Error:\n\w+#\w+:\n(.*)\n\s*(.*)`)

// mistakesSyntaxErrorRe defines the structure of syntax errors.
var mistakesSyntaxErrorRe = regexp.MustCompile(`.* \(SyntaxError\)`)

// Mistakes builds a Ruby repository and returns the list of mistakes found.
func (l *Language) Mistakes(logger *log.Logger, repositoryPath string) (mistakes []string, err error) {
	if err := injectCoverageTracking(repositoryPath); err != nil {
		return nil, err
	}

	output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			tools.SymflowerPath, "test",
			"--language", "ruby",
			"--workspace", repositoryPath,
		},

		Directory: repositoryPath,
	})
	if output == "" {
		return nil, pkgerrors.Wrap(err, "no output to extract errors from")
	}

	return extractMistakes(output), nil
}

// extractMistakes returns a list of errors found in raw output.
func extractMistakes(rawMistakes string) (mistakes []string) {
	rawMistakes = strings.ReplaceAll(rawMistakes, "\r", "") // Remove Windows new-line returns.

	for _, result := range mistakesErrorRe.FindAllStringSubmatch(rawMistakes, -1) {
		if !strings.Contains(result[2], "_test.rb") {
			return []string{result[1] + " : " + result[2]}
		}
	}

	// If no errors match the regexp then we check for syntax errors.
	for _, result := range mistakesSyntaxErrorRe.FindAllStringSubmatch(rawMistakes, -1) {
		mistakes = append(mistakes, result[0])
	}

	return mistakes
}
