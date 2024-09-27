package util

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestUniqueName(t *testing.T) {
	type testCase struct {
		Name string

		Input        string
		AlreadyExist []string

		ExpectedUniqueName string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			alreadyExist := make(map[string]bool, len(tc.AlreadyExist))
			for _, exists := range tc.AlreadyExist {
				alreadyExist[exists] = true
			}

			actualUniqueName, err := UniqueName(tc.Input, func(candidate string) (bool, error) {
				return alreadyExist[candidate], nil
			})
			require.NoError(t, err)
			assert.Equal(t, tc.ExpectedUniqueName, actualUniqueName)
		})
	}

	validate(t, &testCase{
		Name: "Already Unique",

		Input: "foo",

		ExpectedUniqueName: "foo",
	})
	validate(t, &testCase{
		Name: "Not Unique",

		Input: "foo",
		AlreadyExist: []string{
			"foo",
		},

		ExpectedUniqueName: "foo-0",
	})
	validate(t, &testCase{
		Name: "Multiple Outputs Exist",

		Input: "foo",
		AlreadyExist: []string{
			"foo",
			"foo-0",
			"foo-1",
			"foo-2",
		},

		ExpectedUniqueName: "foo-3",
	})
}
