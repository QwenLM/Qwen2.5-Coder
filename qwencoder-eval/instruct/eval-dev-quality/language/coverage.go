package language

import (
	"encoding/json"
	"errors"
	"os"
	"regexp"

	pkgerrors "github.com/pkg/errors"
	"github.com/symflower/eval-dev-quality/log"
)

// CoverageBlockUnfolded is an unfolded representation of a coverage data block.
type CoverageBlockUnfolded struct {
	// FileRange holds the file range.
	FileRange string
	// CoverageType holds the covered coverage type.
	CoverageType string
	// Count holds the execution count.
	Count uint
}

// FileRangeMatch match a textual file range with lines and columns.
var FileRangeMatch = regexp.MustCompile(`^(.+):(\d+):(\d+)-(.+):(\d+):(\d+)$`)

// CoverageObjectCountOfFile parses the given coverage file and returns its coverage object count.
func CoverageObjectCountOfFile(logger *log.Logger, coverageFilePath string) (coverageObjectCount uint64, err error) {
	coverageFile, err := os.ReadFile(coverageFilePath)
	if err != nil {
		return 0, pkgerrors.WithMessage(pkgerrors.WithStack(err), coverageFilePath)
	}

	// Log coverage objects.
	logger.Printf("coverage objects: %s", string(coverageFile))

	var coverageData []CoverageBlockUnfolded
	if err := json.Unmarshal(coverageFile, &coverageData); err != nil {
		return 0, pkgerrors.WithMessage(pkgerrors.WithStack(err), string(coverageFile))
	}
	for _, c := range coverageData {
		if c.Count == 0 {
			continue
		}

		fr := FileRangeMatch.FindStringSubmatch(c.FileRange)
		if fr == nil {
			return 0, pkgerrors.WithMessage(pkgerrors.WithStack(errors.New("could not match file range")), c.FileRange)
		}

		coverageObjectCount++
	}

	return coverageObjectCount, nil
}
