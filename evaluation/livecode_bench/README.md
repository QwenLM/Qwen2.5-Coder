## LiveCodeBench

### Introduction
[LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) provides holistic and contamination-free evaluation of coding capabilities of LLMs. Particularly, LiveCodeBench continuously collects new problems over time from contests across three competition platforms -- LeetCode, AtCoder, and CodeForces. 

### How to reproduce
Our evaluation of CodeQwen1.5 is grounded on the version found in LiveCodeBench at commit [e82c2488](https://github.com/LiveCodeBench/LiveCodeBench/tree/e82c2488e6a9632ed6f482c3c5cf85f042694df5). Subsequently, we will integrate CodeQwen1.5 into the official code to facilitate the evaluation process.
> **Installation**
```bash
# Make sure the CUDA version > 12.0.
pip install -r requirements.txt
pip install flash-attn --no-build-isolation
```
> **For running the inference, please use the following command.**
```bash
# Qwen/CodeQwen1.5-7B-Chat
python -m lcb_runner.runner.main --model Qwen/CodeQwen1.5-7B-Chat --scenario codegeneration --evaluate
# Qwen/CodeQwen1.5-7B
python -m lcb_runner.runner.main --model Qwen/CodeQwen1.5-7B --scenario codegeneration --evaluate
```
> **To get scores over different time windows**
```bash
# Qwen/CodeQwen1.5-7B-Chat
python -m lcb_runner.evaluation.compute_scores --eval_all_file output/CodeQwen1.5-7B-Chat/Scenario.codegeneration_10_0.2_eval_all.json --start_date 2023-09-01 --end_date 2024-04-01
# Qwen/CodeQwen1.5-7B
python -m lcb_runner.evaluation.compute_scores --eval_all_file output/CodeQwen1.5-7B/Scenario.codegeneration_10_0.2_eval_all.json --start_date 2023-09-01 --end_date 2024-04-01
```
### Results
<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>All Time</div>
                <div>Pass@1</div>
            </div>
        </td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>Sep. 2023 ~ Apr. 2024</div>
                <div>Pass@1</div>
            </div>
        </td>
    </tr>
    <tr>
        <td colspan=4><b>Base Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>6.5</td>
        <td>7.6</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2</td>
        <td style="text-align: left">7B</td>
        <td>11.3</td>
        <td>12.7</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>19.1</td>
        <td>13.7</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td>
        <td><b>21.8</b></td>
        <td><b>19.3</b></td>
    </tr>
    <tr>
        <td colspan=4><b>Chat Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Instruct</td>
        <td style="text-align: left">7B</td>
        <td>10.6</td>
        <td>12.4</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>21.6</td>
        <td>19.2</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td><b>24.8</b></td>
        <td><b>23.5</b></td>
    </tr>
</table>

### Acknowleage
Thank you to the [LiveCodeBench](https://livecodebench.github.io/leaderboard.html) team for their contributions to the open-source community.