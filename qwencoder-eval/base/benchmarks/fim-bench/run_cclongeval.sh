export LC_ALL="POSIX"

INPUT_MODEL=$1
OUTPUT_DIR=$2
TP=$3


export TOKENIZERS_PARALLELISM=false
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1

echo "Running CrossCodeLongEval"
mkdir -p ${OUTPUT_DIR}/cclong
python cclongeval/cclong.py \
    --tasks chunk_completion function_completion \
    --model_type codelm_right_cfc_left \
    --model_name_or_path ${INPUT_MODEL} \
    --cfc_seq_length 2048 \
    --right_context_length 2048 \
    --prompt_file cclongeval/processed_data/python_TASK_sparse_oracle.jsonl \
    --gen_length 50 \
    --max_seq_length 8192 \
    --output_dir ${OUTPUT_DIR} \
    --dataset cclong \
    --tp ${TP} \
    --ts_lib build/python-lang-parser.so \
    --language python