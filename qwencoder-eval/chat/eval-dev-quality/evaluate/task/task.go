package task

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	evaltask "github.com/symflower/eval-dev-quality/task"
)

var (
	// AllIdentifiers holds all available task identifiers.
	AllIdentifiers []evaltask.Identifier
	// LookupIdentifier holds a map of all available task identifiers.
	LookupIdentifier = map[evaltask.Identifier]bool{}
)

// registerIdentifier registers the given identifier and makes it available.
func registerIdentifier(name string) (identifier evaltask.Identifier) {
	identifier = evaltask.Identifier(name)
	AllIdentifiers = append(AllIdentifiers, identifier)

	if _, ok := LookupIdentifier[identifier]; ok {
		panic(fmt.Sprintf("task identifier already registered: %s", identifier))
	}
	LookupIdentifier[identifier] = true

	return identifier
}

var (
	// IdentifierWriteTests holds the identifier for the "write test" task.
	IdentifierWriteTests = registerIdentifier("write-tests")
	// IdentifierWriteTestsSymflowerFix holds the identifier for the "write test" task with the "symflower fix" applied.
	IdentifierWriteTestsSymflowerFix = registerIdentifier("write-tests-symflower-fix")
	// IdentifierCodeRepair holds the identifier for the "code repair" task.
	IdentifierCodeRepair = registerIdentifier("code-repair")
	// IdentifierTranspile holds the identifier for the "transpile" task.
	IdentifierTranspile = registerIdentifier("transpile")
	// IdentifierTranspileSymflowerFix holds the identifier for the "transpile" task with the "symflower fix" applied.
	IdentifierTranspileSymflowerFix = registerIdentifier("transpile-symflower-fix")
)

// TaskForIdentifier returns a task based on the task identifier.
func TaskForIdentifier(taskIdentifier evaltask.Identifier) (task evaltask.Task, err error) {
	switch taskIdentifier {
	case IdentifierWriteTests:
		return &TaskWriteTests{}, nil
	case IdentifierCodeRepair:
		return &TaskCodeRepair{}, nil
	case IdentifierTranspile:
		return &TaskTranspile{}, nil
	default:
		return nil, pkgerrors.Wrap(evaltask.ErrTaskUnknown, string(taskIdentifier))
	}
}

// taskLogger holds common logging functionality.
type taskLogger struct {
	*log.Logger

	ctx  evaltask.Context
	task evaltask.Task
}

// newTaskLogger initializes the logging.
func newTaskLogger(ctx evaltask.Context, task evaltask.Task) (logging *taskLogger, err error) {
	logging = &taskLogger{
		ctx:  ctx,
		task: task,
	}

	logging.Logger = ctx.Logger
	logging.Logger.Printf("Evaluating model %q on task %q using language %q and repository %q", ctx.Model.ID(), task.Identifier(), ctx.Language.ID(), ctx.Repository.Name())

	return logging, nil
}

// finalizeLogging finalizes the logging.
func (t *taskLogger) finalize(problems []error) {
	t.Logger.Printf("Evaluated model %q on task %q using language %q and repository %q: encountered %d problems: %+v", t.ctx.Model.ID(), t.task.Identifier(), t.ctx.Language.ID(), t.ctx.Repository.Name(), len(problems), problems)
}

// packageSourceFile returns the source file of a package.
func packageSourceFile(log *log.Logger, packagePath string, language language.Language) (sourceFilePath string, err error) {
	filePaths, err := language.Files(log, packagePath)
	if err != nil {
		return "", pkgerrors.WithStack(err)
	}

	for _, file := range filePaths {
		if strings.HasSuffix(file, language.DefaultTestFileSuffix()) {
			continue
		} else if filepath.Ext(file) == language.DefaultFileExtension() { // We can assume there is only one source file because the package structure was previously verified.
			return file, nil
		}
	}

	return "", pkgerrors.WithStack(pkgerrors.Errorf("could not find any %s source file in package %q", language.Name(), packagePath))
}

// repositoryOnlyHasPackages checks if a repository only has packages and returns all package paths.
func repositoryOnlyHasPackages(repositoryPath string) (packagePaths []string, err error) {
	files, err := os.ReadDir(repositoryPath)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	var otherFiles []string
	for _, file := range files {
		if file.Name() == "repository.json" {
			continue
		} else if file.Name() == ".git" || file.Name() == "target" { // Do not validate Git or Maven directories.
			continue
		} else if file.IsDir() {
			packagePaths = append(packagePaths, filepath.Join(repositoryPath, file.Name()))
		} else {
			otherFiles = append(otherFiles, file.Name())
		}
	}

	if len(otherFiles) > 0 {
		return nil, pkgerrors.Errorf("the code repair repository %q must contain only packages, but found %+v", repositoryPath, otherFiles)
	}

	return packagePaths, nil
}

// packagesSourceAndTestFiles returns a list of all source and test relative file paths of a package.
func packagesSourceAndTestFiles(logger *log.Logger, packagePath string, language language.Language) (sourceFilePaths []string, testFilePaths []string, err error) {
	files, err := language.Files(logger, packagePath)
	if err != nil {
		return nil, nil, pkgerrors.WithStack(err)
	}

	for _, file := range files {
		if strings.HasSuffix(file, "_init.rb") { // Exclude our custom Ruby test initialization.
			continue
		}

		if strings.HasSuffix(file, language.DefaultTestFileSuffix()) {
			testFilePaths = append(testFilePaths, file)
		} else if strings.HasSuffix(file, language.DefaultFileExtension()) {
			sourceFilePaths = append(sourceFilePaths, file)
		}
	}

	return sourceFilePaths, testFilePaths, nil
}
