# LiveCodeBench for Reasoning Models

This is a customized version of [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) specifically designed for reasoning models, such as **QwQ-32B-Preview**.

## Getting Started

### 1. Download the Dataset

```bash
huggingface-cli download --repo-type dataset livecodebench/code_generation_lite --local-dir code_generation_lite
```

### 2. Inference and Evaluation

Before running the inference and evaluation, ensure that you have configured the following in the `scripts/evaluate_qwq.sh` script:

- `PYTHON_BIN`: Set the path to your Python binary.
- `MODEL_DIR`: Set the path to the **QwQ-32B-Preview** model directory.

Run the following command to perform inference and evaluation:

```bash
bash scripts/evaluate_qwq.sh
```

The results of the inference will be saved in the `lcb_result/qwq-32b-preview` directory. We have included results obtained from the **Qwen/QwQ-32B-Preview** model.

## Modifications

1. A new chat template for **Qwen/QwQ-32B-Preview**.
2. Adjusted the prompt template to allow the model to think more freely (removed `You will NOT return anything except for the program`).
3. Implemented a filter to select examples within a specified date range.
4. Modified the `extract_code` function to select the last code block according to the updated prompt template.

## Acknowledgments

A big thank you to the [LiveCodeBench](https://livecodebench.github.io/leaderboard.html) team for their valuable contributions to the open-source community.