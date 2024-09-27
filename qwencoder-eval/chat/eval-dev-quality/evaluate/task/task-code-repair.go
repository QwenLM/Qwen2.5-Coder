package task

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	evaltask "github.com/symflower/eval-dev-quality/task"
)

// TaskCodeRepair holds the code repair task.
type TaskCodeRepair struct {
}

// TaskArgumentsCodeRepair holds extra arguments to be used in a query prompt.
type TaskArgumentsCodeRepair struct {
	// Mistakes holds the list of compilation errors for a package.
	Mistakes []string
}

var _ evaltask.Task = (*TaskCodeRepair)(nil)

// Identifier returns the code repair task identifier.
func (t *TaskCodeRepair) Identifier() evaltask.Identifier {
	return IdentifierCodeRepair
}

// Run performs source code repairing in a repository with compilation errors.
// This task requires the repository to consist of multiple packages, with each containing one faulty implementation file and a corresponding test file.
func (t *TaskCodeRepair) Run(ctx evaltask.Context) (repositoryAssessment map[evaltask.Identifier]metrics.Assessments, problems []error, err error) {
	modelCapability, ok := ctx.Model.(model.CapabilityRepairCode)
	if !ok {
		return nil, nil, pkgerrors.Wrap(evaltask.ErrTaskUnsupportedByModel, fmt.Sprintf("%q does not support %q", ctx.Model.ID(), string(t.Identifier())))
	}

	taskLogger, err := newTaskLogger(ctx, t)
	if err != nil {
		return nil, nil, err
	}
	defer func() {
		taskLogger.finalize(problems)
	}()

	var packagePaths []string
	files, err := os.ReadDir(ctx.Repository.DataPath())
	if err != nil {
		return nil, nil, pkgerrors.WithStack(err)
	}
	for _, file := range files {
		if file.IsDir() && !strings.HasPrefix(file.Name(), ".") { // Ignore hidden directories.
			packagePaths = append(packagePaths, filepath.Join(ctx.Repository.DataPath(), file.Name()))
		}
	}

	modelAssessment := metrics.NewAssessments()
	modelAssessment[metrics.AssessmentKeyFilesExecutedMaximumReachable] = uint64(len(packagePaths))
	for _, packagePath := range packagePaths {
		if err := ctx.Repository.Reset(ctx.Logger); err != nil {
			ctx.Logger.Panicf("ERROR: unable to reset temporary repository path: %s", err)
		}

		sourceFile, mistakes, err := t.unpackCodeRepairPackage(ctx, taskLogger.Logger, packagePath)
		if err != nil {
			return nil, nil, err
		}

		modelContext := model.Context{
			Language: ctx.Language,

			RepositoryPath: packagePath,
			FilePath:       sourceFile,

			Arguments: &TaskArgumentsCodeRepair{
				Mistakes: mistakes,
			},

			Logger: taskLogger.Logger,
		}
		assessments, err := modelCapability.RepairCode(modelContext)
		if err != nil {
			problems = append(problems, pkgerrors.WithMessage(err, sourceFile))

			continue
		}
		if assessments[metrics.AssessmentKeyProcessingTime] == 0 {
			return nil, nil, pkgerrors.Errorf("no model response time measurement present for %q at repository %q", ctx.Model.ID(), ctx.Repository.Name())
		}
		modelAssessment.Add(assessments)
		modelAssessment.Award(metrics.AssessmentKeyResponseNoError)

		testResult, ps, err := ctx.Language.ExecuteTests(taskLogger.Logger, packagePath)
		problems = append(problems, ps...)
		if err != nil {
			problems = append(problems, pkgerrors.WithMessage(err, sourceFile))

			continue
		}
		testsPassing := testResult.TestsPass
		taskLogger.Printf("Executes tests with %d tests passing", testsPassing)
		modelAssessment.Award(metrics.AssessmentKeyFilesExecuted)
		modelAssessment.AwardPoints(metrics.AssessmentKeyTestsPassing, uint64(testsPassing))
	}

	repositoryAssessment = map[evaltask.Identifier]metrics.Assessments{
		IdentifierCodeRepair: modelAssessment,
	}

	return repositoryAssessment, problems, nil
}

// unpackCodeRepairPackage validates a package under test and returns the source file path and the list of compilation errors found.
func (t *TaskCodeRepair) unpackCodeRepairPackage(ctx evaltask.Context, fileLogger *log.Logger, packagePath string) (sourceFilePath string, mistakes []string, err error) {
	mistakes, err = ctx.Language.Mistakes(ctx.Logger, packagePath)
	if err != nil {
		return "", nil, pkgerrors.WithStack(err)
	} else if len(mistakes) == 0 {
		return "", nil, pkgerrors.Errorf("package %q in repository %q must contain source files with compilation errors", packagePath, ctx.Repository.Name())
	}

	sourceFilePath, err = packageSourceFile(fileLogger, packagePath, ctx.Language)
	if err != nil {
		return "", nil, err
	}

	return sourceFilePath, mistakes, nil
}

// validateCodeRepairRepository checks if the repository for the "code-repair" task is well-formed.
func validateCodeRepairRepository(logger *log.Logger, repositoryPath string, language language.Language) (err error) {
	logger.Printf("validating repository %q", repositoryPath)

	packagePaths, err := repositoryOnlyHasPackages(repositoryPath)
	if err != nil {
		return err
	}

	for _, packagePath := range packagePaths {
		sourceFiles, testFiles, err := packagesSourceAndTestFiles(logger, packagePath, language)
		if err != nil {
			return err
		}

		if len(sourceFiles) != 1 {
			return pkgerrors.Errorf("the code repair package %q in repository %q must contain exactly one %s source file, but found %+v", packagePath, repositoryPath, language.Name(), sourceFiles)
		} else if len(testFiles) != 1 {
			return pkgerrors.Errorf("the code repair repository %q must contain exactly one %s test file, but found %+v", repositoryPath, language.Name(), testFiles)
		}
	}

	return nil
}
