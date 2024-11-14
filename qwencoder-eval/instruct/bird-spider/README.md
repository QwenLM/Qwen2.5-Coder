## Prepare data

1. Download **data** from [Alibaba Cloud OSS](https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen2.5/Qwen2.5-Coder-Family/sql_data.zip). This is a zip file containing the data for the test suite.
2. Unzip the file and put the `data` folder in the `sql_suites` directory.

The final structure should be like this:

```text
├── README.md
├── code_eval
│   ├── __init__.py
│   ├── arguments.py
│   ├── base.py
│   ├── evaluator.py
│   ├── generation.py
│   ├── tasks
│   │   ├── __init__.py
│   │   ├── bird_dev.py
│   │   ├── bird_dev_chat.py
│   │   ├── bird_dev_chat_cot.py
│   │   ├── spider_dev.py
│   │   ├── spider_dev_chat.py
│   │   ├── spider_dev_chat_cot.py
│   │   ├── sql_task_base.py
│   │   ├── sql_task_chat_base.py
│   │   └── sql_task_chat_cot_base.py
│   └── utils.py
├── dog_utils.py
├── main.py
├── openai_api_test.sh
├── sql_suites
│   ├── comparator.py
│   ├── data
│   │   ├── bird-dev
│   │   └── spider-dev
│   ├── eval.py
│   ├── preprocess_bird.py
│   ├── preprocess_spider.py
│   └── utils.py
├── test-cot.sh
└── test.sh
```

## Run test
- run `bash test.sh` to run base test, e.g. `bash test.sh Qwen/Qwen2.5-Coder-7B-Instruct 2 outputs`
  - The 1st argument is the path of the test suite, e.g. `Qwen/Qwen2.5-Coder-7B-Instruct`
  - The 2nd argument is the tensor-parallel-size, e.g. `2`
  - The 3rd argument is the output directory, e.g. `outputs`

- run `bash test-cot` to run cot test, e.g. `bash test-cot Qwen/Qwen2.5-Coder-7B-Instruct 2 outputs`
  - The 1st argument is the path of the test suite, e.g. `Qwen/Qwen2.5-Coder-7B-Instruct`
  - The 2nd argument is the tensor-parallel-size, e.g. `2`
  - The 3rd argument is the output directory, e.g. `outputs`

- run `openai_api_test` to test openai compatibale model, e.g. `bash openai_api_test gpt-4o outputs`
  - The 1st argument is the path of the test suite, e.g. `gpt-4o`
  - The 2nd argument is the output directory, e.g. `outputs`