package pascalsTriangle

import (
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSymflowerPascalsTriangle(t *testing.T) {
	type testCase struct {
		Name string

		Rows int

		ExpectedSlice [][]int
		ExpectedError error
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualSlice, actualError := pascalsTriangle(tc.Rows)

			assert.Equal(t, tc.ExpectedSlice, actualSlice)
			assert.Equal(t, tc.ExpectedError, actualError)
		})
	}

	validate(t, &testCase{
		Rows: -1,

		ExpectedSlice: [][]int(nil),
		ExpectedError: errors.New("Rows can't be negative!"),
	})
	validate(t, &testCase{
		Rows: 0,

		ExpectedSlice: [][]int{},
	})
	validate(t, &testCase{
		Rows: 1,

		ExpectedSlice: [][]int{
			[]int{1},
		},
	})
	validate(t, &testCase{
		Rows: 5,

		ExpectedSlice: [][]int{
			[]int{1},
			[]int{1, 1},
			[]int{1, 2, 1},
			[]int{1, 3, 3, 1},
			[]int{1, 4, 6, 4, 1},
		},
	})
}
