########################
# unset PYTORCH_CUDA_ALLOC_CONF;
# export NCCL_IB_TC=136
# export NCCL_IB_SL=5
# export NCCL_IB_GID_INDEX=3
# export NCCL_SOCKET_IFNAME=bond1
# export NCCL_DEBUG=INFO
# export NCCL_IB_HCA=mlx5_bond
# export NCCL_IB_TIMEOUT=22
# export NCCL_IB_QPS_PER_CONNECTION=8
# export NCCL_MIN_NCHANNELS=4
# export NCCL_NET_PLUGIN=none
########################


export PATH=./miniconda3/envs/trl/bin:$PATH
echo ${PATH}
DATA_PATH=${1}
SFT_MODEL=${2}
OUTPUT_DIR=${3}

MICRO_BATCH_SIZE=${4}
MICRO_BATCH_SIZE=${MICRO_BATCH_SIZE:-"1"}
BATCH_SIZE=${5}
BATCH_SIZE=${BATCH_SIZE:-"2048"}

LR=${6}
WARMUP_STEPS=${7}
WEIGHT_DECAY=${8}
MAX_LENGTH=${9}
EXTRA_ARGS=${10}
echo ${EXTRA_ARGS}
LR=${LR:-"3e-4"}
MIN_LR=${MIN_LR:-"5e-6"}
WARMUP_STEPS=${WARMUP_STEPS:-"100"}
WEIGHT_DECAY=${WEIGHT_DECAY:-"0.0"}
MAX_LENGTH=${MAX_LENGTH:-"1280"}

DATA_PATH=${DATA_PATH:-"/path/to/processed/sft.jsonl"}
SFT_MODEL=${SFT_MODEL:-"/path/to/pretrained_models/Qwen/Qwen2.5-Coder-1.5B/"}
OUTPUT_DIR=${OUTPUT_DIR:-"/path/to/checkpoints/lr${LR}-wr${WARMUP_STEPS}-wd${WEIGHT_DECAY}-bsz${BATCH_SIZE}-maxlen${MAX_LENGTH}/"}


GPUS_PER_NODE=$(python -c "import torch; print(torch.cuda.device_count());")
MASTER_ADDR=${MASTER_ADDR:-localhost}
NNODES=${WORLD_SIZE:-1}
NODE_RANK=${RANK:-0}
WORLD_SIZE=$(($GPUS_PER_NODE*$NNODES))
MASTER_PORT=${MASTER_PORT:-6105}
DISTRIBUTED_ARGS="
    --nproc_per_node $GPUS_PER_NODE \
    --nnodes $NNODES \
    --node_rank $NODE_RANK \
    --master_addr $MASTER_ADDR \
    --master_port $MASTER_PORT
"
# DISTRIBUTED_ARGS="
#     --num_gpus=$GPUS_PER_NODE \
#     --num_nodes=$NNODES \
#     --node_rank=$NODE_RANK \
#     --master_addr=$MASTER_ADDR \
#     --master_port=$MASTER_PORT \
# "
DEEPSPEED_CONFIG="./configs/ds_z3_offload_config.json"


GRAD_ACCU=$(($BATCH_SIZE / $WORLD_SIZE / $MICRO_BATCH_SIZE))
echo "LR: ${LR}, WARMUP_STEPS: ${WARMUP_STEPS}"
echo "SFT Model" ${SFT_MODEL}
echo "BATCH SIZE" ${BATCH_SIZE}
echo "WORLD_SIZE" ${WORLD_SIZE} "MICRO BATCH SIZE" ${MICRO_BATCH_SIZE} "GRAD_ACCU" ${GRAD_ACCU}

echo $DISTRIBUTED_ARGS
DATASET_WORKERS=32
BETA=0.1
ROOT_PATH="./finetuning/dpo"
cd ${ROOT_PATH}
torchrun ${DISTRIBUTED_ARGS} train.py \
    --model_name_or_path  ${SFT_MODEL} \
    --dataset_name $DATA_PATH \
    --max_length ${MAX_LENGTH} \
    --max_prompt_length ${MAX_LENGTH} \
    --model_max_length ${MAX_LENGTH} \
    --output_dir ${OUTPUT_DIR} \
    --num_train_epochs 1 \
    --max_steps 1000 \
    --per_device_train_batch_size ${MICRO_BATCH_SIZE} \
    --gradient_accumulation_steps ${GRAD_ACCU} \
    --per_device_eval_batch_size 4 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --dataset_num_proc ${DATASET_WORKERS} \
    --save_steps 1000 \
    --save_total_limit 10 \
    --learning_rate ${LR} \
    --weight_decay ${WEIGHT_DECAY} \
    --warmup_steps ${WARMUP_STEPS} \
    --lr_scheduler_type "cosine" \
    --logging_strategy "steps" \
    --logging_steps 1 \
    --deepspeed ${DEEPSPEED_CONFIG} \
    --report_to "tensorboard" \
    --bf16 True \
    --tf32 True \
    --truncate_source True \
    --beta ${BETA} \
    ${EXTRA_ARGS}
