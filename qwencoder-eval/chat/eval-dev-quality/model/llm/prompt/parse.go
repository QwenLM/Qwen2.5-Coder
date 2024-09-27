package prompt

import (
	"regexp"
	"strings"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
)

var (
	codeTagMatch           = regexp.MustCompile("(^|\n)\\s*```.*($|\n)")
	codeTagDuplicatedMatch = regexp.MustCompile("```(\\s|\n)*```")
)

// ParseResponse parses code from a model's response.
func ParseResponse(response string) (assessment metrics.Assessments, code string, err error) {
	assessment = metrics.Assessments{}

	// Check for empty responses.
	if strings.TrimSpace(response) == "" {
		return assessment, "", pkgerrors.New("empty response from model")
	}

	// Some models produce duplicated code tags, so unify them if needed.
	response = codeTagDuplicatedMatch.ReplaceAllString(response, "```")

	blocks := bytesutil.GuardedBlocks(response, codeTagMatch, codeTagMatch)

	// When no code blocks are found, assume that just the code is returned.
	if len(blocks) == 0 {
		// TODO If we cannot distinguish between code and text, we sadly also cannot check if the response contains actual code or if there is any excess response content. https://github.com/symflower/eval-dev-quality/issues/43

		// If we weren`t able to extract blocks despite code fences being present, that means they are not used correctly (i.e. opened and not closed or vice versa) so just remove them completely.
		if codeTagMatch.MatchString(response) {
			response = strings.ReplaceAll(response, "```", "")
		}

		return assessment, strings.TrimSpace(response), nil
	}
	assessment.Award(metrics.AssessmentKeyResponseWithCode)

	// Assume the first code block contains the response code fragment.
	block := blocks[0]

	// Check if the response contained only that single code block.
	responseWithoutBlock := strings.Replace(response, block, "", 1)
	if bytesutil.IsWhitespace(responseWithoutBlock) {
		assessment.Award(metrics.AssessmentKeyResponseNoExcess)
	}

	return assessment, strings.TrimSpace(codeTagMatch.ReplaceAllString(block, "")), nil
}
