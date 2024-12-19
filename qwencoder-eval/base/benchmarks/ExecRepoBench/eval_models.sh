ROOT_DIR="./ExecRepoBench"
MODEL_NAME="qwen2.5-coder-base-7B"
MODEL_DIR="./qwen/Qwen2.5-Coder-7B"
INPUT_PATH="./test_set/exec_repo_bench.jsonl"
OUTPUT_PATH=". /results/${MODEL_NAME}/generation.jsonl"
WORKERS=64
TP=1
EXTRA_ARGS="-max_context_tokens 8192 -max_tokens 32768 -max_generation_tokens 1024"
bash ${ROOT_DIR}/eval.sh ${MODEL_NAME} ${MODEL_DIR} ${INPUT_PATH} ${OUTPUT_PATH} ${WORKERS} ${TP} "${EXTRA_ARGS}"
