package language

import (
	"errors"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/log"
)

var (
	// ErrCannotParseTestSummary indicates that the test summary cannot be parsed.
	ErrCannotParseTestSummary = errors.New("cannot parse test summary")
)

// DefaultExecutionTimeout defines the timeout for an execution.
// WORKAROUND For now we define the timeout as a global variable but it should eventually be moved to the "symflower test" command.
var DefaultExecutionTimeout = 5 * time.Minute

// Language defines a language to evaluate a repository.
type Language interface {
	// ID returns the unique ID of this language.
	ID() (id string)
	// Name is the prose name of this language.
	Name() (id string)

	// Files returns a list of relative file paths of the repository that should be evaluated.
	Files(logger *log.Logger, repositoryPath string) (filePaths []string, err error)
	// ImportPath returns the import path of the given source file.
	ImportPath(projectRootPath string, filePath string) (importPath string)
	// TestFilePath returns the file path of a test file given the corresponding file path of the test's source file.
	TestFilePath(projectRootPath string, filePath string) (testFilePath string)
	// TestFramework returns the human-readable name of the test framework that should be used.
	TestFramework() (testFramework string)

	// DefaultFileExtension returns the default file extension of the implemented language.
	DefaultFileExtension() string
	// DefaultTestFileSuffix returns the default test file suffix of the implemented language.
	DefaultTestFileSuffix() string

	// ExecuteTests invokes the language specific testing on the given repository.
	ExecuteTests(logger *log.Logger, repositoryPath string) (testResult *TestResult, problems []error, err error)
	// Mistakes builds a repository and returns the list of mistakes found.
	Mistakes(logger *log.Logger, repositoryPath string) (mistakes []string, err error)
}

// Languages holds a register of all languages.
var Languages = map[string]Language{}

// LanguageByFileExtension holds the language for a default file extension.
var LanguageByFileExtension = map[string]Language{}

// Register adds a language to the common language list.
func Register(language Language) {
	id := language.ID()
	if _, ok := Languages[id]; ok {
		panic(pkgerrors.WithMessage(pkgerrors.New("language was already registered"), id))
	}
	if _, ok := LanguageByFileExtension[language.DefaultFileExtension()]; ok {
		panic(pkgerrors.WithMessage(pkgerrors.New("language file extension was already registered"), id))
	}

	Languages[id] = language
	LanguageByFileExtension[language.DefaultFileExtension()] = language
}

// RepositoriesForLanguage returns the relative repository paths for a language.
func RepositoriesForLanguage(language Language, testdataPath string) (relativeRepositoryPaths []string, err error) {
	languagePath := filepath.Join(testdataPath, language.ID())
	languageRepositories, err := os.ReadDir(languagePath)
	if err != nil {
		pkgerrors.WithMessagef(err, "language path %q cannot be accessed", languagePath)
	}

	for _, repository := range languageRepositories {
		if !repository.IsDir() {
			continue
		}
		relativeRepositoryPaths = append(relativeRepositoryPaths, filepath.Join(language.ID(), repository.Name()))
	}

	sort.Strings(relativeRepositoryPaths)

	return relativeRepositoryPaths, nil
}

// Files returns a list of relative file paths of the repository that should be evaluated.
func Files(logger *log.Logger, language Language, repositoryPath string) (filePaths []string, err error) {
	repositoryPath, err = filepath.Abs(repositoryPath)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	fs, err := osutil.FilesRecursive(repositoryPath)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	repositoryPath = repositoryPath + string(os.PathSeparator)
	for _, f := range fs {
		if !strings.HasSuffix(f, language.DefaultFileExtension()) {
			continue
		}

		filePaths = append(filePaths, strings.TrimPrefix(f, repositoryPath))
	}

	return filePaths, nil
}

// TestResult holds the result of running tests.
type TestResult struct {
	TestsTotal uint
	TestsPass  uint

	Coverage uint64
}

// PassingTestsPercentage returns the percentage of passing tests.
func (tr *TestResult) PassingTestsPercentage() (percentage uint) {
	return tr.TestsPass / tr.TestsTotal * 100
}
