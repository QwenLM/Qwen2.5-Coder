package llm

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"
	"time"

	"github.com/avast/retry-go"
	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/evaluate/metrics"
	evaluatetask "github.com/symflower/eval-dev-quality/evaluate/task"
	"github.com/symflower/eval-dev-quality/language"
	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/model"
	"github.com/symflower/eval-dev-quality/model/llm/prompt"
	"github.com/symflower/eval-dev-quality/provider"
)

// Model represents a LLM model accessed via a provider.
type Model struct {
	// provider is the client to query the LLM model.
	provider provider.Query
	// model holds the identifier for the LLM model.
	model string

	// queryAttempts holds the number of query attempts to perform when a model request errors in the process of solving a task.
	queryAttempts uint

	// metaInformation holds a model meta information.
	metaInformation *model.MetaInformation
}

// NewModel returns an LLM model corresponding to the given identifier which is queried via the given provider.
func NewModel(provider provider.Query, modelIdentifier string) *Model {
	return &Model{
		provider: provider,
		model:    modelIdentifier,

		queryAttempts: 1,
	}
}

// NewModelWithMetaInformation returns a LLM model with meta information corresponding to the given identifier which is queried via the given provider.
func NewModelWithMetaInformation(provider provider.Query, modelIdentifier string, metaInformation *model.MetaInformation) *Model {
	return &Model{
		provider: provider,
		model:    modelIdentifier,

		queryAttempts: 1,

		metaInformation: metaInformation,
	}
}

// MetaInformation returns the meta information of a model.
func (m *Model) MetaInformation() (metaInformation *model.MetaInformation) {
	return m.metaInformation
}

// llmSourceFilePromptContext is the context for template for generating an LLM test generation prompt.
type llmSourceFilePromptContext struct {
	// Language holds the programming language name.
	Language language.Language

	// Code holds the source code of the file.
	Code string
	// FilePath holds the file path of the file.
	FilePath string
	// ImportPath holds the import path of the file.
	ImportPath string
}

// llmGenerateTestForFilePromptTemplate is the template for generating an LLM test generation prompt.
var llmGenerateTestForFilePromptTemplate = template.Must(template.New("model-llm-generate-test-for-file-prompt").Parse(bytesutil.StringTrimIndentations(`
	Given the following {{ .Language.Name }} code file "{{ .FilePath }}" with package "{{ .ImportPath }}", provide a test file for this code{{ with $testFramework := .Language.TestFramework }} with {{ $testFramework }} as a test framework{{ end }}.
	The tests should produce 100 percent code coverage and must compile.
	The response must contain only the test code in a fenced code block and nothing else.

	` + "```" + `{{ .Language.ID }}
	{{ .Code }}
	` + "```" + `
`)))

// llmGenerateTestForFilePrompt returns the prompt for generating an LLM test generation.
func llmGenerateTestForFilePrompt(data *llmSourceFilePromptContext) (message string, err error) {
	// Use Linux paths even when running the evaluation on Windows to ensure consistency in prompting.
	data.FilePath = filepath.ToSlash(data.FilePath)
	data.Code = strings.TrimSpace(data.Code)

	var b strings.Builder
	if err := llmGenerateTestForFilePromptTemplate.Execute(&b, data); err != nil {
		return "", pkgerrors.WithStack(err)
	}

	return b.String(), nil
}

// llmCodeRepairSourceFilePromptContext is the template context for a code repair LLM prompt.
type llmCodeRepairSourceFilePromptContext struct {
	// llmSourceFilePromptContext holds the context for a source file prompt.
	llmSourceFilePromptContext

	// Mistakes holds the list of compilation errors of a package.
	Mistakes []string
}

// llmCodeRepairSourceFilePromptTemplate is the template for generating an LLM code repair prompt.
var llmCodeRepairSourceFilePromptTemplate = template.Must(template.New("model-llm-code-repair-source-file-prompt").Parse(bytesutil.StringTrimIndentations(`
	Given the following {{ .Language.Name }} code file "{{ .FilePath }}" with package "{{ .ImportPath }}" and a list of compilation errors, modify the code such that the errors are resolved.
	The response must contain only the source code in a fenced code block and nothing else.

	` + "```" + `{{ .Language.ID }}
	{{ .Code }}
	` + "```" + `

	The list of compilation errors is the following:{{ range .Mistakes }}
	- {{.}}{{ end }}
`)))

// llmCodeRepairSourceFilePrompt returns the prompt to code repair a source file.
func llmCodeRepairSourceFilePrompt(data *llmCodeRepairSourceFilePromptContext) (message string, err error) {
	// Use Linux paths even when running the evaluation on Windows to ensure consistency in prompting.
	data.FilePath = filepath.ToSlash(data.FilePath)
	data.Code = strings.TrimSpace(data.Code)

	var b strings.Builder
	if err := llmCodeRepairSourceFilePromptTemplate.Execute(&b, data); err != nil {
		return "", pkgerrors.WithStack(err)
	}

	return b.String(), nil
}

// llmTranspileSourceFilePromptContext is the template context for a transpilation LLM prompt.
type llmTranspileSourceFilePromptContext struct {
	// llmSourceFilePromptContext holds the context for a source file prompt.
	llmSourceFilePromptContext

	// OriginLanguage holds the language we are transpiling from.
	OriginLanguage language.Language
	// OriginFileContent holds the code we want to transpile.
	OriginFileContent string
}

// llmTranspileSourceFilePromptTemplate is the template for generating an LLM transpilation prompt.
var llmTranspileSourceFilePromptTemplate = template.Must(template.New("model-llm-transpile-source-file-prompt").Parse(bytesutil.StringTrimIndentations(`
	Given the following {{ .OriginLanguage.Name }} code file, transpile it into a {{ .Language.Name }} code file.
	The response must contain only the transpiled {{ .Language.Name }} source code in a fenced code block and nothing else.

	` + "```" + `{{ .OriginLanguage.ID }}
	{{ .OriginFileContent }}
	` + "```" + `

	The transpiled {{ .Language.Name }} code file must have the package "{{ .ImportPath }}" and the following signature:

	` + "```" + `{{ .Language.ID }}
	{{ .Code }}
	` + "```" + `
`)))

// llmTranspileSourceFilePrompt returns the prompt to transpile a source file.
func llmTranspileSourceFilePrompt(data *llmTranspileSourceFilePromptContext) (message string, err error) {
	// Use Linux paths even when running the evaluation on Windows to ensure consistency in prompting.
	data.FilePath = filepath.ToSlash(data.FilePath)
	data.Code = strings.TrimSpace(data.Code)
	data.OriginFileContent = strings.TrimSpace(data.OriginFileContent)

	var b strings.Builder
	if err := llmTranspileSourceFilePromptTemplate.Execute(&b, data); err != nil {
		return "", pkgerrors.WithStack(err)
	}

	return b.String(), nil
}

var _ model.Model = (*Model)(nil)

// ID returns the unique ID of this model.
func (m *Model) ID() (id string) {
	return m.model
}

var _ model.CapabilityWriteTests = (*Model)(nil)

// WriteTests generates test files for the given implementation file in a repository.
func (m *Model) WriteTests(ctx model.Context) (assessment metrics.Assessments, err error) {
	data, err := os.ReadFile(filepath.Join(ctx.RepositoryPath, ctx.FilePath))
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	fileContent := strings.TrimSpace(string(data))

	importPath := ctx.Language.ImportPath(ctx.RepositoryPath, ctx.FilePath)

	request, err := llmGenerateTestForFilePrompt(&llmSourceFilePromptContext{
		Language: ctx.Language,

		Code:       fileContent,
		FilePath:   ctx.FilePath,
		ImportPath: importPath,
	})
	if err != nil {
		return nil, err
	}

	response, duration, err := m.query(ctx.Logger, request)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	assessment, testContent, err := prompt.ParseResponse(response)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	assessment[metrics.AssessmentKeyProcessingTime] = uint64(duration.Milliseconds())
	assessment[metrics.AssessmentKeyResponseCharacterCount] = uint64(len(response))
	assessment[metrics.AssessmentKeyGenerateTestsForFileCharacterCount] = uint64(len(testContent))

	testFilePath := ctx.Language.TestFilePath(ctx.RepositoryPath, ctx.FilePath)
	if err := os.MkdirAll(filepath.Join(ctx.RepositoryPath, filepath.Dir(testFilePath)), 0755); err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	if err := os.WriteFile(filepath.Join(ctx.RepositoryPath, testFilePath), []byte(testContent), 0644); err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	return assessment, nil
}

func (m *Model) query(logger *log.Logger, request string) (response string, duration time.Duration, err error) {
	if err := retry.Do(
		func() error {
			logger.Printf("Querying model %q with:\n%s", m.ID(), string(bytesutil.PrefixLines([]byte(request), []byte("\t"))))
			start := time.Now()
			response, err = m.provider.Query(context.Background(), m.model, request)
			if err != nil {
				return err
			}
			duration = time.Since(start)
			logger.PrintWith(fmt.Sprintf("Model %q responded (%d ms) with:\n%s", m.ID(), duration.Milliseconds(), string(bytesutil.PrefixLines([]byte(response), []byte("\t")))), log.Attribute(log.AttributeKeyArtifact, "response"))

			return nil
		},
		retry.Attempts(m.queryAttempts),
		retry.Delay(5*time.Second),
		retry.DelayType(retry.BackOffDelay),
		retry.LastErrorOnly(true),
		retry.OnRetry(func(n uint, err error) {
			logger.Printf("Attempt %d/%d: %s", n+1, m.queryAttempts, err)
		}),
	); err != nil {
		return "", 0, err
	}

	return response, duration, nil
}

var _ model.CapabilityRepairCode = (*Model)(nil)

// RepairCode queries the model to repair a source code with compilation error.
func (m *Model) RepairCode(ctx model.Context) (assessment metrics.Assessments, err error) {
	codeRepairArguments, ok := ctx.Arguments.(*evaluatetask.TaskArgumentsCodeRepair)
	if !ok {
		return nil, pkgerrors.Errorf("unexpected type %#v", ctx.Arguments)
	}

	assessment = map[metrics.AssessmentKey]uint64{}

	data, err := os.ReadFile(filepath.Join(ctx.RepositoryPath, ctx.FilePath))
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	fileContent := strings.TrimSpace(string(data))

	importPath := ctx.Language.ImportPath(ctx.RepositoryPath, ctx.FilePath)

	request, err := llmCodeRepairSourceFilePrompt(&llmCodeRepairSourceFilePromptContext{
		llmSourceFilePromptContext: llmSourceFilePromptContext{
			Language: ctx.Language,

			Code:       fileContent,
			FilePath:   ctx.FilePath,
			ImportPath: importPath,
		},

		Mistakes: codeRepairArguments.Mistakes,
	})
	if err != nil {
		return nil, err
	}

	response, duration, err := m.query(ctx.Logger, request)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	assessment, sourceFileContent, err := prompt.ParseResponse(response)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	assessment[metrics.AssessmentKeyProcessingTime] = uint64(duration.Milliseconds())
	assessment[metrics.AssessmentKeyResponseCharacterCount] = uint64(len(response))
	assessment[metrics.AssessmentKeyGenerateTestsForFileCharacterCount] = uint64(len(sourceFileContent))

	err = os.WriteFile(filepath.Join(ctx.RepositoryPath, ctx.FilePath), []byte(sourceFileContent), 0644)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	return assessment, nil
}

var _ model.CapabilityTranspile = (*Model)(nil)

// Transpile queries the model to transpile source code to another language.
func (m *Model) Transpile(ctx model.Context) (assessment metrics.Assessments, err error) {
	transpileArguments, ok := ctx.Arguments.(*evaluatetask.TaskArgumentsTranspile)
	if !ok {
		return nil, pkgerrors.Errorf("unexpected type %#v", ctx.Arguments)
	}

	data, err := os.ReadFile(filepath.Join(ctx.RepositoryPath, ctx.FilePath))
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	stubFileContent := strings.TrimSpace(string(data))

	data, err = os.ReadFile(filepath.Join(ctx.RepositoryPath, transpileArguments.OriginFilePath))
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	originFileContent := strings.TrimSpace(string(data))

	importPath := ctx.Language.ImportPath(ctx.RepositoryPath, ctx.FilePath)

	request, err := llmTranspileSourceFilePrompt(&llmTranspileSourceFilePromptContext{
		llmSourceFilePromptContext: llmSourceFilePromptContext{
			Language: ctx.Language,

			Code:       stubFileContent,
			FilePath:   ctx.FilePath,
			ImportPath: importPath,
		},

		OriginLanguage:    transpileArguments.OriginLanguage,
		OriginFileContent: originFileContent,
	})
	if err != nil {
		return nil, err
	}

	response, duration, err := m.query(ctx.Logger, request)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	assessment, originFileContent, err = prompt.ParseResponse(response)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}
	assessment[metrics.AssessmentKeyProcessingTime] = uint64(duration.Milliseconds())
	assessment[metrics.AssessmentKeyResponseCharacterCount] = uint64(len(response))
	assessment[metrics.AssessmentKeyGenerateTestsForFileCharacterCount] = uint64(len(originFileContent))

	err = os.WriteFile(filepath.Join(ctx.RepositoryPath, ctx.FilePath), []byte(originFileContent), 0644)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	return assessment, nil
}

var _ model.SetQueryAttempts = (*Model)(nil)

// SetQueryAttempts sets the number of query attempts to perform when a model request errors in the process of solving a task.
func (m *Model) SetQueryAttempts(queryAttempts uint) {
	m.queryAttempts = queryAttempts
}
