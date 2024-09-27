package report

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	evaluatetask "github.com/symflower/eval-dev-quality/evaluate/task"
	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
	"github.com/symflower/eval-dev-quality/model"
	modeltesting "github.com/symflower/eval-dev-quality/model/testing"
	"github.com/symflower/eval-dev-quality/task"
)

func TestNewEvaluationFile(t *testing.T) {
	var file strings.Builder
	_, err := NewEvaluationFile(&file)
	require.NoError(t, err)

	actualEvaluationFileContent := file.String()
	require.NoError(t, err)

	expectedEvaluationFileContent := bytesutil.StringTrimIndentations(`
		model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
	`)

	assert.Equal(t, expectedEvaluationFileContent, string(actualEvaluationFileContent))
}

func TestWriteEvaluationRecord(t *testing.T) {
	type testCase struct {
		Name string

		Assessments map[task.Identifier]metrics.Assessments

		ExpectedCSV string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			var file strings.Builder
			evaluationFile, err := NewEvaluationFile(&file)
			require.NoError(t, err)

			modelMock := modeltesting.NewMockModelNamed(t, "mocked-model")
			languageMock := languagetesting.NewMockLanguageNamed(t, "golang")

			err = evaluationFile.WriteEvaluationRecord(modelMock, languageMock, "golang/plain", tc.Assessments)
			require.NoError(t, err)

			assert.Equal(t, bytesutil.StringTrimIndentations(tc.ExpectedCSV), file.String())
		})
	}

	validate(t, &testCase{
		Name: "Single task with empty assessments",

		Assessments: map[task.Identifier]metrics.Assessments{
			evaluatetask.IdentifierWriteTests: metrics.NewAssessments(),
		},

		ExpectedCSV: `
			model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
			mocked-model,golang,golang/plain,write-tests,0,0,0,0,0,0,0,0,0,0,0
		`,
	})
	validate(t, &testCase{
		Name: "Multiple tasks with assessments",

		Assessments: map[task.Identifier]metrics.Assessments{
			evaluatetask.IdentifierWriteTests: metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted:                 1,
				metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
				metrics.AssessmentKeyResponseNoError:               1,
				metrics.AssessmentKeyCoverage:                      0,
			},
			evaluatetask.IdentifierWriteTestsSymflowerFix: metrics.Assessments{
				metrics.AssessmentKeyFilesExecuted:                 1,
				metrics.AssessmentKeyFilesExecutedMaximumReachable: 1,
				metrics.AssessmentKeyResponseNoError:               1,
				metrics.AssessmentKeyCoverage:                      10,
			},
		},

		ExpectedCSV: `
			model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
			mocked-model,golang,golang/plain,write-tests,2,0,1,1,0,0,0,1,0,0,0
			mocked-model,golang,golang/plain,write-tests-symflower-fix,12,10,1,1,0,0,0,1,0,0,0
		`,
	})
}

func TestRecordsFromEvaluationCSVFiles(t *testing.T) {
	type testCase struct {
		Name string

		Before func(workingDirectory string)

		EvaluationCSVFilePaths []string

		ExpectedRecords [][]string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			temporaryPath := t.TempDir()

			if tc.Before != nil {
				tc.Before(temporaryPath)
			}

			for i, evaluationCSVFilePath := range tc.EvaluationCSVFilePaths {
				tc.EvaluationCSVFilePaths[i] = filepath.Join(temporaryPath, evaluationCSVFilePath)
			}

			actualRows, actualErr := RecordsFromEvaluationCSVFiles(tc.EvaluationCSVFilePaths)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedRecords, actualRows)
		})
	}

	validate(t, &testCase{
		Name: "Only header exists",

		Before: func(workingDirectory string) {
			header := `model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code`
			require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.csv"), []byte(header), 0700))
		},

		EvaluationCSVFilePaths: []string{
			"evaluation.csv",
		},

		ExpectedRecords: nil,
	})
	validate(t, &testCase{
		Name: "Single file",

		Before: func(workingDirectory string) {
			content := bytesutil.StringTrimIndentations(`
				model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code
				openrouter/anthropic/claude-2.0,golang,golang/light,write-tests,1,1,1,1,1,1,1,1,1,1
			`)
			require.NoError(t, os.WriteFile(filepath.Join(workingDirectory, "evaluation.csv"), []byte(content), 0700))
		},

		EvaluationCSVFilePaths: []string{
			"evaluation.csv",
		},

		ExpectedRecords: [][]string{
			[]string{
				"openrouter/anthropic/claude-2.0", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1",
			},
		},
	})
	validate(t, &testCase{
		Name: "Multiple files",

		Before: func(workingDirectory string) {
			modelA := filepath.Join(workingDirectory, "modelA")
			modelAFileContent := bytesutil.StringTrimIndentations(`
				model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code
				modelA,golang,golang/light,write-tests,1,1,1,1,1,1,1,1,1,1
				modelA,golang,golang/plain,write-tests,2,2,2,2,2,2,2,2,2,2
			`)
			require.NoError(t, osutil.MkdirAll(modelA))
			require.NoError(t, os.WriteFile(filepath.Join(modelA, "evaluation.csv"), []byte(modelAFileContent), 0700))

			modelB := filepath.Join(workingDirectory, "modelB")
			modelBFileContent := bytesutil.StringTrimIndentations(`
				model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code
				modelB,java,java/light,write-tests,3,3,3,3,3,3,3,3,3,3
				modelB,java,java/plain,write-tests,4,4,4,4,4,4,4,4,4,4
			`)
			require.NoError(t, osutil.MkdirAll(modelB))
			require.NoError(t, os.WriteFile(filepath.Join(modelB, "evaluation.csv"), []byte(modelBFileContent), 0700))
		},

		EvaluationCSVFilePaths: []string{
			filepath.Join("modelA", "evaluation.csv"),
			filepath.Join("modelB", "evaluation.csv"),
		},

		ExpectedRecords: [][]string{
			[]string{"modelA", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
			[]string{"modelA", "golang", "golang/plain", "write-tests", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"},
			[]string{"modelB", "java", "java/light", "write-tests", "3", "3", "3", "3", "3", "3", "3", "3", "3", "3"},
			[]string{"modelB", "java", "java/plain", "write-tests", "4", "4", "4", "4", "4", "4", "4", "4", "4", "4"},
		},
	})
}

func TestEvaluationFileWriteLines(t *testing.T) {
	type testCase struct {
		Name string

		RawRecords [][]string

		ExpectedEvaluationFile string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			var file strings.Builder
			evaluationFile, err := NewEvaluationFile(&file)
			require.NoError(t, err)

			actualErr := evaluationFile.WriteLines(tc.RawRecords)
			require.NoError(t, actualErr)

			assert.Equal(t, bytesutil.StringTrimIndentations(tc.ExpectedEvaluationFile), file.String())
		})
	}

	validate(t, &testCase{
		Name: "No records",

		ExpectedEvaluationFile: `
			model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
		`,
	})
	validate(t, &testCase{
		Name: "Single record",

		RawRecords: [][]string{
			[]string{"modelA", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
		},

		ExpectedEvaluationFile: `
			model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
			modelA,golang,golang/light,write-tests,1,1,1,1,1,1,1,1,1,1,1
		`,
	})
	validate(t, &testCase{
		Name: "Multiple records",

		RawRecords: [][]string{
			[]string{"modelA", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
			[]string{"modelA", "golang", "golang/plain", "write-tests", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"},
			[]string{"modelA", "java", "java/light", "write-tests", "3", "3", "3", "3", "3", "3", "3", "3", "3", "3", "3"},
			[]string{"modelA", "java", "java/plain", "write-tests", "4", "4", "4", "4", "4", "4", "4", "4", "4", "4", "4"},
		},

		ExpectedEvaluationFile: `
			model-id,language,repository,task,score,coverage,files-executed,files-executed-maximum-reachable,generate-tests-for-file-character-count,processing-time,response-character-count,response-no-error,response-no-excess,response-with-code,tests-passing
			modelA,golang,golang/light,write-tests,1,1,1,1,1,1,1,1,1,1,1
			modelA,golang,golang/plain,write-tests,2,2,2,2,2,2,2,2,2,2,2
			modelA,java,java/light,write-tests,3,3,3,3,3,3,3,3,3,3,3
			modelA,java,java/plain,write-tests,4,4,4,4,4,4,4,4,4,4,4
		`,
	})
}

func TestSortRecords(t *testing.T) {
	type testCase struct {
		Name string

		Records [][]string

		ExpectedRecords [][]string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			SortRecords(tc.Records)

			assert.Equal(t, tc.ExpectedRecords, tc.Records)
		})
	}

	validate(t, &testCase{
		Name: "Single record",

		Records: [][]string{
			[]string{"modelA", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
		},

		ExpectedRecords: [][]string{
			[]string{"modelA", "golang", "golang/light", "write-tests", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
		},
	})
	validate(t, &testCase{
		Name: "Multiple records",

		Records: [][]string{
			[]string{"modelD", "languageB", "repositoryA", "taskA", "7", "7", "7", "7", "7", "7", "7", "7", "7", "7"},
			[]string{"modelD", "languageA", "repositoryA", "taskB", "6", "6", "6", "6", "6", "6", "6", "6", "6", "6"},
			[]string{"modelC", "languageA", "repositoryB", "taskB", "5", "5", "5", "5", "5", "5", "5", "5", "5", "5"},
			[]string{"modelC", "languageA", "repositoryB", "taskA", "4", "4", "4", "4", "4", "4", "4", "4", "4", "4"},
			[]string{"modelC", "languageA", "repositoryA", "taskA", "3", "3", "3", "3", "3", "3", "3", "3", "3", "3"},
			[]string{"modelB", "languageA", "repositoryA", "taskA", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"},
			[]string{"modelA", "languageA", "repositoryA", "taskA", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
		},

		ExpectedRecords: [][]string{
			[]string{"modelA", "languageA", "repositoryA", "taskA", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"},
			[]string{"modelB", "languageA", "repositoryA", "taskA", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"},
			[]string{"modelC", "languageA", "repositoryA", "taskA", "3", "3", "3", "3", "3", "3", "3", "3", "3", "3"},
			[]string{"modelC", "languageA", "repositoryB", "taskA", "4", "4", "4", "4", "4", "4", "4", "4", "4", "4"},
			[]string{"modelC", "languageA", "repositoryB", "taskB", "5", "5", "5", "5", "5", "5", "5", "5", "5", "5"},
			[]string{"modelD", "languageA", "repositoryA", "taskB", "6", "6", "6", "6", "6", "6", "6", "6", "6", "6"},
			[]string{"modelD", "languageB", "repositoryA", "taskA", "7", "7", "7", "7", "7", "7", "7", "7", "7", "7"},
		},
	})
}

func TestAssessmentFromRecord(t *testing.T) {
	type testCase struct {
		Name string

		Record []string

		ExpectedAssessments metrics.Assessments
		ExpectedErrText     string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualAssessments, actualErr := assessmentFromRecord(tc.Record)

			if len(tc.ExpectedErrText) > 0 {
				assert.ErrorContains(t, actualErr, tc.ExpectedErrText)
			} else {
				require.NoError(t, actualErr)
			}

			assert.Equal(t, tc.ExpectedAssessments, actualAssessments)
		})
	}

	validate(t, &testCase{
		Name: "Invalid assessments",

		Record: []string{"1", "2", "3"},

		ExpectedErrText: fmt.Sprintf("expected %d assessments, but found %d", len(metrics.AllAssessmentKeysStrings), 3),
	})
	validate(t, &testCase{
		Name: "Valid assessments",

		Record: []string{"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},

		ExpectedAssessments: metrics.Assessments{
			metrics.AssessmentKeyCoverage:                           1,
			metrics.AssessmentKeyFilesExecuted:                      2,
			metrics.AssessmentKeyFilesExecutedMaximumReachable:      3,
			metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 4,
			metrics.AssessmentKeyProcessingTime:                     5,
			metrics.AssessmentKeyResponseCharacterCount:             6,
			metrics.AssessmentKeyResponseNoError:                    7,
			metrics.AssessmentKeyResponseNoExcess:                   8,
			metrics.AssessmentKeyResponseWithCode:                   9,
			metrics.AssessmentKeyTestsPassing:                       10,
		},
	})
}

func TestRecordsToAssessmentsPerModel(t *testing.T) {
	type testCase struct {
		Name string

		Records [][]string

		ExpectedAssessmentsPerModel AssessmentPerModel
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualAssessmentsPerModel, actualErr := RecordsToAssessmentsPerModel(tc.Records)
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedAssessmentsPerModel, actualAssessmentsPerModel)
		})
	}

	validate(t, &testCase{
		Name: "Single record",

		Records: [][]string{
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
		},

		ExpectedAssessmentsPerModel: map[string]metrics.Assessments{
			"modelA": metrics.Assessments{
				metrics.AssessmentKeyCoverage:                           1,
				metrics.AssessmentKeyFilesExecuted:                      2,
				metrics.AssessmentKeyFilesExecutedMaximumReachable:      3,
				metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 4,
				metrics.AssessmentKeyProcessingTime:                     5,
				metrics.AssessmentKeyResponseCharacterCount:             6,
				metrics.AssessmentKeyResponseNoError:                    7,
				metrics.AssessmentKeyResponseNoExcess:                   8,
				metrics.AssessmentKeyResponseWithCode:                   9,
				metrics.AssessmentKeyTestsPassing:                       10,
			},
		},
	})
	validate(t, &testCase{
		Name: "Multiple records from the same model",

		Records: [][]string{
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
		},

		ExpectedAssessmentsPerModel: map[string]metrics.Assessments{
			"modelA": metrics.Assessments{
				metrics.AssessmentKeyCoverage:                           3,
				metrics.AssessmentKeyFilesExecuted:                      6,
				metrics.AssessmentKeyFilesExecutedMaximumReachable:      9,
				metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 12,
				metrics.AssessmentKeyProcessingTime:                     15,
				metrics.AssessmentKeyResponseCharacterCount:             18,
				metrics.AssessmentKeyResponseNoError:                    21,
				metrics.AssessmentKeyResponseNoExcess:                   24,
				metrics.AssessmentKeyResponseWithCode:                   27,
				metrics.AssessmentKeyTestsPassing:                       30,
			},
		},
	})
	validate(t, &testCase{
		Name: "Multiple records from different models",

		Records: [][]string{
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelA", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelB", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelB", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
			[]string{"modelC", "languageB", "repositoryA", "taskA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
		},

		ExpectedAssessmentsPerModel: map[string]metrics.Assessments{
			"modelA": metrics.Assessments{
				metrics.AssessmentKeyCoverage:                           3,
				metrics.AssessmentKeyFilesExecuted:                      6,
				metrics.AssessmentKeyFilesExecutedMaximumReachable:      9,
				metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 12,
				metrics.AssessmentKeyProcessingTime:                     15,
				metrics.AssessmentKeyResponseCharacterCount:             18,
				metrics.AssessmentKeyResponseNoError:                    21,
				metrics.AssessmentKeyResponseNoExcess:                   24,
				metrics.AssessmentKeyResponseWithCode:                   27,
				metrics.AssessmentKeyTestsPassing:                       30,
			},
			"modelB": metrics.Assessments{
				metrics.AssessmentKeyCoverage:                           2,
				metrics.AssessmentKeyFilesExecuted:                      4,
				metrics.AssessmentKeyFilesExecutedMaximumReachable:      6,
				metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 8,
				metrics.AssessmentKeyProcessingTime:                     10,
				metrics.AssessmentKeyResponseCharacterCount:             12,
				metrics.AssessmentKeyResponseNoError:                    14,
				metrics.AssessmentKeyResponseNoExcess:                   16,
				metrics.AssessmentKeyResponseWithCode:                   18,
				metrics.AssessmentKeyTestsPassing:                       20,
			},
			"modelC": metrics.Assessments{
				metrics.AssessmentKeyCoverage:                           1,
				metrics.AssessmentKeyFilesExecuted:                      2,
				metrics.AssessmentKeyFilesExecutedMaximumReachable:      3,
				metrics.AssessmentKeyGenerateTestsForFileCharacterCount: 4,
				metrics.AssessmentKeyProcessingTime:                     5,
				metrics.AssessmentKeyResponseCharacterCount:             6,
				metrics.AssessmentKeyResponseNoError:                    7,
				metrics.AssessmentKeyResponseNoExcess:                   8,
				metrics.AssessmentKeyResponseWithCode:                   9,
				metrics.AssessmentKeyTestsPassing:                       10,
			},
		},
	})
}

func TestWriteMetaInformationRecords(t *testing.T) {
	var file strings.Builder

	err := WriteMetaInformationRecords(&file, [][]string{
		[]string{"provider/modelA", "modelA", "0.1", "0.2", "0.3", "0.4"},
		[]string{"provider/modelB", "modelB", "0.01", "0.02", "0.03", "0.04"},
		[]string{"provider/modelC", "modelC", "0.001", "0.002", "0.003", "0.004"},
		[]string{"provider/modelD", "modelD", "0.0001", "0.0002", "0.0003", "0.0004"},
		[]string{"provider/modelE", "modelE", "0.00001", "0.00002", "0.00003", "0.00004"},
	})
	require.NoError(t, err)

	assert.Equal(t, bytesutil.StringTrimIndentations(`
		model-id,model-name,completion,image,prompt,request
		provider/modelA,modelA,0.1,0.2,0.3,0.4
		provider/modelB,modelB,0.01,0.02,0.03,0.04
		provider/modelC,modelC,0.001,0.002,0.003,0.004
		provider/modelD,modelD,0.0001,0.0002,0.0003,0.0004
		provider/modelE,modelE,0.00001,0.00002,0.00003,0.00004
	`), file.String())
}

func TestMetaInformationRecords(t *testing.T) {
	actualRecords := MetaInformationRecords([]*model.MetaInformation{
		&model.MetaInformation{
			ID:   "provider/modelA",
			Name: "modelA",
			Pricing: model.Pricing{
				Completion: 0.1,
				Image:      0.2,
				Prompt:     0.3,
				Request:    0.4,
			},
		},
		&model.MetaInformation{
			ID:   "provider/modelB",
			Name: "modelB",
			Pricing: model.Pricing{
				Completion: 0.01,
				Image:      0.02,
				Prompt:     0.03,
				Request:    0.04,
			},
		},
		&model.MetaInformation{
			ID:   "provider/modelC",
			Name: "modelC",
			Pricing: model.Pricing{
				Completion: 0.001,
				Image:      0.002,
				Prompt:     0.003,
				Request:    0.004,
			},
		},
		&model.MetaInformation{
			ID:   "provider/modelD",
			Name: "modelD",
			Pricing: model.Pricing{
				Completion: 0.0001,
				Image:      0.0002,
				Prompt:     0.0003,
				Request:    0.0004,
			},
		},
		&model.MetaInformation{
			ID:   "provider/modelE",
			Name: "modelE",
			Pricing: model.Pricing{
				Completion: 0.00001,
				Image:      0.00002,
				Prompt:     0.00003,
				Request:    0.00004,
			},
		},
	})

	assert.ElementsMatch(t, [][]string{
		[]string{"provider/modelA", "modelA", "0.1", "0.2", "0.3", "0.4"},
		[]string{"provider/modelB", "modelB", "0.01", "0.02", "0.03", "0.04"},
		[]string{"provider/modelC", "modelC", "0.001", "0.002", "0.003", "0.004"},
		[]string{"provider/modelD", "modelD", "0.0001", "0.0002", "0.0003", "0.0004"},
		[]string{"provider/modelE", "modelE", "0.00001", "0.00002", "0.00003", "0.00004"},
	}, actualRecords)
}

func TestWriteCSV(t *testing.T) {
	type testCase struct {
		Name string

		Header  []string
		Records [][]string

		ExpectedContent string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			var file strings.Builder
			actualErr := WriteCSV(&file, tc.Header, tc.Records)
			require.NoError(t, actualErr)

			assert.Equal(t, bytesutil.StringTrimIndentations(tc.ExpectedContent), file.String())
		})
	}

	validate(t, &testCase{
		Name: "Single record",

		Header: []string{
			"model-id", "price", "score",
		},

		Records: [][]string{
			[]string{"modelA", "0.01", "1000"},
		},

		ExpectedContent: `
			model-id,price,score
			modelA,0.01,1000
		`,
	})
	validate(t, &testCase{
		Name: "Multiple records",

		Header: []string{
			"model-id", "price", "score",
		},

		Records: [][]string{
			[]string{"modelA", "0.01", "1000"},
			[]string{"modelB", "0.02", "2000"},
			[]string{"modelC", "0.03", "3000"},
		},

		ExpectedContent: `
			model-id,price,score
			modelA,0.01,1000
			modelB,0.02,2000
			modelC,0.03,3000
		`,
	})
}
