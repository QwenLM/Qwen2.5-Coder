# DevQualityEval

An evaluation benchmark 📈 and framework to compare and evolve the quality of code generation of LLMs.

This repository gives developers of LLMs (and other code generation tools) a standardized benchmark and framework to improve real-world usage in the software development domain and provides users of LLMs with metrics and comparisons to check if a given LLM is useful for their tasks.

The [latest results](docs/reports/v0.5.0) are discussed in a deep dive: [DeepSeek v2 Coder and Claude 3.5 Sonnet are more cost-effective at code generation than GPT-4o!](https://symflower.com/en/company/blog/2024/dev-quality-eval-v0.5.0-deepseek-v2-coder-and-claude-3.5-sonnet-beat-gpt-4o-for-cost-effectiveness-in-code-generation/)

![Scatter plot that shows the best LLMs aligned with their capability on the y-axis to costs with a logarithmic scale on the x-axis of the v0.5.0 deep dive.](https://symflower.com/en/company/blog/2024/dev-quality-eval-v0.5.0-deepseek-v2-coder-and-claude-3.5-sonnet-beat-gpt-4o-for-cost-effectiveness-in-code-generation/images/header.png)

## Installation

[Install Git](https://git-scm.com/downloads), [install Go](https://go.dev/doc/install), and then execute the following commands:

```bash
git clone https://github.com/symflower/eval-dev-quality.git
cd eval-dev-quality
go install -v github.com/symflower/eval-dev-quality/cmd/eval-dev-quality
```

You can now use the `eval-dev-quality` binary to [execute the benchmark](#usage).

## Usage

> REMARK This project does not execute the LLM generated code in a sandbox by default. Make sure that you are running benchmarks only inside of an isolated environment, e.g. by using `--runtime docker`.

The easiest-to-use LLM provider is [openrouter.ai](https://openrouter.ai/). You need to create an [access key](https://openrouter.ai/keys) and save it in an environment variable:

```bash
export PROVIDER_TOKEN=openrouter:${your-key}
```

Then you can run all benchmark tasks on all models and repositories:

```bash
eval-dev-quality evaluate
```

The output of the commands is a detailed log of all the requests and responses to the models and of all the commands executed. After the execution, you can find the final result saved to the file `evaluation.csv`.

See `eval-dev-quality --help` and especially `eval-dev-quality evaluate --help` for options.

### Example usage: Evaluate only one or more models

In the case you only want to evaluate only one or more models you can use the `--model` option to define a model you want to use. You can use this option with as many models as you want.

Executing the following output:

```bash
eval-dev-quality evaluate --model=openrouter/meta-llama/llama-3-70b-instruct
```

Should return an evaluation log similar to this:

<details>
<summary>Log for the above command.</summary>

````plain
2024/05/02 10:01:58 Writing results to evaluation-2024-05-02-10:01:58
2024/05/02 10:01:58 Checking that models and languages can be used for evaluation
2024/05/02 10:01:58 Evaluating model "openrouter/meta-llama/llama-3-70b-instruct" using language "golang" and repository "golang/plain"
2024/05/02 10:01:58 Querying model "openrouter/meta-llama/llama-3-70b-instruct" with:
        Given the following Go code file "plain.go" with package "plain", provide a test file for this code.
        The tests should produce 100 percent code coverage and must compile.
        The response must contain only the test code and nothing else.

        ```golang
        package plain

        func plain() {
                return // This does not do anything but it gives us a line to cover.
        }
        ```
2024/05/02 10:02:00 Model "openrouter/meta-llama/llama-3-70b-instruct" responded with:
        ```go
        package plain

        import "testing"

        func TestPlain(t *testing.T) {
                plain()
        }
        ```
2024/05/02 10:02:00 $ symflower test --language golang --workspace /tmp/eval-dev-quality2330727502/plain
Checking for updates
There is a new version of symflower available! Please run `symflower update`.
=== RUN   TestPlain
--- PASS: TestPlain (0.00s)
PASS
coverage: 100.0% of statements
ok      plain   0.002s  coverage: 100.0% of statements

DONE 1 tests in 0.348s
2024/05/02 10:02:01 Evaluated model "openrouter/meta-llama/llama-3-70b-instruct" using language "golang" and repository "golang/plain": encountered 0 problems: []
2024/05/02 10:02:01 Evaluating model "openrouter/meta-llama/llama-3-70b-instruct" using language "java" and repository "java/plain"
2024/05/02 10:02:01 Querying model "openrouter/meta-llama/llama-3-70b-instruct" with:
        Given the following Java code file "src/main/java/com/eval/Plain.java" with package "com.eval", provide a test file for this code with JUnit 5 as a test framework.
        The tests should produce 100 percent code coverage and must compile.
        The response must contain only the test code and nothing else.

        ```java
        package com.eval;

        class Plain {
            static void plain() {
            }
        }
        ```
2024/05/02 10:02:02 Model "openrouter/meta-llama/llama-3-70b-instruct" responded with:
        ```java
        package com.eval;

        import org.junit.jupiter.api.Test;

        import static org.junit.jupiter.api.Assertions.assertFalse;
        import static org.junit.jupiter.api.Assertions.assertTrue;

        public class PlainTest {
            @Test
            void testPlain() {
                Plain.plain();
                // Since the method is empty, we can only assert that it doesn't throw an exception
                assertTrue(true);
            }
        }
        ```
2024/05/02 10:02:02 $ symflower test --language java --workspace /tmp/eval-dev-quality1094965069/plain
Total coverage 100.000000%
2024/05/02 10:02:09 Evaluated model "openrouter/meta-llama/llama-3-70b-instruct" using language "java" and repository "java/plain": encountered 0 problems: []
2024/05/02 10:02:09 Evaluating models and languages
2024/05/02 10:02:09 Evaluation score for "openrouter/meta-llama/llama-3-70b-instruct" ("code-no-excess"): score=12, coverage=2, files-executed=2, response-no-error=2, response-no-excess=2, response-not-empty=2, response-with-code=2
````

</details>

The execution by default also creates a report file `REPORT.md` that contains additional evaluation results and links to individual result files.

# Containerized use

## Notes

The following parameters do have a special behavior when using a containerized runtime.

- `--configuration`: Passing configuration files to the docker runtime is currently unsupported.
- `--testdata`: The check if the path exists is ignored on the host system but still enforced inside the container because the paths of the host and inside the container might differ.

## Docker

### Setup

Ensure that docker is installed on the system.

### Build or pull the image

```bash
docker build . -t eval-dev-quality:dev
```

```bash
docker pull ghcr.io/symflower/eval-dev-quality:main
```

### Run the evaluation either with the built or pulled image

The following command will run the model `symflower/symbolic-execution` and stores the the results of the run inside the local directory `evaluation`.

```bash
eval-dev-quality evaluate --runtime docker --runtime-image eval-dev-quality:dev --model symflower/symbolic-execution
```

Omitting the `--runtime-image` parameter will default to the image from the `main` branch. `ghcr.io/symflower/eval-dev-quality:main`

```bash
eval-dev-quality evaluate --runtime docker --model symflower/symbolic-execution
```

## Kubernetes

Please check the [Kubernetes](./docs/kubernetes/README.md) documentation.

## Providers

The following providers (for model inference) are currently supported:

- [OpenRouter](https://openrouter.ai/)
  - register API key via: `--tokens=openrouter:${key}` or environment `PROVIDER_TOKEN=openrouter:${key}`
  - select models via the `openrouter` prefix, i.e. `--model openrouter/meta-llama/llama-3.1-8b-instruct`
- [Ollama](https://ollama.com/)
  - the evaluation listens to the default Ollama port (`11434`), or will attempt to start an Ollama server if you have the `ollama` binary on your path
  - select models via the `ollama` prefix, i.e. `--model ollama/llama3.1:8b`
- [OpenAI API](https://platform.openai.com/docs/api-reference/chat/create)
  - use any inference endpoint that conforms to the OpenAI chat completion API
  - register the endpoint using `--urls=custom-${name}:${endpoint-url}` (mind the `custom-` prefix) or using the environment `PROVIDER_URL`
  - ensure to register your API key to the same `custom-${name}`
  - select models via the `custom-${name}` prefix
  - example for [fireworks.ai](https://fireworks.ai/): `eval-dev-quality evaluate --urls=custom-fw:https://api.fireworks.ai/inference/v1 --tokens=custom-fw:${your-api-token} --model custom-fw/accounts/fireworks/models/llama-v3p1-8b-instruct`

# The Evaluation

With `DevQualityEval` we answer answer the following questions:

- Which LLMs can solve software development tasks?
- How good is the quality of their results?

Programming is a non-trivial profession. Even writing tests for an empty function requires substantial knowledge of the used programming language and its conventions. We already investigated this challenge and how many LLMs failed at it in our [first `DevQualityEval` report](https://symflower.com/en/company/blog/2024/can-ai-test-a-go-function-that-does-nothing/#why-evaluate-an-empty-function). This highlights the need for a **benchmarking framework for evaluating AI performance on software development task solving**.

## Setup

The models evaluated in `DevQualityEval` have to solve programming tasks, not only in one, but in multiple programming languages.
Every task is a well-defined, abstract challenge that the model needs to complete (for example: writing a unit test for a given function).
Multiple concrete cases (or candidates) exist for a given task that each represent an actual real-world example that a model has to solve (i.e. for function `abc() {...` write a unit test).

Completing a task-case rewards points depending on the quality of the result. This, of course, depends on which criteria make the solution to a task a "good" solution, but the general rule is that the more points - the better. For example, the unit tests generated by a model might actually be compiling, yielding points that set the model apart from other models that generate only non-compiling code.

### Running specific tasks

### Via repository

Each repository can contain a configuration file `repository.json` in its root directory specifying a list of tasks which are supposed to be run for this repository.

```json
{
  "tasks": ["write-tests"]
}
```

For the evaluation of the repository only the specified tasks are executed. If no `repository.json` file exists, all tasks are executed.

## Tasks

### Task: Test Generation

Test generation is the task of generating a test suite for a given source code example.

The great thing about test generation is that it is easy to automatically check if the result is correct.
It needs to compile and provide 100% coverage. A model can only write such tests if it understands the source, so implicitly we are evaluating the language understanding of a LLM.

On a high level, `DevQualityEval` asks the model to produce tests for an example case, saves the response to a file and tries to execute the resulting tests together with the original source code.

#### Cases

Currently, the following cases are available for this task:

- Java
  - [`java/plain`](testdata/java/plain)
  - [`java/light`](testdata/java/light)
- Go
  - [`golang/plain`](testdata/golang/plain)
  - [`golang/light`](testdata/golang/light)
- Ruby
  - [`ruby/plain`](testdata/ruby/plain)
  - [`ruby/light`](testdata/ruby/light)

### Task: Code Repair

Code repair is the task of repairing source code with compilation errors.

For this task, we introduced the `mistakes` repository, which includes examples of source code with compilation errors. Each example is isolated in its own package, along with a valid test suite. We compile each package in the `mistakes` repository and provide the LLM's with both the source code and the list of compilation errors. The LLM's response is then validated with the predefined test suite.

#### Cases

Currently, the following cases are available for this task:

- Java
  - [`java/mistakes`](testdata/java/mistakes)
- Go
  - [`golang/mistakes`](testdata/golang/mistakes)
- Ruby
  - [`golang/mistakes`](testdata/ruby/mistakes)

### Task: Transpile

Transpile is the task of converting source code from one language to another.

The test data repository for this task consists of several packages. At the root of each package, there must be a folder called `implementation` containing the **implementation files** (one per origin language), which are to be transpiled from. Each package must also contain a source file with a stub (a function signature so the LLM's know the signature of the function they need to generate code for) and a valid test suite. The LLM's response is then validated with the predefined test suite.

#### Cases

Currently, the following cases are available for this task:

- Java
  - [`java/transpile`](testdata/java/transpile)
- Go
  - [`golang/transpile`](testdata/golang/transpile)
- Ruby
  - [`golang/transpile`](testdata/ruby/transpile)

### Reward Points

Currently, the following points are awarded:

- `response-no-error`: `+1` if the response did not encounter an error
- `response-not-empty`: `+1` if the response is not empty
- `response-with-code`: `+1` if the response contained source code
- `compiled`: `+1` if the source code compiled
- `statement-coverage-reached`: `+10` for each coverage object of executed code (disabled for `transpile` and `code-repair`, as models are writing the implementation code and could just add arbitrary statements to receive a higher score)
- `no-excess`: `+1` if the response did not contain more content than requested
- `passing-tests`: `+10` for each test that is passing (disabled for `write-test`, as models are writing the test code and could just add arbitrary test cases to receive a higher score)

## Results

When interpreting the results, please keep the following in mind that LLMs are nondeterministic, so results may vary.

Furthermore, the choice of a "best" model for a task might depend on additional factors. For example, the needed computing resources or query cost of a cloud LLM endpoint differs greatly between models. Also, the open availability of model weights might change one's model choice. So in the end, there is no "perfect" overall winner, only the "perfect" model for a specific use case.

# How to extend the benchmark?

If you want to add new files to existing language repositories or new repositories to existing languages, [install the evaluation binary](#installation) of this repository and you are good to go.

To add new tasks to the benchmark, add features, or fix bugs, you'll need a development environment. The development environment comes with this repository and can be installed by executing `make install-all`. Then you can run `make` to see the documentation for all the available commands.

# How to contribute?

First of all, thank you for thinking about contributing! There are multiple ways to contribute:

- Add more files to existing language repositories.
- Add more repositories to languages.
- Implement another language and add repositories for it.
- Implement new tasks for existing languages and repositories.
- Add more features and fix bugs in the evaluation, development environment, or CI: [best to have a look at the list of issues](https://github.com/symflower/eval-dev-quality/issues).

If you want to contribute but are unsure how: [create a discussion](https://github.com/symflower/eval-dev-quality/discussions) or write us directly at [markus.zimmermann@symflower.com](mailto:markus.zimmermann@symflower.com).

# When and how to release?

## Publishing Content

Releasing a new version of `DevQualityEval` and publishing content about it are two different things!
But, we plan development and releases to be "content-driven", i.e. we work on / add features that are interesting to write about (see "Release Roadmap" below).
Hence, for every release we also publish a deep dive blog post with our latest features and findings.
Our published content is aimed at giving insight into our work and educating the reader.

- new features that add value (i.e. change / add to the scoring / ranking) are always publish-worthy / release-worthy
- new tools / models are very often not release-worthy but still publish-worthy (i.e. how is new model `XYZ` doing in the benchmark)
- insights, learnings, problems, surprises, achieved goals and experiments are always publish-worthy
  - they need to be documented for later publishing (in a deep-dive blog post)
  - they can also be published right away already (depending on the nature of the finding) as a small report / post

❗ Always publish / release / journal early:

- if something works, but is not merged yet: publish about it already
- if some feature is merged that is release-worthy, but we were planning on adding other things to that release: release anyways
- if something else is publish-worth: at least write down a few bullet-points immediately why it is interesting, including examples

## Release Roadmap

The `main` branch is always stable and could theoretically be used to form a new release at any given time.
To avoid having hundreds of releases for every merge to `main`, we perform releases only when a (group of) publish-worthy feature(s) or important bugfix(es) is merged (see "Publishing Content" above).

Therefore, we plan releases in special `Roadmap for vX.Y.Z` issues.
Such an issue contains a current list of publish-worthy goals that must be met for that release, a `TODO` section with items not planned for the current but a future release, and instructions on how issues / PRs / tasks need to be groomed and what needs to be done for a release to happen.

The issue template for roadmap issues can be found at [`.github/ISSUE_TEMPLATE/roadmap.md`](.github/ISSUE_TEMPLATE/roadmap.md)
