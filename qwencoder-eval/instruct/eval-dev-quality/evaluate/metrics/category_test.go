package metrics

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAssessmentsCategory(t *testing.T) {
	type testCase struct {
		Name string

		Assessments Assessments
		Total       uint64

		ExpectedAssessmentCategory *AssessmentCategory
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualAssessmentCategory := tc.Assessments.Category(tc.Total)

			assert.Equal(t, tc.ExpectedAssessmentCategory, actualAssessmentCategory)
		})
	}

	validate(t, &testCase{
		Name: "Unknown",

		Assessments: NewAssessments(),
		Total:       0,

		ExpectedAssessmentCategory: AssessmentCategoryUnknown,
	})

	validate(t, &testCase{
		Name: "No Points",

		Assessments: NewAssessments(),
		Total:       1,

		ExpectedAssessmentCategory: AssessmentCategoryResponseError,
	})

	validate(t, &testCase{
		Name: "No Response Error",

		Assessments: Assessments{
			AssessmentKeyResponseNoError: 1,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryResponseNoCode,
	})

	validate(t, &testCase{
		Name: "Contains Code",

		Assessments: Assessments{
			AssessmentKeyResponseNoError:  1,
			AssessmentKeyResponseWithCode: 1,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryCodeInvalid,
	})

	validate(t, &testCase{
		Name: "Code not Detected but Executes", // TODO We cannot always detect yet if a model response contains source code, so ensure we don't categorize into "no code" if the code actually ran successfully. https://github.com/symflower/eval-dev-quality/issues/43

		Assessments: Assessments{
			AssessmentKeyResponseNoError: 1,
			AssessmentKeyFilesExecuted:   1,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryCodeExecuted,
	})

	validate(t, &testCase{
		Name: "Executes",

		Assessments: Assessments{
			AssessmentKeyResponseNoError:  1,
			AssessmentKeyResponseWithCode: 1,
			AssessmentKeyFilesExecuted:    1,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryCodeExecuted,
	})

	validate(t, &testCase{
		Name: "Full Statement Coverage",

		Assessments: Assessments{
			AssessmentKeyResponseNoError:  1,
			AssessmentKeyResponseWithCode: 1,
			AssessmentKeyFilesExecuted:    1,
			AssessmentKeyCoverage:         10,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryCodeCoverageStatementReached,
	})

	validate(t, &testCase{
		Name: "No Excess",

		Assessments: Assessments{
			AssessmentKeyResponseNoError:  1,
			AssessmentKeyResponseWithCode: 1,
			AssessmentKeyFilesExecuted:    1,
			AssessmentKeyCoverage:         10,
			AssessmentKeyResponseNoExcess: 1,
		},
		Total: 1,

		ExpectedAssessmentCategory: AssessmentCategoryCodeNoExcess,
	})

	validate(t, &testCase{
		Name: "Inconsistent",

		Assessments: Assessments{
			AssessmentKeyResponseNoError:  2,
			AssessmentKeyResponseWithCode: 2,
			AssessmentKeyFilesExecuted:    2,
			AssessmentKeyCoverage:         1,
			AssessmentKeyResponseNoExcess: 0,
		},
		Total: 2,

		ExpectedAssessmentCategory: AssessmentCategoryCodeExecuted,
	})
}
