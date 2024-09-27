package report

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	metricstesting "github.com/symflower/eval-dev-quality/evaluate/metrics/testing"
	evaluatetask "github.com/symflower/eval-dev-quality/evaluate/task"
	"github.com/symflower/eval-dev-quality/language"
	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
	"github.com/symflower/eval-dev-quality/model"
	modeltesting "github.com/symflower/eval-dev-quality/model/testing"
	"github.com/symflower/eval-dev-quality/task"
)

func TestAssessmentPerModelPerLanguagePerRepositoryWalk(t *testing.T) {
	type testCase struct {
		Name string

		Assessments metricstesting.AssessmentTuples

		ExpectedOrder []metrics.Assessments
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			assessmentStore := assessmentTuplesToStore(tc.Assessments)

			assessmentLookup := tc.Assessments.ToMap()
			actualOrder := []metrics.Assessments{}

			assert.NoError(t, assessmentStore.Walk(func(m model.Model, l language.Language, r string, ti task.Identifier, a metrics.Assessments) (err error) {
				actualOrder = append(actualOrder, a)
				metricstesting.AssertAssessmentsEqual(t, assessmentLookup[m][l][r][ti], a)

				return nil
			}))

			if assert.Equal(t, len(tc.ExpectedOrder), len(actualOrder)) {
				for i := range tc.ExpectedOrder {
					metricstesting.AssertAssessmentsEqual(t, tc.ExpectedOrder[i], actualOrder[i])
				}
			}
		})
	}

	validate(t, &testCase{
		Name: "Single Group",

		Assessments: metricstesting.AssessmentTuples{
			&metricstesting.AssessmentTuple{
				Model:          modeltesting.NewMockCapabilityWriteTestsNamed(t, "some-model"),
				Language:       languagetesting.NewMockLanguageNamed(t, "some-language"),
				RepositoryPath: "some-repository",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 1,
				},
			},
		},

		ExpectedOrder: []metrics.Assessments{
			metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 1,
			},
		},
	})

	{

		modelA := modeltesting.NewMockCapabilityWriteTestsNamed(t, "some-model-a")
		modelB := modeltesting.NewMockCapabilityWriteTestsNamed(t, "some-model-b")
		languageA := languagetesting.NewMockLanguageNamed(t, "some-language-a")
		languageB := languagetesting.NewMockLanguageNamed(t, "some-language-b")

		validate(t, &testCase{
			Name: "Multiple Groups",

			Assessments: metricstesting.AssessmentTuples{
				&metricstesting.AssessmentTuple{
					Model:          modelA,
					Language:       languageA,
					RepositoryPath: "some-repository-a",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 1,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelA,
					Language:       languageA,
					RepositoryPath: "some-repository-b",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 2,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelA,
					Language:       languageB,
					RepositoryPath: "some-repository-a",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 3,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelA,
					Language:       languageB,
					RepositoryPath: "some-repository-b",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 4,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelB,
					Language:       languageA,
					RepositoryPath: "some-repository-a",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 5,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelB,
					Language:       languageA,
					RepositoryPath: "some-repository-b",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 6,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelB,
					Language:       languageB,
					RepositoryPath: "some-repository-a",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 7,
					},
				},
				&metricstesting.AssessmentTuple{
					Model:          modelB,
					Language:       languageB,
					RepositoryPath: "some-repository-b",
					Task:           evaluatetask.IdentifierWriteTests,
					Assessment: metrics.Assessments{
						metrics.AssessmentKeyResponseNoExcess: 8,
					},
				},
			},

			ExpectedOrder: []metrics.Assessments{
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 1,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 2,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 3,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 4,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 5,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 6,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 7,
				},
				metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 8,
				},
			},
		})
	}
}

func TestWalkByScore(t *testing.T) {
	type testCase struct {
		Name string

		AssessmentPerModel AssessmentPerModel

		ExpectedModelOrder []string
		ExpectedScoreOrder []uint64
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			require.Equal(t, len(tc.ExpectedModelOrder), len(tc.ExpectedScoreOrder), "expected order needs equal lengths")

			actualModelOrder := make([]string, 0, len(tc.ExpectedModelOrder))
			actualAssessmentOrder := make([]metrics.Assessments, 0, len(tc.ExpectedModelOrder))
			actualScoreOrder := make([]uint64, 0, len(tc.ExpectedScoreOrder))
			assert.NoError(t, tc.AssessmentPerModel.WalkByScore(func(model string, assessment metrics.Assessments, score uint64) (err error) {
				actualModelOrder = append(actualModelOrder, model)
				actualAssessmentOrder = append(actualAssessmentOrder, assessment)
				actualScoreOrder = append(actualScoreOrder, score)

				return nil
			}))

			assert.Equal(t, tc.ExpectedModelOrder, actualModelOrder)
			assert.Equal(t, tc.ExpectedScoreOrder, actualScoreOrder)
			for i, model := range tc.ExpectedModelOrder {
				assert.Equal(t, tc.AssessmentPerModel[model], actualAssessmentOrder[i])
			}
		})
	}

	validate(t, &testCase{
		Name: "No Assessment",

		AssessmentPerModel: AssessmentPerModel{},

		ExpectedModelOrder: []string{},
		ExpectedScoreOrder: []uint64{},
	})

	validate(t, &testCase{
		Name: "Single Assessment",

		AssessmentPerModel: AssessmentPerModel{
			"modelA": metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted: 1,
			},
		},

		ExpectedModelOrder: []string{
			"modelA",
		},
		ExpectedScoreOrder: []uint64{
			1,
		},
	})

	validate(t, &testCase{
		Name: "Multiple Assessments",

		AssessmentPerModel: AssessmentPerModel{
			"modelA": metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted: 1,
			},
			"modelB": metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted: 2,
			},
			"modelC": metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted: 3,
			},
		},

		ExpectedModelOrder: []string{
			"modelA",
			"modelB",
			"modelC",
		},
		ExpectedScoreOrder: []uint64{
			1,
			2,
			3,
		},
	})
}

func TestAssessmentCollapseByModel(t *testing.T) {
	type testCase struct {
		Name string

		Assessments metricstesting.AssessmentTuples

		ExpectedAssessmentPerModel AssessmentPerModel
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			assessmentStore := assessmentTuplesToStore(tc.Assessments)

			actualAssessmentPerModel := assessmentStore.CollapseByModel()

			assert.Equal(t, tc.ExpectedAssessmentPerModel, actualAssessmentPerModel)
		})
	}

	modelA := modeltesting.NewMockCapabilityWriteTestsNamed(t, "some-model-a")
	modelB := modeltesting.NewMockCapabilityWriteTestsNamed(t, "some-model-b")
	languageA := languagetesting.NewMockLanguageNamed(t, "some-language-a")
	languageB := languagetesting.NewMockLanguageNamed(t, "some-language-b")

	validate(t, &testCase{
		Name: "Collapse",

		Assessments: metricstesting.AssessmentTuples{
			&metricstesting.AssessmentTuple{
				Model:          modelA,
				Language:       languageA,
				RepositoryPath: "some-repository-a",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 1,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelA,
				Language:       languageA,
				RepositoryPath: "some-repository-b",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 2,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelA,
				Language:       languageB,
				RepositoryPath: "some-repository-a",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 3,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelA,
				Language:       languageB,
				RepositoryPath: "some-repository-b",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 4,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelB,
				Language:       languageA,
				RepositoryPath: "some-repository-a",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 5,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelB,
				Language:       languageA,
				RepositoryPath: "some-repository-b",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 6,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelB,
				Language:       languageB,
				RepositoryPath: "some-repository-a",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 7,
				},
			},
			&metricstesting.AssessmentTuple{
				Model:          modelB,
				Language:       languageB,
				RepositoryPath: "some-repository-b",
				Task:           evaluatetask.IdentifierWriteTests,
				Assessment: metrics.Assessments{
					metrics.AssessmentKeyResponseNoExcess: 8,
				},
			},
		},

		ExpectedAssessmentPerModel: AssessmentPerModel{
			"some-model-a": metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 10,
			},
			"some-model-b": metrics.Assessments{
				metrics.AssessmentKeyResponseNoExcess: 26,
			},
		},
	})
}

func assessmentTuplesToStore(at metricstesting.AssessmentTuples) (store *AssessmentStore) {
	store = NewAssessmentStore()
	for _, a := range at {
		store.Add(a.Model, a.Language, a.RepositoryPath, a.Task, a.Assessment)
	}

	return store
}
