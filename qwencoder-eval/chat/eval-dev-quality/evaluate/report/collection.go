package report

import (
	"cmp"
	"slices"
	"sort"

	"golang.org/x/exp/maps"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/task"
)

// AssessmentPerModel holds a collection of assessments per model id.
type AssessmentPerModel map[string]metrics.Assessments

// WalkByScore walks the given assessment metrics by their score.
func (a AssessmentPerModel) WalkByScore(function func(model string, assessment metrics.Assessments, score uint64) error) (err error) {
	models := maps.Keys(a)
	sort.Strings(models)

	scores := make(map[string]uint64, len(models))
	for _, model := range models {
		scores[model] = a[model].Score()
	}
	sort.SliceStable(models, func(i, j int) bool {
		return scores[models[i]] < scores[models[j]]
	})

	for _, model := range models {
		if err := function(model, a[model], scores[model]); err != nil {
			return err
		}
	}

	return nil
}

// AssessmentStore holds a collection of assessments per model per language and per repository.
type AssessmentStore struct {
	store map[model.Model]map[language.Language]map[string]map[task.Identifier]metrics.Assessments
}

// NewAssessmentStore returns a new store for collecting assessments.
func NewAssessmentStore() (assessments *AssessmentStore) {
	return &AssessmentStore{
		store: map[model.Model]map[language.Language]map[string]map[task.Identifier]metrics.Assessments{},
	}
}

// Add adds a new assessment.
func (a *AssessmentStore) Add(model model.Model, l language.Language, repositoryPath string, taskIdentifier task.Identifier, assessment metrics.Assessments) {
	perLanguageLookup, ok := a.store[model]
	if !ok {
		perLanguageLookup = map[language.Language]map[string]map[task.Identifier]metrics.Assessments{}
		a.store[model] = perLanguageLookup
	}

	perRepositoryLookup, ok := perLanguageLookup[l]
	if !ok {
		perRepositoryLookup = map[string]map[task.Identifier]metrics.Assessments{}
		perLanguageLookup[l] = perRepositoryLookup
	}

	perTaskLookup, ok := perRepositoryLookup[repositoryPath]
	if !ok {
		perTaskLookup = map[task.Identifier]metrics.Assessments{}
		perRepositoryLookup[repositoryPath] = perTaskLookup
	}

	assessments, ok := perTaskLookup[taskIdentifier]
	if !ok {
		assessments = metrics.NewAssessments()
		perTaskLookup[taskIdentifier] = assessments
	}

	assessments.Add(assessment)
}

// AddAssessmentPerTask adds new assessments per task.
func (a *AssessmentStore) AddAssessmentPerTask(model model.Model, l language.Language, repositoryPath string, taskAssessment map[task.Identifier]metrics.Assessments) {
	for taskIdentifier, assessment := range taskAssessment {
		a.Add(model, l, repositoryPath, taskIdentifier, assessment)
	}
}

// Walk walks over all entries.
func (a *AssessmentStore) Walk(function func(m model.Model, l language.Language, r string, t task.Identifier, a metrics.Assessments) error) (err error) {
	models := maps.Keys(a.store)
	slices.SortStableFunc(models, func(a, b model.Model) int {
		return cmp.Compare(a.ID(), b.ID())
	})
	for _, m := range models {
		languages := maps.Keys(a.store[m])
		slices.SortStableFunc(languages, func(a, b language.Language) int {
			return cmp.Compare(a.ID(), b.ID())
		})
		for _, l := range languages {
			repositories := maps.Keys(a.store[m][l])
			sort.Strings(repositories)
			for _, r := range repositories {
				taskIdentifiers := maps.Keys(a.store[m][l][r])
				for _, t := range taskIdentifiers {
					if err := function(m, l, r, t, a.store[m][l][r][t]); err != nil {
						return err
					}
				}
			}
		}
	}

	return nil
}

// CollapseByModel returns all assessments aggregated per model ID.
func (a *AssessmentStore) CollapseByModel() AssessmentPerModel {
	perModel := make(AssessmentPerModel, len(a.store))
	for _, m := range maps.Keys(a.store) {
		perModel[m.ID()] = metrics.NewAssessments()
	}
	_ = a.Walk(func(m model.Model, l language.Language, r string, t task.Identifier, a metrics.Assessments) (err error) {
		perModel[m.ID()].Add(a)

		return nil
	})

	return perModel
}
