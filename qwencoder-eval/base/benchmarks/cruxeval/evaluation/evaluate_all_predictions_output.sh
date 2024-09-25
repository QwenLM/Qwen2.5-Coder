#!/bin/bash

run_names=(
    # "codellama-13b+cot_temp0.2_output"
    # "codellama-13b+cot_temp0.8_output"
    # "codellama-13b_temp0.2_output"
    # "codellama-13b_temp0.8_output"
    # "codellama-34b+cot_temp0.2_output"
    # "codellama-34b+cot_temp0.8_output"
    # "codellama-34b_temp0.2_output"
    # "codellama-34b_temp0.8_output"
    # "codellama-7b+cot_temp0.2_output"
    # "codellama-7b+cot_temp0.8_output"
    # "codellama-7b_temp0.2_output"
    # "codellama-7b_temp0.8_output"
    # "codellama-python-13b_temp0.2_output"
    # "codellama-python-13b_temp0.8_output"
    # "codellama-python-34b_temp0.2_output"
    # "codellama-python-34b_temp0.8_output"
    # "codellama-python-7b_temp0.2_output"
    # "codellama-python-7b_temp0.8_output"
    # "codetulu-2-34b_temp0.2_output"
    # "codetulu-2-34b_temp0.8_output"
    # "deepseek-base-1.3b_temp0.2_output"
    # "deepseek-base-1.3b_temp0.8_output"
    # "deepseek-base-33b_temp0.2_output"
    # "deepseek-base-33b_temp0.8_output"
    # "deepseek-base-6.7b_temp0.2_output"
    # "deepseek-base-6.7b_temp0.8_output"
    # "deepseek-instruct-1.3b_temp0.2_output"
    # "deepseek-instruct-1.3b_temp0.8_output"
    # "deepseek-instruct-33b_temp0.2_output"
    # "deepseek-instruct-33b_temp0.8_output"
    # "deepseek-instruct-6.7b_temp0.2_output"
    # "deepseek-instruct-6.7b_temp0.8_output"
    # "gpt-3.5-turbo-0613+cot_temp0.2_output"
    # "gpt-3.5-turbo-0613+cot_temp0.8_output"
    # "gpt-3.5-turbo-0613_temp0.2_output"
    # "gpt-3.5-turbo-0613_temp0.8_output"
    # "gpt-4-0613+cot_temp0.2_output"
    # "gpt-4-0613+cot_temp0.8_output"
    # "gpt-4-0613_temp0.2_output"
    # "gpt-4-0613_temp0.8_output"
    # "magicoder-ds-7b_temp0.2_output"
    # "magicoder-ds-7b_temp0.8_output"
    # "mistral-7b_temp0.2_output"
    # "mistral-7b_temp0.8_output"
    # "mixtral-8x7b_temp0.2_output"
    # "mixtral-8x7b_temp0.8_output"
    # "phi-1.5_temp0.2_output"
    # "phi-1.5_temp0.8_output"
    # "phi-1_temp0.2_output"
    # "phi-1_temp0.8_output"
    # "phi-2_temp0.2_output"
    # "phi-2_temp0.8_output"
    # "phind_temp0.2_output"
    # "phind_temp0.8_output"
    # "starcoderbase-16b_temp0.2_output"
    # "starcoderbase-16b_temp0.8_output"
    # "starcoderbase-7b_temp0.2_output"
    # "starcoderbase-7b_temp0.8_output"
    # "wizard-13b_temp0.2_output"
    # "wizard-13b_temp0.8_output"
    # "wizard-34b_temp0.2_output"
    # "wizard-34b_temp0.8_output"
)

mkdir evaluation_results
for run_name in "${run_names[@]}"; do
	echo $run_name
    sbatch --export=ALL,run_name="${run_name}" <<'EOF'
#!/bin/bash
#SBATCH --output=slurm_logs/slurm-%A-%a.out
#SBATCH --error=slurm_logs/slurm-%A-%a.err
#SBATCH --partition=YOUR_PARTITION_HERE
#SBATCH --cpus-per-task=40
#SBATCH --mem=0GB
#SBATCH --time=03:00:00

python evaluate_generations.py \
    --generations_path ../model_generations/${run_name}/generations.json \
    --scored_results_path evaluation_results/${run_name}.json \
    --mode output
EOF
done