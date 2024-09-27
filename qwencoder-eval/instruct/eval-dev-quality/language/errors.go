package language

import (
	"errors"
)

// Common errors over all languages.
var (
	// ErrNoTestFound indicates that no tests could be found.
	ErrNoTestFound = errors.New("no tests could be found")
)
