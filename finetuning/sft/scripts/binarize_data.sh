export PATH=/path/to/miniconda3/envs/qwen/bin:$PATH;
cd ./Qwen2.5-Coder-evaluation/sft/;
INPUT_PATH=${1}
OUTPUT_PATH=${2}
TOKENIZER_PATH=${3}
INPUT_PATH=${INPUT_PATH:-"./raw/sft.jsonl"}
OUTPUT_PATH=${OUTPUT_PATH:-"./processed/sft.jsonl"}
TOKENIZER_PATH=${TOKENIZER_PATH:-"./pretrained_models/Qwen/Qwen2___5-Coder-1___5B/"}
python binarize_data.py -input_path ${INPUT_PATH} -output_path ${OUTPUT_PATH} -workers 64 -tokenizer_path ${TOKENIZER_PATH}