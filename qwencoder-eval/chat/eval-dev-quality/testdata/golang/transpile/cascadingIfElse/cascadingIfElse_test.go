package cascadingIfElse

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSymflowerCascadingIfElse(t *testing.T) {
	type testCase struct {
		Name string

		I int

		ExpectedInt int
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualInt := cascadingIfElse(tc.I)

			assert.Equal(t, tc.ExpectedInt, actualInt)
		})
	}

	validate(t, &testCase{
		I: 0,

		ExpectedInt: 5,
	})
	validate(t, &testCase{
		I: 1,

		ExpectedInt: 2,
	})
	validate(t, &testCase{
		I: 3,

		ExpectedInt: 4,
	})
}
