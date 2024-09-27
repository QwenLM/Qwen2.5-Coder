#!/bin/bash

export MODEL_DIR=$1
export TP=$2
export OUTPUT_DIR=$3

MODEL_NAME=$(basename ${MODEL_DIR})

# define the base path for saving generations and scored results
SAVE_GENERATIONS_BASE_PATH=${OUTPUT_DIR}/cruxeval

# define the tasks and their corresponding modes
declare -A tasks_modes=(["input_prediction"]="input" ["output_prediction"]="output")

# loop over the tasks
for task in "${!tasks_modes[@]}"; do
    mode=${tasks_modes[$task]}
    for cot in "" "_cot"; do
		# define the file paths
        SAVE_GENERATIONS_PATH="${SAVE_GENERATIONS_BASE_PATH}_${mode}${cot}/completion.json"
        SCORED_RESULTS_PATH="${SAVE_GENERATIONS_BASE_PATH}_${mode}${cot}/completion_scored.json"
		mkdir -p $(dirname ${SAVE_GENERATIONS_PATH})

		# execute inference
        python inference/main.py \
            --model ${MODEL_DIR} \
            --trust_remote_code \
            --tasks ${task} \
            --batch_size 1 \
            --save_generations_path ${SAVE_GENERATIONS_PATH} \
            --save_generations \
            --tensor_parallel_size ${TP} \
            ${cot:+--cot}

		# execute evaluation
        python evaluation/evaluate_generations.py \
            --generations_path ${SAVE_GENERATIONS_PATH} \
            --scored_results_path ${SCORED_RESULTS_PATH} \
            --mode ${mode}
    done
done