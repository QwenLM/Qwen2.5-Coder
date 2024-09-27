package importMissing

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestImportMissing(t *testing.T) {
	type testCase struct {
		Name string

		S string

		ExpectedBool bool
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualBool := importMissing(tc.S)

			assert.Equal(t, tc.ExpectedBool, actualBool)
		})
	}

	validate(t, &testCase{
		S: "bar",

		ExpectedBool: false,
	})
	validate(t, &testCase{
		S: "foobar",

		ExpectedBool: true,
	})
}
