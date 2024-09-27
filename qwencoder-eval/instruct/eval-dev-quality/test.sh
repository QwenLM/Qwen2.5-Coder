#!/bin/bash
export GOPROXY=https://goproxy.cn,direct

export HF_ENDPOINT=http://hf-mirror.com
export HF_HOME="/hf_offline/huggingface"
export HF_DATASETS_OFFLINE=1
export HF_EVALUATE_OFFLINE=1

export OPENAI_API_BASE=http://0.0.0.0:8000/v1
export OPENAI_API_KEY=token-abc123

export MODEL=$1
export TP=$2
export OUTPUT_DIR=$3

export SERVED_MODEL_NAME=$(basename ${MODEL})
export API_MODEL_NAME=custom-vllm/${SERVED_MODEL_NAME}

mkdir -p ${OUTPUT_DIR}

echo "Starting serving ${MODEL} as ${SERVED_MODEL_NAME}..."
vllm serve ${MODEL} \
    --served-model-name ${SERVED_MODEL_NAME} \
    --tensor-parallel-size ${TP} \
    --trust-remote-code \
    --max-model-len 4096 \
    --dtype auto \
    --api-key token-abc123 \
    > ${OUTPUT_DIR}/vllm-server.txt 2>&1 &

jobs -l > ${OUTPUT_DIR}/jobs.txt
PID=$(awk '{print $2}' ${OUTPUT_DIR}/jobs.txt)
echo "PID: $PID"

echo "Waiting for the model to be served..."
while true; do
    if grep -q 'Uvicorn running on' "${OUTPUT_DIR}/vllm-server.txt"; then
        echo "Model is being served..."
        break
    else
        echo "Waiting for model to start..."
        sleep 1
    fi
done


make install

echo "Benchmarking ${SERVED_MODEL_NAME}..."
eval-dev-quality evaluate \
    --execution-timeout 30 \
    --install-tools-path .tools \
    --urls=custom-vllm:${OPENAI_API_BASE} \
    --tokens=custom-vllm:${OPENAI_API_KEY} \
	--result-path ${OUTPUT_DIR}/history \
    --model ${API_MODEL_NAME}

PID=$(awk '{print $2}' ${OUTPUT_DIR}/jobs.txt)
kill ${PID}

# Extract the score from the evaluation log
echo "{\"score\": $(tail -n 2 ${OUTPUT_DIR}/history/evaluation.log | sed -n 's/.*score=\([0-9]\+\).*/\1/p')}" > ${OUTPUT_DIR}/results.json