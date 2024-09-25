#!/bin/bash

run_names=(
    #  "codellama-13b+cot_temp0.2_input"
    #  "codellama-13b+cot_temp0.8_input"
    #  "codellama-13b_temp0.2_input"
    #  "codellama-13b_temp0.8_input"
    #  "codellama-34b+cot_temp0.2_input"
    #  "codellama-34b+cot_temp0.8_input"
    #  "codellama-34b_temp0.2_input"
    #  "codellama-34b_temp0.8_input"
    #  "codellama-7b+cot_temp0.2_input"
    #  "codellama-7b+cot_temp0.8_input"
    #  "codellama-7b_temp0.2_input"
    #  "codellama-7b_temp0.8_input"
    #  "codellama-python-13b_temp0.2_input"
    #  "codellama-python-13b_temp0.8_input"
    #  "codellama-python-34b_temp0.2_input"
    #  "codellama-python-34b_temp0.8_input"
    #  "codellama-python-7b_temp0.2_input"
    #  "codellama-python-7b_temp0.8_input"
    #  "codetulu-2-34b_temp0.2_input"
    #  "codetulu-2-34b_temp0.8_input"
    #  "deepseek-base-1.3b_temp0.2_input"
    #  "deepseek-base-1.3b_temp0.8_input"
    #  "deepseek-base-33b_temp0.2_input"
    #  "deepseek-base-33b_temp0.8_input"
    #  "deepseek-base-6.7b_temp0.2_input"
    #  "deepseek-base-6.7b_temp0.8_input"
    #  "deepseek-instruct-1.3b_temp0.2_input"
    #  "deepseek-instruct-1.3b_temp0.8_input"
    #  "deepseek-instruct-33b_temp0.2_input"
    #  "deepseek-instruct-33b_temp0.8_input"
    #  "deepseek-instruct-6.7b_temp0.2_input"
    #  "deepseek-instruct-6.7b_temp0.8_input"
    #  "gpt-3.5-turbo-0613+cot_temp0.2_input"
    #  "gpt-3.5-turbo-0613+cot_temp0.8_input"
    #  "gpt-3.5-turbo-0613_temp0.2_input"
    #  "gpt-3.5-turbo-0613_temp0.8_input"
    #  "gpt-4-0613+cot_temp0.2_input"
    #  "gpt-4-0613+cot_temp0.8_input"
    #  "gpt-4-0613_temp0.2_input"
    #  "gpt-4-0613_temp0.8_input"
    #  "magicoder-ds-7b_temp0.2_input"
    #  "magicoder-ds-7b_temp0.8_input"
    #  "mistral-7b_temp0.2_input"
    #  "mistral-7b_temp0.8_input"
    #  "mixtral-8x7b_temp0.2_input"
    #  "mixtral-8x7b_temp0.8_input"
    #  "phi-1.5_temp0.2_input"
    #  "phi-1.5_temp0.8_input"
    #  "phi-1_temp0.2_input"
    #  "phi-1_temp0.8_input"
    #  "phi-2_temp0.2_input"
    #  "phi-2_temp0.8_input"
    #  "phind_temp0.2_input"
    #  "phind_temp0.8_input"
    #  "starcoderbase-16b_temp0.2_input"
    #  "starcoderbase-16b_temp0.8_input"
    #  "starcoderbase-7b_temp0.2_input"
    #  "starcoderbase-7b_temp0.8_input"
    #  "wizard-13b_temp0.2_input"
    #  "wizard-13b_temp0.8_input"
    #  "wizard-34b_temp0.2_input"
    #  "wizard-34b_temp0.8_input"
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
    --mode input
EOF
done