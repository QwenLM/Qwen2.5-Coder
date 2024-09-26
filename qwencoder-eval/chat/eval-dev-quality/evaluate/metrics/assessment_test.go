package metrics

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAssessmentsAdd(t *testing.T) {
	type testCase struct {
		Name string

		Assessments Assessments
		X           Assessments

		ExpectedAssessments Assessments
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			tc.Assessments.Add(tc.X)

			assert.Equal(t, tc.Assessments, tc.ExpectedAssessments)
		})
	}

	validate(t, &testCase{
		Name: "Empty",

		Assessments: NewAssessments(),
		X:           NewAssessments(),

		ExpectedAssessments: NewAssessments(),
	})

	validate(t, &testCase{
		Name: "Non existing key",

		Assessments: NewAssessments(),
		X: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},

		ExpectedAssessments: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},
	})

	validate(t, &testCase{
		Name: "Existing key",

		Assessments: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},
		X: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},

		ExpectedAssessments: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 2,
		},
	})
}

func TestAssessmentsMerge(t *testing.T) {
	type testCase struct {
		Name string

		A Assessments
		B Assessments

		ExpectedC Assessments
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualC := Merge(tc.A, tc.B)

			assert.Equal(t, tc.ExpectedC, actualC)
		})
	}

	validate(t, &testCase{
		Name: "Empty",

		ExpectedC: NewAssessments(),
	})

	validate(t, &testCase{
		Name: "Non existing key",

		A: NewAssessments(),
		B: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},

		ExpectedC: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},
	})

	validate(t, &testCase{
		Name: "Existing key",

		A: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},
		B: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 1,
		},

		ExpectedC: map[AssessmentKey]uint64{
			AssessmentKeyResponseNoExcess: 2,
		},
	})
}

func TestAssessmentString(t *testing.T) {
	type testCase struct {
		Name string

		Assessment Assessments

		ExpectedString string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualString := tc.Assessment.String()

			assert.Equal(t, tc.ExpectedString, actualString)
		})
	}

	validate(t, &testCase{
		Name: "Empty Metrics",

		Assessment: NewAssessments(),

		ExpectedString: "score=0, coverage=0, files-executed=0, files-executed-maximum-reachable=0, generate-tests-for-file-character-count=0, processing-time=0, response-character-count=0, response-no-error=0, response-no-excess=0, response-with-code=0, tests-passing=0",
	})

	validate(t, &testCase{
		Name: "Non-empty Metrics",

		Assessment: Assessments{
			AssessmentKeyGenerateTestsForFileCharacterCount: 50,
			AssessmentKeyResponseCharacterCount:             100,
			AssessmentKeyCoverage:                           1,
			AssessmentKeyFilesExecuted:                      2,
			AssessmentKeyFilesExecutedMaximumReachable:      2,
			AssessmentKeyResponseNoError:                    3,
			AssessmentKeyResponseNoExcess:                   4,
			AssessmentKeyResponseWithCode:                   5,
			AssessmentKeyProcessingTime:                     200,
			AssessmentKeyTestsPassing:                       70,
		},

		ExpectedString: "score=85, coverage=1, files-executed=2, files-executed-maximum-reachable=2, generate-tests-for-file-character-count=50, processing-time=200, response-character-count=100, response-no-error=3, response-no-excess=4, response-with-code=5, tests-passing=70",
	})
}

func TestAssessmentsEqual(t *testing.T) {
	type testCase struct {
		Name string

		Assessments Assessments
		X           Assessments

		ExpectedBool bool
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualBool := tc.Assessments.Equal(tc.X)

			assert.Equal(t, tc.ExpectedBool, actualBool)
		})
	}

	validate(t, &testCase{
		Name: "Empty",

		Assessments: NewAssessments(),
		X:           NewAssessments(),

		ExpectedBool: true,
	})

	validate(t, &testCase{
		Name: "Nil",

		Assessments: nil,
		X:           nil,

		ExpectedBool: true,
	})

	validate(t, &testCase{
		Name: "Equal Values",

		Assessments: Assessments{
			AssessmentKeyResponseWithCode: 2,
		},
		X: Assessments{
			AssessmentKeyResponseWithCode: 2,
		},

		ExpectedBool: true,
	})

	validate(t, &testCase{
		Name: "Default Value",

		Assessments: Assessments{
			AssessmentKeyResponseWithCode: 2,
			AssessmentKeyResponseNoError:  0,
		},
		X: Assessments{
			AssessmentKeyResponseWithCode: 2,
		},

		ExpectedBool: true,
	})

	validate(t, &testCase{
		Name: "Different Values",

		Assessments: Assessments{
			AssessmentKeyResponseWithCode: 3,
		},
		X: Assessments{
			AssessmentKeyResponseWithCode: 2,
		},

		ExpectedBool: false,
	})
}

func TestAssessmentsScore(t *testing.T) {
	type testCase struct {
		Name string

		Assessments Assessments

		ExpectedScore uint64
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualScore := tc.Assessments.Score()

			assert.Equal(t, tc.ExpectedScore, actualScore)
		})
	}

	validate(t, &testCase{
		Name: "Empty Assessment",

		Assessments: NewAssessments(),

		ExpectedScore: uint64(0),
	})

	validate(t, &testCase{
		Name: "Values Assessment",

		Assessments: Assessments{
			AssessmentKeyFilesExecuted:  5,
			AssessmentKeyCoverage:       4,
			AssessmentKeyProcessingTime: 200,
		},

		ExpectedScore: uint64(9),
	})
}

func TestCombineModelAndSymflowerFixAssessments(t *testing.T) {
	type testCase struct {
		Name string

		ModelAssessment         Assessments
		SymflowerFixAssessments Assessments

		ExpectedAssessments Assessments
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualAssessments := CombineWithSymflowerFixAssessments(tc.ModelAssessment, tc.SymflowerFixAssessments)

			assert.Equal(t, tc.ExpectedAssessments, actualAssessments)
		})
	}

	validate(t, &testCase{
		Name: "Simple",

		ModelAssessment: Assessments{
			AssessmentKeyFilesExecuted:                      1,
			AssessmentKeyProcessingTime:                     uint64(200),
			AssessmentKeyCoverage:                           0,
			AssessmentKeyResponseCharacterCount:             100,
			AssessmentKeyGenerateTestsForFileCharacterCount: 50,
			AssessmentKeyResponseNoError:                    0,
			AssessmentKeyResponseWithCode:                   1,
			AssessmentKeyResponseNoExcess:                   1,
		},
		SymflowerFixAssessments: Assessments{
			AssessmentKeyFilesExecuted:   1,
			AssessmentKeyProcessingTime:  uint64(100),
			AssessmentKeyCoverage:        10,
			AssessmentKeyResponseNoError: 1,
			AssessmentKeyTestsPassing:    100,
		},

		ExpectedAssessments: Assessments{
			AssessmentKeyFilesExecuted:                      1,
			AssessmentKeyProcessingTime:                     uint64(300),
			AssessmentKeyCoverage:                           10,
			AssessmentKeyResponseCharacterCount:             100,
			AssessmentKeyGenerateTestsForFileCharacterCount: 50,
			AssessmentKeyResponseNoError:                    0,
			AssessmentKeyResponseWithCode:                   1,
			AssessmentKeyResponseNoExcess:                   1,
			AssessmentKeyTestsPassing:                       100,
		},
	})
}
