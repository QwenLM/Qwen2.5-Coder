package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/avast/retry-go"
	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil"
	"golang.org/x/mod/semver"

	"github.com/symflower/eval-dev-quality/log"
	"github.com/symflower/eval-dev-quality/util"
)

// Ollama holds the "Ollama" tool.
type Ollama struct{}

func init() {
	Register(NewOllama())
}

// NewOllama returns a new Ollama tool.
func NewOllama() Tool {
	return &Ollama{}
}

var _ Tool = &Ollama{}

// ID returns the unique ID of this tool.
func (*Ollama) ID() (id string) {
	return "ollama"
}

// BinaryName returns the name of the tool's binary.
func (*Ollama) BinaryName() string {
	return "ollama" + osutil.BinaryExtension()
}

// OllamaPath holds the file path to the Ollama binary or the command name that should be executed.
var OllamaPath = "ollama" + osutil.BinaryExtension()

// BinaryPath returns the file path of the tool's binary or the command name that should be executed.
// The binary path might also be just the binary name in case the tool is expected to be on the system path.
func (*Ollama) BinaryPath() string {
	return OllamaPath
}

// CheckVersion checks if the tool's version is compatible with the required version.
func (*Ollama) CheckVersion(logger *log.Logger, binaryPath string) (err error) {
	output, err := util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			binaryPath,
			"--version",
		},
	})
	if err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, `unable to verify "Ollama" installation`))
	}

	m := regexp.MustCompile(`version is (\d+\.\d+\.\d+)`).FindStringSubmatch(output)
	if m == nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(errors.New("cannot find version"), output))
	}

	versionPresent := "v" + m[1]
	if !semver.IsValid(versionPresent) {
		return pkgerrors.New(fmt.Sprintf("invalid semantic version string %q", versionPresent))
	}
	versionRequired := "v" + ollamaVersion
	if !semver.IsValid(versionRequired) {
		return pkgerrors.New(fmt.Sprintf("invalid semantic version string %q", versionRequired))
	}

	// Check if binary is compatible.
	if semver.Compare(versionPresent, versionRequired) < 0 {
		return pkgerrors.WithStack(ErrToolVersionOutdated)
	}

	return nil
}

// ollamaVersion holds the version of Ollama required for this revision of the evaluation.
var ollamaVersion = "0.2.8"

// RequiredVersion returns the required version of the tool.
func (*Ollama) RequiredVersion() string {
	return ollamaVersion
}

// Install installs the tool's binary to the given install path.
func (*Ollama) Install(logger *log.Logger, installPath string) (err error) {
	if !osutil.IsLinux() {
		return pkgerrors.WithMessage(pkgerrors.WithStack(ErrUnsupportedOperatingSystem), runtime.GOOS)
	}

	var architectureIdentifier string
	switch a := runtime.GOARCH; a {
	case "amd64":
		architectureIdentifier = "amd64"
	case "arm64":
		architectureIdentifier = "arm64"
	default:
		return pkgerrors.WithStack(fmt.Errorf("unsupported architecture %s", a))
	}

	ollamaDownloadURL := "https://github.com/ollama/ollama/releases/download/v" + ollamaVersion + "/ollama-linux-" + architectureIdentifier
	ollamaInstallPath := filepath.Join(installPath, "ollama")
	logger.Printf("Install \"ollama\" to %s from %s", ollamaInstallPath, ollamaDownloadURL)
	if err := osutil.DownloadFileWithProgress(ollamaDownloadURL, ollamaInstallPath); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("cannot download to %s from %s", ollamaInstallPath, ollamaDownloadURL)))
	}

	// Non-Windows binaries need to be made executable because the executable bit is not set for downloads.
	if !osutil.IsWindows() {
		if _, err := util.CommandWithResult(context.Background(), logger, &util.Command{
			Command: []string{"chmod", "+x", ollamaInstallPath},
		}); err != nil {
			return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("cannot make %s executable", ollamaInstallPath)))
		}
	}

	return nil
}

var (
	// OllamaURL holds the URL to the Ollama service.
	OllamaURL = "http://127.0.0.1:11434"

	// ollamaProcessStates holds Ollama URLs to states of Ollama service processes.
	ollamaProcessStates = map[string]*ollamaProcessState{}
	// ollamaProcessStatesLock holds the lock for accessing Ollama process states.
	ollamaProcessStatesLock sync.Mutex
)

type ollamaProcessState struct {
	// url holds the URL of the Ollama process.
	url string
	// connectionCount holds the amount of connections.
	// When the counter hits `0`, the process will be removed.
	connectionCount uint
	// cleanup holds an optional function to clean up the Ollama process.
	// Can be `nil` in case the process was running already.
	cleanup func()
}

// ollamaProcessStateAdd add a connection to the process states.
func ollamaProcessStateAdd(url string, cleanup func()) {
	state, ok := ollamaProcessStates[url]
	if !ok {
		state = &ollamaProcessState{
			url: url,
		}
		ollamaProcessStates[url] = state
	}
	if cleanup != nil {
		if state.cleanup != nil {
			panic("would overwrite a a clean up function which means the process has been started more than once")
		}

		state.cleanup = cleanup // A process can be started afterwards as well, so make sure it is always cleaned up.
	}
	state.connectionCount++
}

// ollamaProcessStateRemove remove a connection from the process states.
func ollamaProcessStateRemove(url string) {
	state, ok := ollamaProcessStates[url]
	if !ok {
		panic("removed state without being added")
	}

	if state.connectionCount == 0 {
		panic("removed stated more often than added")
	}
	state.connectionCount--
	if state.connectionCount == 0 {
		if state.cleanup != nil {
			state.cleanup()
		}
		delete(ollamaProcessStates, url)
	}
}

// OllamaCheck checks that an Ollama service is running at the given URL.
func OllamaCheck(url string) (err error) {
	if err := retry.Do(
		func() error {
			response, err := http.Get(url)
			if err != nil {
				return pkgerrors.WithStack(err)
			} else if response.StatusCode != http.StatusOK {
				return pkgerrors.WithStack(fmt.Errorf("unexpected status code %d", response.StatusCode))
			}

			body, err := io.ReadAll(response.Body)
			if err != nil {
				return pkgerrors.WithStack(err)
			} else if string(body) != "Ollama is running" {
				return pkgerrors.WithMessage(pkgerrors.WithStack(errors.New("service is not running")), string(body))
			}

			return nil
		},
		retry.Attempts(3),
		retry.Delay(5*time.Second),
		retry.LastErrorOnly(true),
	); err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, "could not detect running Ollama service"))
	}

	return nil
}

// OllamaStart starts an Ollama service if necessary with the given binary connected to the given URL and returns a shutdown function.
func OllamaStart(logger *log.Logger, binaryPath string, url string) (shutdown func() (err error), err error) {
	ollamaProcessStatesLock.Lock()
	defer ollamaProcessStatesLock.Unlock()

	// Check if the URL has already a running service.
	if err := OllamaCheck(url); err == nil {
		logger.Printf("Reusing existing Ollama service on %q", url)

		ollamaProcessStateAdd(url, nil)

		return func() (err error) {
			ollamaProcessStateRemove(url)

			return nil
		}, nil
	}

	ctx, cancel := context.WithCancel(context.Background())

	logger.Printf("Starting new Ollama service on %q using %s", url, binaryPath)

	var serverError error
	var serverWaitGroup sync.WaitGroup
	serverWaitGroup.Add(1)
	go func() {
		defer serverWaitGroup.Done()

		if output, err := util.CommandWithResult(ctx, logger, &util.Command{
			Command: []string{
				binaryPath,
				"serve",
			},

			Env: map[string]string{
				"OLLAMA_HOST": url,
			},
		}); err != nil && !strings.Contains(err.Error(), "killed") {
			logger.Printf("could not start Ollama service: %s\n%s", err, output)
			serverError = pkgerrors.WithStack(pkgerrors.WithMessage(err, output))
		}
	}()

	if err := OllamaCheck(url); err != nil {
		cancel()
		serverWaitGroup.Wait()

		return nil, err
	}

	ollamaProcessStateAdd(url, func() {
		cancel()
		serverWaitGroup.Wait()
	})

	return func() error {
		ollamaProcessStatesLock.Lock()
		defer ollamaProcessStatesLock.Unlock()

		ollamaProcessStateRemove(url)

		return serverError
	}, nil
}

// OllamaModels returns which models are available to be queried.
func OllamaModels(ollamaURL string) (modelNames []string, err error) {
	var localModels struct {
		Models []struct {
			Name string `json:"name"`
		} `json:"models"`
	}

	ollamaURL, err = url.JoinPath(ollamaURL, "api", "tags")
	if err != nil {
		panic(err)
	}
	response, err := http.Get(ollamaURL)
	if err != nil {
		return nil, pkgerrors.WithMessage(pkgerrors.WithStack(err), ollamaURL)
	}
	defer func() {
		if e := response.Body.Close(); e != nil {
			e = pkgerrors.WithStack(e)
			if err == nil {
				err = e
			} else {
				err = errors.Join(err, e)
			}
		}
	}()

	if err := json.NewDecoder(response.Body).Decode(&localModels); err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	modelNames = make([]string, len(localModels.Models))
	for i, model := range localModels.Models {
		modelNames[i] = model.Name
	}

	return modelNames, nil
}

// OllamaPull pulls a model.
func OllamaPull(logger *log.Logger, binaryPath string, url string, modelName string) (err error) {
	_, err = util.CommandWithResult(context.Background(), logger, &util.Command{
		Command: []string{
			binaryPath,
			"pull", modelName,
		},

		Env: map[string]string{
			"OLLAMA_HOST": url,
		},
	})

	return err
}

// OllamaLoad loads a model into memory.
func OllamaLoad(ollamaURL string, modelName string) (err error) {
	ollamaURL, err = url.JoinPath(ollamaURL, "api", "generate")
	if err != nil {
		panic(err)
	}

	// Send an empty request with negative keep-alive time to load the model and keep it loaded indefinitely. https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately
	response, err := http.Post(ollamaURL, "application/json", bytes.NewBufferString(fmt.Sprintf("{\"model\":%q,\"keep_alive\":-1}", modelName)))
	if err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("error loading model %q to Ollama server at %q", modelName, ollamaURL)))
	} else if response.StatusCode != http.StatusOK {
		return pkgerrors.Errorf("unexpected status code when trying to load model %q to Ollama server at %q: %d", modelName, ollamaURL, response.StatusCode)
	}

	return nil
}

// OllamaUnload unloads a model from memory.
func OllamaUnload(ollamaURL string, modelName string) (err error) {
	ollamaURL, err = url.JoinPath(ollamaURL, "api", "generate")
	if err != nil {
		panic(err)
	}

	// Send an empty request with zero keep-alive time to unload the model. https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately
	response, err := http.Post(ollamaURL, "application/json", bytes.NewBufferString(fmt.Sprintf("{\"model\":%q,\"keep_alive\":0}", modelName)))
	if err != nil {
		return pkgerrors.WithStack(pkgerrors.WithMessage(err, fmt.Sprintf("error unloading model %q to Ollama server at %q", modelName, ollamaURL)))
	} else if response.StatusCode != http.StatusOK {
		return pkgerrors.Errorf("unexpected status code when trying to unloading model %q to Ollama server at %q: %d", modelName, ollamaURL, response.StatusCode)
	}

	return nil
}
