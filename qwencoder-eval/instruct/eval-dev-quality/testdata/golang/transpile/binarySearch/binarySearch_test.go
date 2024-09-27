package binarySearch

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSymflowerBinarySearch(t *testing.T) {
	type testCase struct {
		Name string

		A []int
		X int

		ExpectedInt int
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualInt := binarySearch(tc.A, tc.X)

			assert.Equal(t, tc.ExpectedInt, actualInt)
		})
	}

	validate(t, &testCase{
		A: []int(nil),
		X: 0,

		ExpectedInt: -1,
	})
	validate(t, &testCase{
		A: []int{0},
		X: 5,

		ExpectedInt: -1,
	})
	validate(t, &testCase{
		A: []int{1, 2, 3, 4, 5},
		X: 6,

		ExpectedInt: -1,
	})
	validate(t, &testCase{
		A: []int{1, 2, 3, 4, 5},
		X: 3,

		ExpectedInt: 2,
	})
	validate(t, &testCase{
		A: []int{1, 5, 10, 15, 20, 25},
		X: 25,

		ExpectedInt: 5,
	})
}
