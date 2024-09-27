export PATH=./vllm/bin:$PATH

lgs=("python" "cs" "cpp" "java" "php" "ts" "sh" "js")

npm install -g multiple_metrics/typescript-5.5.4.tgz


MODEL_DIR=${1}
TP=${2}
OUTPUT_DIR=${3}

echo "Multiple: ${MODEL_DIR}"
for lg in ${lgs[@]}; do
    GENERATION_PATH="${OUTPUT_DIR}/generations_${lg}.jsonl"
    METRIC_OUTPUT_PATH="${OUTPUT_DIR}/results_${lg}.jsonl"
    bash evaluate_humaneval.sh ${MODEL_DIR} ${lg} ${GENERATION_PATH} ${METRIC_OUTPUT_PATH} "chat_template" ${TP}
done