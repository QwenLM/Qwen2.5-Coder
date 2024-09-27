export PATH=./aider/bin:$PATH

export HF_ENDPOINT=http://hf-mirror.com
export HF_HOME=""
export HF_DATASETS_OFFLINE=1
export HF_EVALUATE_OFFLINE=1

export OPENAI_API_BASE=http://0.0.0.0:8000/v1
export OPENAI_API_KEY=token-abc123

export MODEL=$1
export TP=$2
export OUTPUT_DIR=$3

export SERVED_MODEL_NAME=$(basename ${MODEL})
export API_MODEL_NAME=openai/${SERVED_MODEL_NAME}

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

sleep 5
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

echo "Benchmarking ${SERVED_MODEL_NAME}..."

python benchmark/benchmark.py ${SERVED_MODEL_NAME} \
    --new \
    --model ${API_MODEL_NAME} \
    --edit-format whole \
    --threads 10 \
    > ${OUTPUT_DIR}/log.txt

# extract the required lines from log.txt and use awk to extract the corresponding values
pass_rate_1=$(tail -n 100 ${OUTPUT_DIR}/log.txt | grep 'pass_rate_1' | awk '{print $2}')
pass_rate_2=$(tail -n 100 ${OUTPUT_DIR}/log.txt | grep 'pass_rate_2' | awk '{print $2}')
percent_cases_well_formed=$(tail -n 100 ${OUTPUT_DIR}/log.txt | grep 'percent_cases_well_formed' | awk '{print $2}')

# create JSON-formatted content
json_content=$(cat <<EOF
{
  "pass_rate_1": $pass_rate_1,
  "pass_rate_2": $pass_rate_2,
  "percent_cases_well_formed": $percent_cases_well_formed
}
EOF
)

# write the JSON content to the results.json file
echo "$json_content" > ${OUTPUT_DIR}/results.json

PID=$(awk '{print $2}' ${OUTPUT_DIR}/jobs.txt)
kill ${PID}