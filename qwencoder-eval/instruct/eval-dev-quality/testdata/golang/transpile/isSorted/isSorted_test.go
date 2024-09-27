package isSorted

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSymflowerIsSorted(t *testing.T) {
	type testCase struct {
		Name string

		A []int

		ExpectedBool bool
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualBool := isSorted(tc.A)

			assert.Equal(t, tc.ExpectedBool, actualBool)
		})
	}

	validate(t, &testCase{
		A: []int(nil),

		ExpectedBool: false,
	})
	validate(t, &testCase{
		A: []int{5, 4, 3, 2, 1},

		ExpectedBool: false,
	})
	validate(t, &testCase{
		A: []int{0},

		ExpectedBool: true,
	})
	validate(t, &testCase{
		A: []int{1, 2, 3, 4, 5},

		ExpectedBool: true,
	})
	validate(t, &testCase{
		A: []int{1, 2, 10, 11, 20, 21},

		ExpectedBool: true,
	})
}
