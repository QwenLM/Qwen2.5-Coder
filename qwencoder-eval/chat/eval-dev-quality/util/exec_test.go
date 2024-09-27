package util

import (
	"context"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/symflower/eval-dev-quality/log"
)

func TestCommandWithResultTimeout(t *testing.T) {
	logOutput, logger := log.Buffer()
	defer func() {
		if t.Failed() {
			t.Log(logOutput.String())
		}
	}()

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(1*time.Second))
	defer cancel()

	start := time.Now()
	_, err := CommandWithResult(ctx, logger, &Command{
		Command: []string{
			"sleep",
			"60",
		},
	})
	duration := time.Since(start)

	assert.Error(t, err)
	assert.Less(t, duration.Seconds(), 5.0)
}

func TestFilterArgs(t *testing.T) {
	type testCase struct {
		Name string

		Args   []string
		Filter []string
		Ignore bool

		ExpectedFiltered []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualFiltered := FilterArgs(tc.Args, tc.Filter, tc.Ignore)

			assert.Equal(t, tc.ExpectedFiltered, actualFiltered)
		})
	}

	validate(t, &testCase{
		Name: "Filter arguments",

		Args: []string{
			"--runtime",
			"abc",
			"--runs",
			"5",
		},
		Filter: []string{
			"runtime",
		},
		Ignore: true,

		ExpectedFiltered: []string{
			"--runs",
			"5",
		},
	})

	validate(t, &testCase{
		Name: "Filter arguments with equals sign",

		Args: []string{
			"--runtime=abc",
			"--runs=5",
			"--foo",
			"bar",
		},
		Filter: []string{
			"runtime",
		},
		Ignore: true,

		ExpectedFiltered: []string{
			"--runs",
			"5",
			"--foo",
			"bar",
		},
	})

	validate(t, &testCase{
		Name: "Filter arguments with an allow list",

		Args: []string{
			"--runtime=abc",
			"--runs=5",
			"--foo",
			"bar",
		},

		Filter: []string{
			"runtime",
		},

		ExpectedFiltered: []string{
			"--runtime",
			"abc",
		},
	})
}

func TestFilterArgsKeep(t *testing.T) {
	type testCase struct {
		Name string

		Args   []string
		Filter []string

		ExpectedFiltered []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualFiltered := FilterArgsKeep(tc.Args, tc.Filter)

			assert.Equal(t, tc.ExpectedFiltered, actualFiltered)
		})
	}

	validate(t, &testCase{
		Name: "Keep arguments",

		Args: []string{
			"--runtime=abc",
			"--runs=5",
			"--foo",
			"bar",
		},

		Filter: []string{
			"runtime",
		},

		ExpectedFiltered: []string{
			"--runtime",
			"abc",
		},
	})

	validate(t, &testCase{
		Name: "Multiple arguments",

		Args: []string{
			"--runtime=abc",
			"--repository=abc",
			"--repository=def",
			"--foo",
			"bar",
		},

		Filter: []string{
			"runtime",
			"repository",
		},

		ExpectedFiltered: []string{
			"--runtime",
			"abc",
			"--repository",
			"abc",
			"--repository",
			"def",
		},
	})
}

func TestFilterArgsRemove(t *testing.T) {
	type testCase struct {
		Name string

		Args   []string
		Filter []string

		ExpectedFiltered []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualFiltered := FilterArgsRemove(tc.Args, tc.Filter)

			assert.Equal(t, tc.ExpectedFiltered, actualFiltered)
		})
	}

	validate(t, &testCase{
		Name: "Remove arguments",

		Args: []string{
			"--runtime",
			"abc",
			"--runs",
			"5",
		},
		Filter: []string{
			"runtime",
		},

		ExpectedFiltered: []string{
			"--runs",
			"5",
		},
	})
}

func TestParallelExecute(t *testing.T) {
	type testCase struct {
		Limit uint
		Times uint

		Function func()
	}

	run := func(tc *testCase) {
		p := NewParallel(tc.Limit)
		for i := uint(0); i < tc.Times; i++ {
			p.Execute(tc.Function)
		}
		p.Wait()
	}

	t.Run("Atomic count", func(t *testing.T) {
		var count atomic.Uint32
		expectedCount := uint(10)

		tc := &testCase{
			Limit: 2,
			Times: expectedCount,

			Function: func() {
				count.Add(1)
			},
		}

		run(tc)

		assert.Equal(t, count.Load(), uint32(expectedCount))
	})

	t.Run("Timed limiting", func(t *testing.T) {
		tc := &testCase{
			Limit: 1,
			Times: 3,

			Function: func() {
				time.Sleep(500 * time.Millisecond)
			},
		}

		start := time.Now()
		run(tc)
		duration := time.Since(start)

		assert.GreaterOrEqual(t, duration, 1500*time.Millisecond)
	})

}

func TestFlags(t *testing.T) {
	type testCase struct {
		Name string

		Cmd any

		ExpectedArgs []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualArgs := Flags(tc.Cmd)

			assert.Equal(t, tc.ExpectedArgs, actualArgs)
		})
	}

	validate(t, &testCase{
		Name: "Struct Command",

		Cmd: struct {
			PropA string `long:"PropA"`
			PropB string `long:"PropB"`
			PropC string `short:"hey"`
		}{},

		ExpectedArgs: []string{
			"PropA",
			"PropB",
		},
	})

	validate(t, &testCase{
		Name: "Pointer Struct Command",

		Cmd: &struct {
			PropA string `long:"PropA"`
			PropB string `long:"PropB"`
		}{},

		ExpectedArgs: []string{
			"PropA",
			"PropB",
		},
	})
}
