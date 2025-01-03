cd ./finetuning/dpo/scripts;
DATA_PATH="./dpo_data/code_dpo_all.jsonl"
PRETRAINED_MODEL=${1}
OUTPUT_DIR=${2}
PRETRAINED_MODEL=${PRETRAINED_MODEL:-"./pretrained_models/Qwen/Qwen2.5-Coder-1.5B-Instruct/"}
BATCH_SIZE=512
MICRO_BATCH_SIZE=4
LR=5e-5
WARMUP_STEPS=100
WEIGHT_DECAY=0.0
MAX_LENGTH=3072
EXTRA_ARGS="" #"--gradient_checkpointing" --include_num_input_tokens_seen True --use_flash_attention
OUTPUT_DIR=${OUTPUT_DIR:-"./hf_checkpoints/1.5B/dpo//lr${LR}-wr${WARMUP_STEPS}-wd${WEIGHT_DECAY}-bsz${BATCH_SIZE}-maxlen${MAX_LENGTH}/"}
bash dpo_qwencoder.sh ${DATA_PATH} ${PRETRAINED_MODEL} ${OUTPUT_DIR} ${MICRO_BATCH_SIZE} ${BATCH_SIZE} ${LR} ${WARMUP_STEPS} ${WEIGHT_DECAY} ${MAX_LENGTH} "${EXTRA_ARGS}"
