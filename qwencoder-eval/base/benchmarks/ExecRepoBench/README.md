## Dataset Summary
In this work, we introduce a novel framework for enhancing code completion in software development through the creation of a repository-level benchmark ExecRepoBench and the instruction corpora Repo-Instruct, aim at improving the functionality of open-source large language models (LLMs) in real-world coding scenarios that involve complex interdependencies across multiple files. ExecRepoBench includes 1.2K samples from active Python repositories. Plus, we present a multi-level grammar-based completion methodology conditioned on the abstract syntax tree to mask code fragments at various logical units (e.g. statements, expressions, and functions).

## Download Data
```sh
git lfs install
git clone https://huggingface.co/datasets/CSJianYang/ExecRepoBench
```

##Install Miniconda
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

## Create Evaluation Environments
```
export PATH=./miniconda3/envs/vllm/bin/:$PATH
python create_test_repo.py --action "prepare_environments"
```
## Verify Evaluation Environments

```
export PATH=./miniconda3/envs/vllm/bin/:$PATH
python create_test_repo.py --action "verify_all_repo_correctness"
```
## Evaluation
```sh
ROOT_DIR="./ExecRepoBench"
MODEL_NAME="qwen2.5-coder-base-7B"
MODEL_DIR="./qwen/Qwen2.5-Coder-7B"
INPUT_PATH="./test_set/exec_repo_bench.jsonl"
OUTPUT_PATH=". /results/${MODEL_NAME}/generation.jsonl"
WORKERS=64
TP=1
EXTRA_ARGS="-max_context_tokens 8192 -max_tokens 32768 -max_generation_tokens 1024"
bash ${ROOT_DIR}/eval.sh ${MODEL_NAME} ${MODEL_DIR} ${INPUT_PATH} ${OUTPUT_PATH} ${WORKERS} ${TP} "${EXTRA_ARGS}"
```

## Citation
If you use the data from this project, please cite the original paper:
```
@article{yang2024execrepobench,
  title={ExecRepoBench: Multi-level Executable Code Completion Evaluation},
  author={Yang, Jian and Zhang, Jiajun and Yang, Jiaxi and Jin, Ke and Zhang, Lei and Peng, Qiyao and Deng, Ken and Miao, Yibo and Liu, Tianyu and Cui, Zeyu and others},
  journal={arXiv preprint arXiv:2412.11990},
  year={2024}
}
```
