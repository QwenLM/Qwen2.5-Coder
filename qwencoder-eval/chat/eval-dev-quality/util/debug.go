package util

import (
	"fmt"

	"github.com/kr/pretty"
)

// FormatToGoObject formats the given object to equivalent Go code.
func FormatToGoObject(object any) string {
	return fmt.Sprintf("%# v", pretty.Formatter(object))
}

// PrettyPrint pretty prints the given object to STDOUT.
func PrettyPrint(object any) {
	fmt.Printf("- %s\n", FormatToGoObject(object))
}

// Pretty pretty prints the given object to a string.
func Pretty(object any) string {
	return FormatToGoObject(object)
}
