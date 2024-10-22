## Evaluation for HumanEval(+) and MBPP(+)

This folder contains the code and scripts to evaluate the performance of the **QwenCoder-2.5** series models on [**EvalPlus**](https://github.com/evalplus/evalplus) benchmark, which includes HumanEval(+) and MBPP(+) datasets. These datasets are designed to test code generation capabilities under varied conditions.


### 1. Setup

Please refer to [**EvalPlus**](https://github.com/evalplus/evalplus) for detailed setup instructions. Install the required packages using:

```bash
pip install evalplus --upgrade
pip install -r requirements.txt
```

### 2. Inference and Evaluation

We utilize 8xA100 GPUs for this benchmark. The following scripts are used to run the inference and evaluations:

```bash
bash test.sh
```
