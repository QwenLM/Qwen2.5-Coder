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
bash evaluate_humaneval.sh python #(Python, Java, CPP, Javascript, Typescript, and other languages)
```



## Acknowledgement

We referred to the evaluation code at [DeepSeek-Coder](https://github.com/deepseek-ai/DeepSeek-Coder/tree/main/Evaluation/HumanEval) and appreciate their contribution.
