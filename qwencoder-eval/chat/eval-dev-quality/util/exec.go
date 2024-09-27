package util

import (
	"bytes"
	"context"
	"io"
	"os/exec"
	"reflect"
	"strings"
	"sync"
	"time"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/log"
)

// Command defines a command that should be executed.
type Command struct {
	// Command holds the command with its optional arguments.
	Command []string
	// Stdin holds a string which is passed on as STDIN.
	Stdin string

	// Directory defines the directory the execution should run in, without changing the working directory of the caller.
	Directory string
	// Env overwrites the environment variables of the executed command.
	Env map[string]string
}

// CommandWithResult executes a command and returns its output, while printing the same output to the given logger.
func CommandWithResult(ctx context.Context, logger *log.Logger, command *Command) (output string, err error) {
	logger.Printf("$ %s", strings.Join(command.Command, " "))

	var writer bytesutil.SynchronizedBuffer
	c := exec.CommandContext(ctx, command.Command[0], command.Command[1:]...)
	if command.Directory != "" {
		c.Dir = command.Directory
	}
	if command.Env != nil {
		envs := osutil.EnvironMap()
		for k, v := range command.Env {
			envs[k] = v
		}
		for k, v := range envs {
			c.Env = append(c.Env, k+"="+v)
		}
	}
	if command.Stdin != "" {
		c.Stdin = bytes.NewBufferString(command.Stdin)
	}
	c.Stdout = io.MultiWriter(logger.Writer(), &writer)
	c.Stderr = c.Stdout

	c.WaitDelay = 3 * time.Second // Some binaries do not like to be killed, e.g. "ollama", so we kill them after some time automatically.

	if err := c.Run(); err != nil {
		return writer.String(), pkgerrors.WithStack(pkgerrors.WithMessage(err, writer.String()))
	}

	return writer.String(), nil
}

// Flags returns a list of `long` flags bound on the command or nil.
func Flags(cmd any) (args []string) {
	typ := reflect.TypeOf(cmd)

	// Dereference pointer
	if typ.Kind() == reflect.Pointer {
		typ = typ.Elem()
	}

	if typ.Kind() != reflect.Struct {
		return nil
	}

	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		arg, ok := field.Tag.Lookup("long")
		if !ok {
			continue
		}

		args = append(args, arg)
	}

	return args
}

// FilterArgs filters the arguments by either ignoring/allowing them in the result.
func FilterArgs(args []string, filter []string, ignore bool) (filtered []string) {
	filterMap := map[string]bool{}
	for _, v := range filter {
		filterMap["--"+v] = true
	}

	// Resolve args with equals sign.
	var resolvedArgs []string
	for _, v := range args {
		if strings.HasPrefix(v, "--") && strings.Contains(v, "=") {
			resolvedArgs = append(resolvedArgs, strings.SplitN(v, "=", 2)...)
		} else {
			resolvedArgs = append(resolvedArgs, v)
		}
	}

	skip := true
	for _, v := range resolvedArgs {
		if strings.HasPrefix(v, "--") {
			if ignore {
				skip = filterMap[v]
			} else {
				skip = !filterMap[v]
			}
		}

		if skip {
			continue
		}

		filtered = append(filtered, v)
	}

	return filtered
}

// FilterArgsKeep filters the given argument list and only returns arguments defined present in "filter".
func FilterArgsKeep(args []string, filter []string) (filtered []string) {
	return FilterArgs(args, filter, false)
}

// FilterArgsRemove filters the given argument list and returns arguments where "filter" entries are removed.
func FilterArgsRemove(args []string, filter []string) (filtered []string) {
	return FilterArgs(args, filter, true)
}

// Parallel holds a buffered channel for limiting parallel executions.
type Parallel struct {
	ch chan struct{}
	wg sync.WaitGroup
}

// NewParallel returns a Parallel execution helper.
func NewParallel(maxWorkers uint) *Parallel {
	return &Parallel{
		ch: make(chan struct{}, maxWorkers),
	}
}

// acquire slot.
func (p *Parallel) acquire() {
	p.ch <- struct{}{}
}

// release slot.
func (p *Parallel) release() {
	<-p.ch
}

// Execute runs the given function while checking for a execution limit.
func (p *Parallel) Execute(f func()) {
	p.acquire()
	p.wg.Add(1)

	go func() {
		defer p.release()
		defer p.wg.Done()
		f()
	}()
}

// Wait waits until all executions are done.
func (l *Parallel) Wait() {
	l.wg.Wait()
}
