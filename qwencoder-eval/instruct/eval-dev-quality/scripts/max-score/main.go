package main

import (
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/exp/maps"
)

var reTaskFileNameRepairAndWriteTest = regexp.MustCompile(`Given the following \w+ code file "(.*)" with`)
var reTaskFileNameTranspile = regexp.MustCompile(`The transpiled \w+ code file must have the package "(.*)"`)
var reTaskNameTranspileJava = regexp.MustCompile(`\s+class (\w+)\s*\{`)

func parseTaskName(s string) (string, bool) {
	if match := reTaskFileNameRepairAndWriteTest.FindStringSubmatch(s); match != nil {
		return match[1], true
	} else if match := reTaskFileNameTranspile.FindStringSubmatch(s); match != nil {
		return match[1], true
	}

	return "", false
}

var reModelName = regexp.MustCompile(`Model "(.*)" responded`)

func parseModelName(s string) (string, bool) {
	if match := reModelName.FindStringSubmatch(s); match != nil {
		return match[1], true
	}

	return "", false
}

var reCoverageObjects = regexp.MustCompile(`Executes tests with (\d+) coverage objects`)

func parseCoverageObjects(s string) (int, bool) {
	match := reCoverageObjects.FindStringSubmatch(s)
	if match == nil {
		return 0, false
	}
	coverageObjectsText := match[1]
	coverageObjects, err := strconv.Atoi(coverageObjectsText)
	if err != nil {
		panic(fmt.Sprintf("cannot convert %q to integer (%q)", coverageObjectsText, s))
	}

	return coverageObjects, true
}

var rePassingTests = regexp.MustCompile(`Executes tests with (\d+) tests passing`)

func parsePassingTests(s string) (int, bool) {
	match := rePassingTests.FindStringSubmatch(s)
	if match == nil {
		return 0, false
	}
	passingTestsText := match[1]
	passingTests, err := strconv.Atoi(passingTestsText)
	if err != nil {
		panic(fmt.Sprintf("cannot convert %q to integer (%q)", passingTestsText, s))
	}

	return passingTests, true
}

func main() {
	logFileNames := os.Args[1:]
	var logFileData []byte

	for _, logFileName := range logFileNames {
		data, err := os.ReadFile(logFileName)
		if err != nil {
			panic(err)
		}
		logFileData = append(logFileData, data...)
	}

	var currentTaskName string
	var currentModelName string
	bestCoverage := map[string]int{}
	bestCoverageModel := map[string]string{}
	bestTests := map[string]int{}
	bestTestsModel := map[string]string{}

	logFileLines := strings.Split(string(logFileData), "\n")
	fmt.Printf("Loaded %d log files (total of %d lines)\n", len(logFileNames), len(logFileLines))
	for _, line := range logFileLines {
		if taskName, ok := parseTaskName(line); ok {
			currentTaskName = taskName
		}
		// The package of Java is always "com.eval" so parse the task name from the class.
		if match := reTaskNameTranspileJava.FindStringSubmatch(line); currentTaskName == "com.eval" && match != nil {
			currentTaskName = match[1]
		}

		if modelName, ok := parseModelName(line); ok {
			currentModelName = modelName
		}

		if currentCoverageObjects, ok := parseCoverageObjects(line); ok && currentCoverageObjects > bestCoverage[currentTaskName] {
			bestCoverage[currentTaskName] = currentCoverageObjects
			bestCoverageModel[currentTaskName] = currentModelName
		}

		if currentPassingTests, ok := parsePassingTests(line); ok && currentPassingTests > bestTests[currentTaskName] {
			bestTests[currentTaskName] = currentPassingTests
			bestTestsModel[currentTaskName] = currentModelName
		}
	}

	if len(bestCoverage) > 0 {
		taskNames := maps.Keys(bestCoverage)
		sort.Strings(taskNames)
		fmt.Println("Coverage")
		sum := 0
		for _, taskName := range taskNames {
			score := bestCoverage[taskName]
			fmt.Printf(" - %s:%d (%q)\n", taskName, score, bestCoverageModel[taskName])
			sum += score
		}
		fmt.Printf("∑ = %d\n", sum)
	}

	if len(bestTests) > 0 {
		taskNames := maps.Keys(bestTests)
		sort.Strings(taskNames)
		fmt.Println("Tests Passing")
		sum := 0
		for _, taskName := range taskNames {
			score := bestTests[taskName]
			fmt.Printf(" - %s:%d (%q)\n", taskName, score, bestTestsModel[taskName])
			sum += score
		}
		fmt.Printf("∑ = %d\n", sum)

	}
}
