package java

import (
	"context"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil"
	"golang.org/x/exp/maps"

	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/tools"
	"github.com/symflower/eval-dev-quality/util"
)

// Language holds a Java language to evaluate a repository.
type Language struct{}

func init() {
	language.Register(&Language{})
}

var _ language.Language = (*Language)(nil)

// ID returns the unique ID of this language.
func (l *Language) ID() (id string) {
	return "java"
}

// Name is the prose name of this language.
func (l *Language) Name() (id string) {
	return "Java"
}

// Files returns a list of relative file paths of the repository that should be evaluated.
func (l *Language) Files(logger *log.Logger, repositoryPath string) (filePaths []string, err error) {
	return language.Files(logger, l, repositoryPath)
}

// ImportPath returns the import path of the given source file.
func (l *Language) ImportPath(projectRootPath string, filePath string) (importPath string) {
	importPath = strings.ReplaceAll(filepath.Dir(filePath), string(os.PathSeparator), ".")

	t := "src.main.java"
	if l := strings.LastIndex(importPath, t); l != -1 {
		return importPath[l+len(t)+1:]
	}

	return importPath
}

// TestFilePath returns the file path of a test file given the corresponding file path of the test's source file.
func (l *Language) TestFilePath(projectRootPath string, filePath string) (testFilePath string) {
	if l := strings.LastIndex(filePath, filepath.Join("src", "main", "java")); l != -1 {
		t := filepath.Join("src", "test", "java")
		filePath = filePath[:l] + t + filePath[l+len(t):]
	}

	return strings.TrimSuffix(filePath, l.DefaultFileExtension()) + l.DefaultTestFileSuffix()
}

// TestFramework returns the human-readable name of the test framework that should be used.
func (l *Language) TestFramework() (testFramework string) {
	return "JUnit 5"
}

// DefaultFileExtension returns the default file extension.
func (l *Language) DefaultFileExtension() string {
	return ".java"
}

// DefaultTestFileSuffix returns the default test file suffix.
func (l *Language) DefaultTestFileSuffix() string {
	return "Test.java"
}

var languageJavaCoverageMatch = regexp.MustCompile(`Total coverage (.+?)%`)

// ExecuteTests invokes the language specific testing on the given repository.
func (l *Language) ExecuteTests(logger *log.Logger, repositoryPath string) (testResult *language.TestResult, problems []error, err error) {
	ctx, cancel := context.WithTimeout(context.Background(), language.DefaultExecutionTimeout)
	defer cancel()
	coverageFilePath := filepath.Join(repositoryPath, "coverage.json")
	commandOutput, err := util.CommandWithResult(ctx, logger, &util.Command{
		Command: []string{
			tools.SymflowerPath, "test",
			"--language", "java",
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

	return testResult, nil, nil
}

var languageMavenTestSummaryRE = regexp.MustCompile(`Tests run: (\d+), Failures: (\d+), Errors: (\d+)`)

func parseSymflowerTestOutput(data string) (testsTotal int, testsPass int, err error) {
	testSummaries := languageMavenTestSummaryRE.FindAllStringSubmatch(data, -1)
	if len(testSummaries) == 0 {
		return 0, 0, pkgerrors.WithMessage(pkgerrors.WithStack(language.ErrCannotParseTestSummary), data)
	}

	testSummary := testSummaries[len(testSummaries)-1]
	testsTotal, err = strconv.Atoi(testSummary[1])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}
	testsFail, err := strconv.Atoi(testSummary[2])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}
	testsError, err := strconv.Atoi(testSummary[3])
	if err != nil {
		return 0, 0, pkgerrors.WithStack(err)
	}

	testsPass = testsTotal - testsFail - testsError

	return testsTotal, testsPass, nil
}

// Mistakes builds a Java repository and returns the list of mistakes found.
func (l *Language) Mistakes(logger *log.Logger, repositoryPath string) (mistakes []string, err error) {
	output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			"mvn",
			"compile",
		},

		Directory: repositoryPath,
	})
	if err != nil {
		if output != "" {
			mistakes := extractMistakes(output)

			// Remove the repository path to make the reported file paths relative.
			for i, mistake := range mistakes {
				mistakes[i], err = convertMavenPathToRelativePath(mistake, repositoryPath)
				if err != nil {
					return nil, pkgerrors.Wrapf(err, "could not convert Maven path in %q to a relative path", mistake)
				}
			}

			return mistakes, nil
		}

		return nil, pkgerrors.Wrap(err, "no output to extract errors from")
	}

	return nil, nil
}

// javaFilePathRe defines the structure of a Java file path.
var javaFilePathRe = regexp.MustCompile(`.*\.java`)

// convertMavenPathToPath converts a Maven file path to a relative operating-system specific file path.
// Maven file paths always use forward slashes independent of the operating system path separator.
func convertMavenPathToRelativePath(mistake string, base string) (relativePath string, err error) {
	filePath := javaFilePathRe.FindString(mistake)
	if filePath == "" {
		return "", pkgerrors.Errorf("cannot extract file path from %q", mistake)
	}

	filePath = strings.ReplaceAll(mistake, "/", string(os.PathSeparator))
	switch {
	case osutil.IsDarwin():
		// MacOS symlinks temporary directories to "/private" which Maven then reports as actual root file system.
		filePath = strings.TrimPrefix(filePath, "/private")
	case osutil.IsWindows():
		// Maven reports file paths with leading slash for Windows.
		filePath = strings.TrimPrefix(filePath, string(os.PathSeparator))
	}

	filePath, err = filepath.Rel(base, filePath)
	if err != nil {
		return "", pkgerrors.WithStack(err)
	}

	return filePath, nil
}

// mistakesRe defines the structure of a Java compiler error.
var mistakesRe = regexp.MustCompile(`(?m)\[ERROR\] (.*\.java:\[\d+,\d+\].*)$`)

func extractMistakes(rawMistakes string) (mistakes []string) {
	uniqueMistake := map[string]bool{}

	rawMistakes = strings.ReplaceAll(rawMistakes, "\r", "") // Remove Windows new-line returns.
	results := mistakesRe.FindAllStringSubmatch(rawMistakes, -1)
	for _, result := range results {
		compileError := result[1]
		if _, ok := uniqueMistake[compileError]; !ok {
			uniqueMistake[compileError] = true
		}
	}

	mistakes = maps.Keys(uniqueMistake)
	sort.Strings(mistakes)

	return mistakes
}
