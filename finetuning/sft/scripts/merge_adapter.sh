export PATH=/path/to/miniconda3/envs/qwen/bin:$PATH;
cd ./Qwen2.5-Coder-evaluation/sft/;
INPUT_MODEL_PATH=${1}
INPUT_ADAPTER_PATH=${2}
OUTPUT_PATH=${3}

INPUT_MODEL_PATH=${INPUT_MODEL_PATH:-"./pretrained_models"}
INPUT_ADAPTER_PATH=${INPUT_ADAPTER_PATH:-"./adapter"}
OUTPUT_PATH=${OUTPUT_PATH:-"./merged_models"}
python merge_adapter.py -input_model_path ${INPUT_MODEL_PATH} -input_adapter_path ${INPUT_ADAPTER_PATH} -output_path ${OUTPUT_PATH}

