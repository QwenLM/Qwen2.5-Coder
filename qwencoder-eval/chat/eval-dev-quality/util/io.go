package util

import (
	"errors"
	"fmt"
	"math"
	"os"
	"strconv"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil"
)

// UniqueName creates an unique name.
func UniqueName(name string, existsFunction func(candidate string) (bool, error)) (uniqueName string, err error) {
	if exists, err := existsFunction(name); err != nil {
		return "", pkgerrors.Wrap(err, fmt.Sprintf("cannot create unique name for %q", name))
	} else if !exists {
		return name, nil
	}

	for i := uint64(0); i < math.MaxUint64; i++ {
		candidate := name + "-" + strconv.FormatUint(i, 10)
		if exists, err := existsFunction(candidate); err != nil {
			return "", pkgerrors.Wrap(err, fmt.Sprintf("cannot create unique name for %q", name))
		} else if !exists {
			return candidate, nil
		}
	}

	return "", pkgerrors.New(fmt.Sprintf("cannot create unique name for: %q", name))
}

// UniqueDirectory creates a unique directory from the given path.
func UniqueDirectory(path string) (uniquePath string, err error) {
	return UniqueName(path, func(candidate string) (bool, error) {
		if err := osutil.DirExists(candidate); err != nil {
			if errors.Is(err, os.ErrNotExist) {
				return false, nil
			}

			return false, err
		}

		return true, nil
	})
}
