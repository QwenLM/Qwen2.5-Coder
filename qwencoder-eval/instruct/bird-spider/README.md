## Prepare data

Download `sql_suites` data from `Alibaba Cloud OSS`, and put it to `.` directory.

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