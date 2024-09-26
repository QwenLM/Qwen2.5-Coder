package metrics

import "fmt"

// AssessmentCategory represents a categorical ranking of a model based on Assessments.
type AssessmentCategory struct {
	// ID holds a unique identifier.
	ID string
	// Name holds a short name.
	Name string
	// Description holds the description.
	Description string
}

// AllAssessmentCategories holds all assessment categories.
var AllAssessmentCategories []*AssessmentCategory

// registerAssessmentCategory registers a new assessment category.
func registerAssessmentCategory(c AssessmentCategory) *AssessmentCategory {
	for _, category := range AllAssessmentCategories {
		if c.ID == category.ID {
			panic(fmt.Sprintf("duplicated category ID %q", c.ID))
		}
	}

	AllAssessmentCategories = append(AllAssessmentCategories, &c)

	return &c
}

var (
	// AssessmentCategoryUnknown indicates that it is not possible to compute a model's category.
	AssessmentCategoryUnknown = registerAssessmentCategory(AssessmentCategory{
		ID:          "category-unknown",
		Name:        "category unknown",
		Description: "Models in this category could not be categorized.",
	})
	// AssessmentCategoryResponseError indicates that a model has encountered an error trying to produce a response.
	AssessmentCategoryResponseError = registerAssessmentCategory(AssessmentCategory{
		ID:          "response-error",
		Name:        "response error",
		Description: "Models in this category encountered an error.",
	})
	// AssessmentCategoryResponseNoCode indicates that a model's response did not contain any source code.
	AssessmentCategoryResponseNoCode = registerAssessmentCategory(AssessmentCategory{
		ID:          "response-no-code",
		Name:        "no code",
		Description: "Models in this category produced no code.",
	})
	// AssessmentCategoryCodeInvalid indicates that a model's generated code produced an error when executed.
	AssessmentCategoryCodeInvalid = registerAssessmentCategory(AssessmentCategory{
		ID:          "code-invalid",
		Name:        "invalid code",
		Description: "Models in this category produced invalid code.",
	})
	// AssessmentCategoryCodeExecuted indicates that a model's generated code could be executed without an error.
	AssessmentCategoryCodeExecuted = registerAssessmentCategory(AssessmentCategory{
		ID:          "code-executed",
		Name:        "executable code",
		Description: "Models in this category produced executable code.",
	})
	// AssessmentCategoryCodeCoverageStatementReached indicates that a model's generated code reached 100% statement coverage.
	AssessmentCategoryCodeCoverageStatementReached = registerAssessmentCategory(AssessmentCategory{
		ID:          "code-coverage-statement",
		Name:        "statement coverage reached",
		Description: "Models in this category produced code that reached full statement coverage.",
	})
	// AssessmentCategoryCodeNoExcess indicates that a model's response did not contain more content than requested.
	AssessmentCategoryCodeNoExcess = registerAssessmentCategory(AssessmentCategory{
		ID:          "code-no-excess",
		Name:        "no excess response",
		Description: "Models in this category did not respond with more content than requested.",
	})
)

// Category infers a categorical ranking of a model based on assessment values.
// A models overall category corresponds to the criterion where the model was consistently able to receive "total" amount of points. I.e. if there were 3 tasks in total and a model was able to produce executing code for all tasks, but only in one case the coverage goal was reached, then the category is only "CodeExecuted" because the coverage goal was not reached consistently.
// The returned category is never "nil".
func (a Assessments) Category(totalTasks uint64) *AssessmentCategory {
	if totalTasks == 0 {
		return AssessmentCategoryUnknown
	}

	switch {
	case a[AssessmentKeyResponseNoError] != totalTasks*multiplierPerAssessment[AssessmentKeyResponseNoError]:
		return AssessmentCategoryResponseError
	case a[AssessmentKeyResponseWithCode] != totalTasks*multiplierPerAssessment[AssessmentKeyResponseWithCode] && a[AssessmentKeyFilesExecuted] != totalTasks*multiplierPerAssessment[AssessmentKeyFilesExecuted]: // TODO We cannot always detect yet if a model response contains source code, so ensure we don't categorize into "no code" if the code actually ran successfully all the time. https://github.com/symflower/eval-dev-quality/issues/43
		return AssessmentCategoryResponseNoCode
	case a[AssessmentKeyFilesExecuted] != totalTasks*multiplierPerAssessment[AssessmentKeyFilesExecuted]:
		return AssessmentCategoryCodeInvalid
	case a[AssessmentKeyCoverage] != totalTasks*multiplierPerAssessment[AssessmentKeyCoverage]:
		return AssessmentCategoryCodeExecuted
	case a[AssessmentKeyResponseNoExcess] != totalTasks*multiplierPerAssessment[AssessmentKeyResponseNoExcess]:
		return AssessmentCategoryCodeCoverageStatementReached
	default:
		return AssessmentCategoryCodeNoExcess
	}
}
