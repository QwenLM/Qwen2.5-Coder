
export PATH=/path/to/vllm/bin/:$PATH
ROOT_DIR="/path/to/ExecRepoBench"
MODEL_NAME=${1}
MODEL_DIR=${2}
INPUT_PATH=${3}
OUTPUT_PATH=${4}
WORKERS=${5}
TP=${6}
EXTRA_ARGS=${7}

MODEL_NAME=${MODEL_NAME:-""}
MODEL_DIR=${MODEL_DIR:-""}
INPUT_PATH=${INPUT_PATH:-""}
OUTPUT_PATH=${OUTPUT_PATH:-""}
WORKERS=${WORKERS:-64}
TP=${TP:-1}

echo "MODEL_NAME: ${MODEL_NAME}"
echo "MODEL_DIR: ${MODEL_DIR}"
echo "EXTRA_ARGS: ${EXTRA_ARGS}"

cd ${ROOT_DIR};

if [ ! -f ${OUTPUT_PATH} ]; then
    echo "Generating ${OUTPUT_PATH}"
    python eval.py \
        -model_name ${MODEL_NAME} \
        -model_dir ${MODEL_DIR} \
        -input_path ${INPUT_PATH} \
        -output_path ${OUTPUT_PATH} \
        -workers ${WORKERS} \
        -generation_only \
        -tensor_parallel_size ${TP} \
        ${EXTRA_ARGS}
fi

if [ ! -f ${OUTPUT_PATH}.metric ]; then
    echo "Evaluating ${OUTPUT_PATH}"
    python eval.py \
        -model_name ${MODEL_NAME} \
        -model_dir ${MODEL_DIR} \
        -input_path ${INPUT_PATH} \
        -output_path ${OUTPUT_PATH} \
        -workers ${WORKERS} \
        -evaluation_only
fi
