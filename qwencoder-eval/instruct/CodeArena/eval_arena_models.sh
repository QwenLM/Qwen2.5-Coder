cd ./code_arena;
MODEL_DIR="Qwen2.5-Coder-32B"
INPUT_PATH="./data/CodeArena_v1.jsonl"
OUTPUT_PATH="./Qwen2.5-Coder-32B/results.jsonl"
TP=1
MAX_LEN=16384
CHAT_TEMPLATE="auto"
bash eval_arena.sh ${INPUT_PATH} ${OUTPUT_PATH} ${MODEL_DIR} ${TP} ${MAX_LEN} ${CHAT_TEMPLATE}

