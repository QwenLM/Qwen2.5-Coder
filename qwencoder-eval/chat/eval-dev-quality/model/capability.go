package model

import "github.com/symflower/eval-dev-quality/evaluate/metrics"

// CapabilityWriteTests defines the capability of a model to generate tests.
type CapabilityWriteTests interface {
	// WriteTests generates test files for the given implementation file in a repository.
	WriteTests(ctx Context) (assessments metrics.Assessments, err error)
}

// CapabilityRepairCode defines the capability of a model to repair code.
type CapabilityRepairCode interface {
	// RepairCode queries the model to repair a source code with compilation error.
	RepairCode(ctx Context) (assessments metrics.Assessments, err error)
}

// CapabilityTranspile defines the capability of a model to transpile code.
type CapabilityTranspile interface {
	// Transpile queries the model to transpile source code to another language.
	Transpile(ctx Context) (assessments metrics.Assessments, err error)
}
