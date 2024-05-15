export PATH=/cpfs01/shared/public/yj411294/miniconda3/envs/qwen/bin:$PATH;
export TOKENIZERS_PARALLELISM=true;
MODEL_DIR=${1}
MODEL_DIR=${MODEL_DIR:-"/home/data/dangkai.dk/hf_ckpts/7b.5000B--longcnt_mixv1-base1000w-cpt256k-v10.15.26_code_v6"}
DATA_PATH="/cpfs01/shared/public/yj411294/CrossMutation/CodeQwen1.5/evaluation/multipl_e/chat/data/"
LANGUAGE=${2}
LANGUAGE=${LANGUAGE:-"python"}
echo "benchmark: humaneval, language ${LANGUAGE}"
GENERATION_PATH=${3}
GENERATION_PATH=${GENERATION_PATH:-"./results/generation_${LANGUAGE}.jsonl"}
METRIC_OUTPUT_PATH=${4}
CHAT_FORMAT=${5}
CHAT_FORMAT=${CHAT_FORMAT:-"chatml"}
METRIC_OUTPUT_PATH=${METRIC_OUTPUT_PATH:-"./results/results_${LANGUAGE}.jsonl"}
TP=${6}
TP=${TP:-1}
PORT=$((RANDOM%9000+1000))
echo "PORT: ${PORT}"

python evaluate.py  \
    --benchmark "humaneval" \
    --model ${MODEL_DIR} \
    --language ${LANGUAGE} \
    --generation_path ${GENERATION_PATH} \
    --metric_output_path ${METRIC_OUTPUT_PATH} \
    --model_max_length 1024 \
    --data_path ${DATA_PATH} \
    --use_vllm \
    --chat_format ${CHAT_FORMAT} \
    --tensor_parallel_size ${TP}
