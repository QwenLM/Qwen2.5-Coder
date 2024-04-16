## CodeEditorbench

### Introduction
[CodeEditorBench](https://github.com/CodeEditorBench/CodeEditorBench/tree/main), a pioneering evaluation framework designed to rigorously assess the performance of LLMs in code editing tasks, including debugging, translating, polishing, and requirement switching. Unlike existing benchmarks focusing solely on code generation, CodeEditorBench emphasizes real-world scenarios and practical aspects of software development.

### How to reproduce
Our evaluation of CodeQwen1.5 is grounded on the version found in CodeEditorBench at commit [83d6ed9](https://github.com/CodeEditorBench/CodeEditorBench/tree/83d6ed96b4ce3d9a05acaf1d03c556b7514d60a5). Subsequently, we will integrate CodeQwen1.5 into the official code to facilitate the evaluation process.
> **Installation**
Please refer to [CodeEditorBench](https://github.com/CodeEditorBench/CodeEditorBench.git) for detailed setup instructions. Install the required packages using:
```bash
conda env create -f coder.yml
conda activate coder
```
> **Replace the corresponding file in the CodeEditorBench repository.**
```bash
rsync -av --exclude='solution_folder' --exclude='README.md' ./ /path/to/your/local/CodeEditorBench/
```
> **Inference**
```bash
cd /path/to/your/local/CodeEditorBench/
bash vllm_inference_codeqwen.sh
python result_postprocess.py
```
The results of the CodeQwen1.5-7B-Chat inference, followed by post-processing, have been released in the `solution_folder/` directory. 
```bash
solution_folder
|-- code_debug        
|   |-- CodeQwen1.5_7B_Chat_0_end.jsonl
`-- code_polishment      
|   |-- CodeQwen1.5_7B_Chat_0_end.jsonl
`-- code_switch       
|   |-- CodeQwen1.5_7B_Chat_0_end.jsonl
`-- code_translate      
|   |-- CodeQwen1.5_7B_Chat_0_end.jsonl
```
> **Evalution**

🚨 Evaluation is performed within Docker. To perform evaluation on CodeEditorBench, please refer to [Evaluation](https://github.com/CodeEditorBench/CodeEditorBench/blob/main/evaluation/README.md) for more details. We reached out to the CodeEditorBench team to conduct a evaluation of CodeQwen1.5-7B-Chat, and we are grateful for their kindness.

### Results
The model was evaluated under the Zero Shot setting across both the CodeEditorBench Plus and Primary datasets, with the evaluation metric being the `Win Rate`.
<table style="text-align:center">
    <tr>
        <th style="text-align: left">Model</th>
        <th>Plus Dataset</th>
        <th>Primary Dataset</th>
    </tr>
    <tr>
        <td style="text-align: left">GPT4</td>
        <td>85.5</td>
        <td>86.8</td>
    </tr>
    <tr>
        <td style="text-align: left">Gemini-Ultra</td>
        <td>77.6</td>
        <td>81.6</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td>72.4</td>
        <td>77.6</td>
    </tr>
    <tr>
        <td style="text-align: left">CodeQwen1.5-7B-Chat</td>
        <td>62.5</td>
        <td>69.7</td>
    </tr>
    <tr>
        <td style="text-align: left">Magicoder-DS-6.7B-Ins</td>
        <td>51.3</td>
        <td>69.7</td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLLaMA-13B-Ins</td>
        <td>42.1</td>
        <td>36.8</td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLLaMA-7B-Ins</td>
        <td>28.9</td>
        <td>25.0</td>
    </tr>
</table>

### Acknowleage
Thank you to the [CodeEditorBench](https://codeeditorbench.github.io/) team for their contributions to the open-source community.

