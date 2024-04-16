export PATH=/python/bin/:$PATH;
MODEL_DIR="Qwen/CodeQwen1.5-7B-Chat"
DATA_PATH="./data/"
LANGUAGE=${1}
LANGUAGE=${LANGUAGE:-"python"}
echo "benchmark: humaneval, language ${LANGUAGE}"
GENERATION_PATH="./results/generation_${LANGUAGE}.jsonl"
METRIC_OUTPUT_PATH="./results/results_${LANGUAGE}.jsonl"
PORT=$((RANDOM%9000+1000))
echo "PORT: ${PORT}"

python evaluate.py  \
    --benchmark "humaneval" \
    --model ${MODEL_DIR} \
    --language ${LANGUAGE} \
    --generation_path ${GENERATION_PATH} \
    --metric_output_path ${METRIC_OUTPUT_PATH} \
    --model_max_length 1024 \

