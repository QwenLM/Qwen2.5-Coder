cd ./CodeQwen1.5/evaluation/multipl_e/chat;
export PATH=/python/path/:$PATH
lgs=("python" "cs" "cpp" "java" "php" "ts" "sh" "js")
MODEL_DIR=${1}
MODEL_DIR=${MODEL_DIR:-"/codeqwen/path/"}
TP=${2}
TP=${TP:-1}
OUTPUT_DIR=${3}
OUTPUT_DIR=${OUTPUT_DIR:-"/result/path/"}

echo "Multiple: ${MODEL_DIR}"
for lg in ${lgs[@]}; do
    GENERATION_PATH="${OUTPUT_DIR}/generations_${lg}.jsonl"
    METRIC_OUTPUT_PATH="${OUTPUT_DIR}/results_${lg}.jsonl"
    bash evaluate_humaneval.sh ${MODEL_DIR} ${lg} ${GENERATION_PATH} ${METRIC_OUTPUT_PATH} "chatml" ${TP}
done
