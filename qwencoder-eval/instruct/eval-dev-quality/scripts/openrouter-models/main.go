package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strings"

	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/provider/openrouter"
	"golang.org/x/exp/maps"
)

func baseModel(name string) string {
	return strings.TrimSuffix(strings.TrimSuffix(name, "-instruct"), "-chat")
}

func isBaseModel(name string) bool {
	return baseModel(name) == name
}

func containsInstructModel(models map[string]bool, name string) string {
	if models[name+"-instruct"] {
		return name + "-instruct"
	} else if models[name+"-chat"] {
		return name + "-chat"
	}

	return ""
}

var ignoredModels = []string{
	// Alias models.
	"openrouter/openrouter/flavor-of-the-week",
	"openrouter/openrouter/auto",

	// Special property models.
	".*:free$",
	".*:beta$",
	".*:nitro$",
	".*:extended$",

	// Model previews, online access models and vision models.
	".*-preview",
	".*-online",
	".*-vision-?",
}

func isIgnored(model model.Model) bool {
	for _, regex := range ignoredModels {
		if regexp.MustCompile(regex).MatchString(model.ID()) {
			return true
		}
	}

	return false
}

func main() {
	provider := openrouter.NewProvider()
	allModels, err := provider.Models()
	if err != nil {
		panic(err)
	}

	models := map[string]bool{}
	for _, model := range allModels {
		if isIgnored(model) {
			fmt.Printf("ignoring %q\n", model.ID())

			continue
		}

		if !isBaseModel(model.ID()) && models[baseModel(model.ID())] {
			baseModelName := baseModel(model.ID())
			fmt.Printf("ignoring %q for instruct model %q\n", baseModelName, model.ID())

			delete(models, baseModelName)
		} else if instructModelName := containsInstructModel(models, model.ID()); instructModelName != "" {
			fmt.Printf("ignoring %q for instruct model %q\n", model.ID(), instructModelName)

			continue
		}

		models[model.ID()] = true
	}

	modelNames := maps.Keys(models)
	sort.Strings(modelNames)

	csvFile, err := os.Create("openrouter.csv")
	if err != nil {
		panic(err)
	}
	defer csvFile.Close()
	csvWriter := csv.NewWriter(csvFile)
	defer csvWriter.Flush()

	csvWriter.Write([]string{"model"})
	for _, model := range modelNames {
		csvWriter.Write([]string{model})
	}
}
