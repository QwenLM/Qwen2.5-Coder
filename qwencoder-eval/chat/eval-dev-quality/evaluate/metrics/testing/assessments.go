package metricstesting

import (
	"testing"

	"golang.org/x/exp/maps"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/task"
)

// AssertAssessmentsEqual checks if the given assessments are equal ignoring default and nondeterministic values.
func AssertAssessmentsEqual(t *testing.T, expected metrics.Assessments, actual metrics.Assessments) {
	expected = maps.Clone(expected)
	actual = maps.Clone(actual)

	clearNonDeterministicAssessmentValues(expected)
	clearNonDeterministicAssessmentValues(actual)

	assert.Truef(t, expected.Equal(actual), "expected:%s\nactual:%s", expected, actual)
}

// AssertTaskAssessmentsEqual checks if the given assessments per task are equal ignoring default and nondeterministic values.
func AssertTaskAssessmentsEqual(t *testing.T, expected map[task.Identifier]metrics.Assessments, actual map[task.Identifier]metrics.Assessments) {
	expected = maps.Clone(expected)
	actual = maps.Clone(actual)

	// The expected and actual maps must have the same task identifiers.
	require.ElementsMatch(t, maps.Keys(expected), maps.Keys(actual))

	// Ignore non-deterministic values.
	for _, assessment := range expected {
		clearNonDeterministicAssessmentValues(assessment)
	}
	for _, assessment := range actual {
		clearNonDeterministicAssessmentValues(assessment)
	}

	for task, expectedAssessment := range expected {
		actualAssessment := actual[task]
		assert.Truef(t, expectedAssessment.Equal(actualAssessment), "task:%s\nexpected:%s\nactual:%s", task, expected, actual)
	}
}

// clearNonDeterministicAssessmentValues ignores non-deterministic values such as processing time and response character count.
func clearNonDeterministicAssessmentValues(assessment metrics.Assessments) {
	assessment[metrics.AssessmentKeyProcessingTime] = 0
	assessment[metrics.AssessmentKeyGenerateTestsForFileCharacterCount] = 0
	assessment[metrics.AssessmentKeyResponseCharacterCount] = 0
}

// AssessmentsWithProcessingTime is an empty assessment collection with positive processing time.
var AssessmentsWithProcessingTime = metrics.Assessments{
	metrics.AssessmentKeyProcessingTime: 1,
}

// AssessmentTuple holds all parameters uniquely defining to which run an assessment belongs to.
type AssessmentTuple struct {
	Model          model.Model
	Language       language.Language
	RepositoryPath string
	Task           task.Identifier
	Assessment     metrics.Assessments
}

type AssessmentTuples []*AssessmentTuple

func (at AssessmentTuples) ToMap() (lookup map[model.Model]map[language.Language]map[string]map[task.Identifier]metrics.Assessments) {
	lookup = map[model.Model]map[language.Language]map[string]map[task.Identifier]metrics.Assessments{}
	for _, t := range at {
		perLanguageLookup, ok := lookup[t.Model]
		if !ok {
			perLanguageLookup = map[language.Language]map[string]map[task.Identifier]metrics.Assessments{}
			lookup[t.Model] = perLanguageLookup
		}

		perRepositoryLookup, ok := perLanguageLookup[t.Language]
		if !ok {
			perRepositoryLookup = map[string]map[task.Identifier]metrics.Assessments{}
			perLanguageLookup[t.Language] = perRepositoryLookup
		}

		perTaskLookup, ok := perRepositoryLookup[t.RepositoryPath]
		if !ok {
			perTaskLookup = map[task.Identifier]metrics.Assessments{}
			perRepositoryLookup[t.RepositoryPath] = perTaskLookup
		}

		assessments, ok := perTaskLookup[t.Task]
		if !ok {
			assessments = metrics.NewAssessments()
			perTaskLookup[t.Task] = assessments
		}

		assessments.Add(t.Assessment)
	}

	return lookup
}
