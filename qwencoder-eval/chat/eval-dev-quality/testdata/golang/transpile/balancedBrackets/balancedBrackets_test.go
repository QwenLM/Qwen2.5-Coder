package balancedBrackets

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSymflowerHasBalancedBrackets(t *testing.T) {
	type testCase struct {
		Name string

		CharArray string

		ExpectedBool bool
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualBool := hasBalancedBrackets(tc.CharArray)

			assert.Equal(t, tc.ExpectedBool, actualBool)
		})
	}

	validate(t, &testCase{
		CharArray: "",

		ExpectedBool: true,
	})
	validate(t, &testCase{
		CharArray: "[",

		ExpectedBool: false,
	})
	validate(t, &testCase{
		CharArray: "[[[]]",

		ExpectedBool: false,
	})
	validate(t, &testCase{
		CharArray: "[[]]",

		ExpectedBool: true,
	})
	validate(t, &testCase{
		CharArray: "[[[[]]]]",

		ExpectedBool: true,
	})
}
