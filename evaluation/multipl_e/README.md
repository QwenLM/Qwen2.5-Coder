# Evaluation on MultiPL-E

## Base Model


```bash
cd base
bash eval.sh > codeqwen-7b.log
python collect.py
```



## Chat Model
Your must specify the path of the `${DATA_PATH}`, `${MODEL_DIR}`, and `${LANGUAGE}` in evaluate_humaneval.sh
```bash
cd chat
bash evaluate_humaneval.sh python
```



## Results

The `CodeQwen-7B` and `CodeQwen-7B-Chat` results on MultiPL-E are shown in the following table.

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>Python</td>
        <td>C++</td>
        <td>Java</td>
        <td>PHP</td>
        <td>TypeScript</td>
        <td>C#</td>
        <td>Bash</td>
        <td>JavaScript</td>
        <td>Average</td>
    </tr>
    <tr>
        <td colspan=11><b>Base Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>31.7</td>
        <td>29.8</td>
        <td>34.2</td>
        <td>23.6</td>
        <td>36.5</td>
        <td>36.7</td>
        <td>12.0</td>
        <td>29.2</td>
        <td>29.2</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2-Base</td>
        <td style="text-align: left">7B</td>
        <td>35.3</td>
        <td>40.9</td>
        <td>37.3</td>
        <td>29.2</td>
        <td>37.7</td>
        <td>40.5</td>
        <td>9.4</td>
        <td>36.0</td>
        <td>33.3</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>49.4</td>
        <td>50.3</td>
        <td>43.0</td>
        <td>38.5</td>
        <td>49.7</td>
        <td>50.0</td>
        <td>28.5</td>
        <td>48.4</td>
        <td>44.7</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5<b></td>
        <td style="text-align: left">7B</td>
        <td>52.4</td>
        <td>52.2</td>
        <td>42.4</td>
        <td>46.6</td>
        <td>52.2</td>
        <td>55.7</td>
        <td>36.7</td>
        <td>49.7</td>
        <td>48.5</td>
    </tr>
    <tr>
        <td colspan=11><b>Chat Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>76.2</td>
        <td>63.4</td>
        <td>69.2</td>
        <td>60.9</td>
        <td>69.1</td>
        <td>70.8</td>
        <td>42.4</td>
        <td>67.1</td>
        <td>64.9</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4</td>
        <td style="text-align: left">-</td>
        <td>84.1</td>
        <td>76.4</td>
        <td>81.6</td>
        <td>77.2</td>
        <td>77.4</td>
        <td>79.1</td>
        <td>58.2</td>
        <td>78.0</td>
        <td>76.5</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>78.6</td>
        <td>63.4</td>
        <td>68.4</td>
        <td>68.9</td>
        <td>67.2</td>
        <td>72.8</td>
        <td>36.7</td>
        <td>72.7</td>
        <td>66.1</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td>83.2</td>
        <td>71.2</td>
        <td>70.1</td>
        <td>73.5</td>
        <td>75.4</td>
        <td>75.9</td>
        <td>41.1</td>
        <td>78.2</td>
        <td>71.1</td>
    </tr>
</table>


## Acknowledgement

We referred to the evaluation code at [DeepSeek-Coder](https://github.com/deepseek-ai/DeepSeek-Coder/tree/main/Evaluation/HumanEval) and appreciate their contribution.
