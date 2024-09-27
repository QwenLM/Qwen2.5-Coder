package prompt

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
)

func TestParseResponse(t *testing.T) {
	type testCase struct {
		Name string

		Response string

		ExpectedAssessment metrics.Assessments
		ExpectedCode       string
		ExpectedError      bool
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualAssessment, actualCode, err := ParseResponse(tc.Response)
			if !tc.ExpectedError {
				assert.NoError(t, err)
			} else {
				assert.Error(t, err)
			}

			metricstesting.AssertAssessmentsEqual(t, tc.ExpectedAssessment, actualAssessment)
			assert.Equal(t, strings.TrimSpace(tc.ExpectedCode), actualCode)
		})
	}

	code := bytesutil.StringTrimIndentations(`
		package main

		import "testing"

		func TestPlain(t *testing.T) {
			plain()
		}
	`)

	validate(t, &testCase{
		Name: "Only Code",

		Response: code,

		ExpectedAssessment: metrics.Assessments{
			// If there are no code fences, we currently cannot determine what is code and what is (excessive) text.
			metrics.AssessmentKeyResponseNoExcess: 0,
			metrics.AssessmentKeyResponseWithCode: 0,
		},
		ExpectedCode: code,
	})

	validate(t, &testCase{
		Name: "Unclosed Tags",

		Response: "```\n" + code,

		ExpectedAssessment: metrics.Assessments{
			// If there are incorrect code fences, we currently cannot determine what is code and what is (excessive) text.
			metrics.AssessmentKeyResponseNoExcess: 0,
			metrics.AssessmentKeyResponseWithCode: 0,
		},
		ExpectedCode: code,
	})

	validate(t, &testCase{
		Name: "Expected error on empty response",

		Response: "",

		ExpectedAssessment: metrics.Assessments{},
		ExpectedCode:       "",
		ExpectedError:      true,
	})

	t.Run("Formatted Code", func(t *testing.T) {
		validate(t, &testCase{
			Name: "No Prose",

			Response: "```\n" + code + "\n```\n",

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})

		validate(t, &testCase{
			Name: "No Final Newline",

			Response: "```\n" + code + "\n```",

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})

		t.Run("Prose", func(t *testing.T) {
			validate(t, &testCase{
				Name: "After Newline",

				Response: "Some text...\n\n```\n" + code + "\n```\n\nSome more text...",

				ExpectedAssessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 0,
					metrics.AssessmentKeyResponseWithCode: 1,
				},
				ExpectedCode: code,
			})
			validate(t, &testCase{
				Name: "No Newline",

				Response: "Some text...\n\n```\n" + code + "\n```Some more text...",

				ExpectedAssessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 0,
					metrics.AssessmentKeyResponseWithCode: 1,
				},
				ExpectedCode: code,
			})
		})

		validate(t, &testCase{
			Name: "Language Specified",

			Response: "```go\n" + code + "\n```\n",

			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})

		validate(t, &testCase{
			Name: "Whitespace before Code Block Guards",

			Response: " ```\n" + code + "\n\t```\n",
			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})

		validate(t, &testCase{
			Name: "Whitespace after Code Block Guards",

			Response: "``` \n" + code + "\n``` ",
			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})

		validate(t, &testCase{
			Name: "Duplicated Code Block Guards",

			Response: "```\n```\n" + code + "\n```\n```\n",
			ExpectedAssessment: metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
				metrics.AssessmentKeyResponseWithCode: 1,
			},
			ExpectedCode: code,
		})
	})
}
