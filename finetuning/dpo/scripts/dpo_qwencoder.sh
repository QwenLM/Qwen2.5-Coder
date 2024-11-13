#!/bin/bash
EXP_NAME=${1}
DATA_PATH=${2}
SFT_MODEL=${3}
OUTPUT_DIR=${4}

LOGFILE_PATH="logs/${EXP_NAME}.log"
mkdir logs

echo "Output Path" ${OUTPUT_DIR}
echo "Training Data" ${DATA_PATH}
echo "SFT Model" ${SFT_MODEL}

BETA=0.1
LR=5e-6
WARMUP_RATIO=0.1

deepspeed train.py \
    --deepspeed "./configs/ds_config_zero3.json" \
    --model_name_or_path ${SFT_MODEL} \
    --dataset_name ${DATA_PATH} \
    --output_dir ${OUTPUT_DIR} \
    --save_strategy "epoch" \
    --per_device_train_batch_size 2 \
    --per_device_eval_batch_size 2 \
    --evaluation_strategy "steps" \
    --eval_steps 100 \
    --num_train_epochs 1 \
    --gradient_accumulation_steps 2 \
    --gradient_checkpointing True \
    --learning_rate ${LR} \
    --beta ${BETA} \
    --warmup_ratio ${WARMUP_RATIO} \
    --logging_steps 1 \
    --max_length 2048 \
    --bf16 True \
    --tf32 True >> ${LOGFILE_PATH} 2>&1