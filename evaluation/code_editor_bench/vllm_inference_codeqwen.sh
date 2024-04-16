#!/bin/bash
mkdir -p greedy_result/{code_debug,code_translate,code_polishment,code_switch}
mkdir -p solution_folder/{code_debug,code_translate,code_polishment,code_switch}
base_models=(
    "Qwen/CodeQwen1.5-7B-Chat" \
)
datasets=("debug" "translate" "polishment" "switch")

for base_model in "${base_models[@]}"; do
    for dataset in "${datasets[@]}"; do
        echo "Running inference with base_model: $base_model and dataset: $dataset"
        python vllm_inference.py \
            --base_model "$base_model" \
            --dataset "$dataset" \
            --input_data_dir "./data/" \
            --output_data_dir "./greedy_result/" \
            --batch_size 64 \
            --num_of_sequences 1 \
            --num_gpus 8 \
            --prompt_type "zero" \
            --start_idx 0 \
            --end_idx -1
    done
done