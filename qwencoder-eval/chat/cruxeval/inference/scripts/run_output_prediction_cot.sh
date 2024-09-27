#!/bin/bash

dirs=(
    # "codellama-7b"
    # "codellama-13b"
    # "codellama-34b"
)

models=(
    # "codellama/CodeLlama-7b-hf"
    # "codellama/CodeLlama-13b-hf"
    # "codellama/CodeLlama-34b-hf"
)

temperatures=(0.2 0.8)

for ((i=0; i<${#models[@]}; i++)); do
    model=${models[$i]}
    base_dir=${dirs[$i]}
    echo $model
    for temperature in "${temperatures[@]}"; do
        dir="${base_dir}+cot_temp${temperature}_output"
        cat <<EOF > temp_sbatch_script.sh
#!/bin/bash
#SBATCH --output=slurm_logs/slurm-%A-%a.out
#SBATCH --error=slurm_logs/slurm-%A-%a.err
#SBATCH --partition=YOUR_PARTITION_HERE
#SBATCH --array=0-1
#SBATCH --cpus-per-task=10
#SBATCH --gpus=1
#SBATCH --gpus-per-task=1
#SBATCH --mem=0GB
#SBATCH --time=03:00:00

dir=$dir
SIZE=800
GPUS=2

i=\$SLURM_ARRAY_TASK_ID
ip=\$((\$i+1))

echo \$dir
mkdir -p model_generations_raw/\$dir

string="Starting iteration \$i with start and end  \$((\$i*SIZE/GPUS)) \$((\$ip*SIZE/GPUS))"
echo \$string

python main.py \
    --model $model \
    --use_auth_token \
    --trust_remote_code \
    --tasks output_prediction \
    --batch_size 10 \
    --n_samples 10 \
    --max_length_generation 2048 \
    --precision bf16 \
    --limit \$SIZE \
    --temperature $temperature \
    --save_generations \
    --save_generations_path model_generations_raw/\${dir}/shard_\$((\$i)).json \
    --start \$((\$i*SIZE/GPUS)) \
    --end \$((\$ip*SIZE/GPUS)) \
    --cot \
    --shuffle
EOF
        sbatch temp_sbatch_script.sh
        rm temp_sbatch_script.sh
    done
done