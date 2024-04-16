## Evaluation for HumanEval(+) and MBPP(+)

This folder contains the code and scripts to evaluate the performance of the **CodeQwen1.5** series models on [**EvalPlus**](https://github.com/evalplus/evalplus) benchmark, which includes HumanEval(+) and MBPP(+) datasets. These datasets are designed to test code generation capabilities under varied conditions.


### 1. Released Generations and Results

We have released the code generations and their corresponding evaluation results in the folder `released/`. These include outputs from different configurations and their performance metrics.

```bash
released
|-- outputs         # generations
|   |-- humaneval
|   |   |-- codeqwen_base_temp_0.0
|   |   |-- codeqwen_chat-awq_temp_0.0
|   |   `-- codeqwen_chat_temp_0.0
|   `-- mbpp
|       |-- codeqwen_base_temp_0.0
|       |-- codeqwen_chat-awq_temp_0.0
|       `-- codeqwen_chat_temp_0.0
`-- results         # evaluation results
    |-- humaneval
    |   |-- codeqwen_base.txt
    |   |-- codeqwen_chat-awq.txt
    |   `-- codeqwen_chat.txt
    `-- mbpp
        |-- codeqwen_base.txt
        |-- codeqwen_chat-awq.txt
        `-- codeqwen_chat.txt
```

We report both base and base+extra results for each configuration.

<table style="text-align:center;">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>HumanEval</td>
        <td>HumanEval+</td>
        <td>MBPP</td>
        <td>MBPP+</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td><td>51.8</td><td>45.7</td><td>72.7</td><td>60.2</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td><td>83.5</td><td>78.7</td><td>77.7</td><td>67.2</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat-AWQ</b></td>
        <td style="text-align: left">7B</td><td>83.5</td><td>78.0</td><td>78.7</td><td>66.7</td>
    </tr>
</table>

### 2. Setup

Please refer to [**EvalPlus**](https://github.com/evalplus/evalplus) for detailed setup instructions. Install the required packages using:

```bash
pip install evalplus --upgrade
pip install -r requirements.txt
```

### 3. Inference and Evaluation

We utilize 8xA100 GPUs for this benchmark. The following scripts are used to run the inference and evaluations:

```bash
bash run_humaneval.sh
bash run_mbpp.sh
```

### Troubleshooting

If you experience poor network conditions that prevent downloading models directly from the repository during runtime, you can switch to using locally downloaded models. 

- **Download the Model**: Ensure you have the model files downloaded to your local machine.
- **Update the `MODEL_MAPPING`**: Modify the MODEL_MAPPING in `generate.py`
    ```python
    MODEL_MAPPING = {
        "codeqwen": {
            "base": "/path/to/your/local/CodeQwen1.5-7B",
            # ...
        },
    }
    ```