export PATH=/path/to/envs/qwen/bin/:$PATH
cd ./code_arena;
INPUT_PATH=${1}
OUTPUT_PATH=${2}
MODEL_DIR=${3}
TP=${4}
MAX_LEN=${5}
CHAT_TEMPLATE=${6}
CONFIG_FILE=${7}

#MAX_LEN=${MAX_LEN:-8192}
CHAT_TEMPLATE=${CHAT_TEMPLATE:-"auto"}
TP=${TP:-1}
INPUT_PATH=${INPUT_PATH:-""}
OUTPUT_PATH=${OUTPUT_PATH:-""}
MODEL_DIR=${MODEL_DIR:-""}
CONFIG_FILE=${CONFIG_FILE:-"./utils/judge_config.yaml"}
if [ ! -f ${OUTPUT_PATH} ]; then
    python infer_vllm.py -model ${MODEL_DIR} -input_path ${INPUT_PATH} -output_path ${OUTPUT_PATH} -tensor_parallel_size ${TP} -model_max_len ${MAX_LEN} -chat_template ${CHAT_TEMPLATE} # 
fi
EVAL_PATH="${OUTPUT_PATH}.judge"
if [ ! -f ${EVAL_PATH} ]; then
    python judge_models.py -input_path ${OUTPUT_PATH} -output_path ${EVAL_PATH} -workers 64 -judgement_only -setting_file ${CONFIG_FILE} 
fi
if [ ! -f ${OUTPUT_PATH}.judge.metric ]; then
    python judge_models.py -input_path ${OUTPUT_PATH} -output_path ${EVAL_PATH} -evaluation_only -setting_file ${CONFIG_FILE}
fi
