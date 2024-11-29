export LC_ALL="POSIX"

INPUT_MODEL=$1
OUTPUT_DIR=$2/humaneval-infilling
TP=$3


mkdir -p ${OUTPUT_DIR}/humaneval-infilling
python hm_fim/humaneval_fim.py \
    --model_type codelm_leftright_context \
    --model_name_or_path ${INPUT_MODEL} \
    --output_dir ${OUTPUT_DIR} \
    --tp ${TP}