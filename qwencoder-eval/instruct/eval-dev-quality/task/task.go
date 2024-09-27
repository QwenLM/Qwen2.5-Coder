package task

import (
	"errors"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
)

var (
	// ErrTaskUnknown indicates that a task is unknown.
	ErrTaskUnknown = errors.New("task unknown")
	// ErrTaskUnsupportedByModel indicates that the model does not support the task.
	ErrTaskUnsupportedByModel = errors.New("model does not support task")
)

// Identifier holds the identifier of a task.
type Identifier string

// Context holds the data need by a task to be run.
type Context struct {
	// Language holds the language for which the task should be evaluated.
	Language language.Language
	// Repository holds the repository which should be evaluated.
	Repository Repository
	// Model holds the model which the task should be evaluated.
	Model model.Model

	// ResultPath holds the directory path where results should be written to.
	ResultPath string

	// Logger holds the logger for this tasks.
	Logger *log.Logger
}

// Task defines an evaluation task.
type Task interface {
	// Identifier returns the task identifier.
	Identifier() (identifier Identifier)

	// Run runs a task in a given repository.
	Run(ctx Context) (assessments map[Identifier]metrics.Assessments, problems []error, err error)
}

// Repository defines a repository to be evaluated.
type Repository interface {
	// Name holds the name of the repository.
	Name() (name string)
	// DataPath holds the absolute path to the repository.
	DataPath() (dataPath string)

	// SupportedTasks returns the list of task identifiers the repository supports.
	SupportedTasks() (tasks []Identifier)

	// Validate checks it the repository is well-formed.
	Validate(logger *log.Logger, language language.Language) (err error)

	// Reset resets the repository to its initial state.
	Reset(logger *log.Logger) (err error)
}
