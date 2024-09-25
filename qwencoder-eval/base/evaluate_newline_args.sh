source /etc/profile.d/00-restore-env.sh
export LC_ALL="POSIX"

INPUT_MODEL=$1
OUTPUT_DIR=$2
TP=$3

TASKS=(
    "EvalPlus"
    # "MultiPL-E"
    # "CRUX-Eval"
    # "BigCodeBench"
)

echo "Tasks to run: (${TASKS[@]})"

export TOKENIZERS_PARALLELISM=false
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1


######################################
run_this() {
    for t in "${TASKS[@]}"; do if [[ "$t" == "$1" ]]; then return 0
    fi done 
    return 1
}
######################################


#[1]##################################
#[EvalPlus]###########################
if run_this "EvalPlus"; then
    export HUMANEVAL_OVERRIDE_PATH=eval_cache/evalplus/HumanEvalPlus-v0.1.9.jsonl
    export MBPP_OVERRIDE_PATH=eval_cache/evalplus/MbppPlus-v0.1.0.jsonl

    echo "Running EvalPlus::[HumanEval]"
    mkdir -p ${OUTPUT_DIR}/evalplus/humaneval
    python benchmarks/evalplus/generate.py \
        --model ${INPUT_MODEL} \
        --tp $TP \
        --bs 1 \
        --temperature 0 \
        --n_samples 1 \
        --greedy  \
        --save_folder ${OUTPUT_DIR}/evalplus/humaneval \
        --dataset humaneval

    echo "Running EvalPlus::[MBPP]"
    mkdir -p ${OUTPUT_DIR}/evalplus/mbpp
    python benchmarks/evalplus/generate.py \
        --model ${INPUT_MODEL} \
        --tp $TP \
        --bs 1 \
        --temperature 0 \
        --n_samples 1 \
        --greedy  \
        --save_folder ${OUTPUT_DIR}/evalplus/mbpp \
        --dataset mbpp
    echo "Finish: EvalPlus"
else
    echo "Skip: EvalPlus"
fi


#[2]##################################
#[MultiPL-E]##########################
if run_this "MultiPL-E"; then
    mkdir -p $OUTPUT_DIR/multipl-e
    python -u benchmarks/multiple-eval/eval_multiple_lang.py \
    --tp $TP \
    --modelpath ${INPUT_MODEL} \
    --logdir ${OUTPUT_DIR}/multipl-e
else
    echo "Skip: MultiPL-E"
fi


#[3]##################################
#[CRUX-Eval/CoT]######################
if run_this "CRUX-Eval"; then
    # split: I-CoT
    mkdir -p ${OUTPUT_DIR}/cruxeval/input-cot
    python -u benchmarks/cruxeval/inference/main.py \
        --model ${INPUT_MODEL} \
        --trust_remote_code  \
        --tasks input_prediction \
        --batch_size 1 \
        --save_generations_path ${OUTPUT_DIR}/cruxeval/input-cot/completion.json \
        --save_generations  \
        --tensor_parallel_size $TP \
        --cot

    python benchmarks/cruxeval/evaluation/evaluate_generations.py \
        --generations_path  ${OUTPUT_DIR}/cruxeval/input-cot/completion.json \
        --scored_results_path  ${OUTPUT_DIR}/cruxeval/input-cot/completion_scored.json \
        --mode input

    # split: O-CoT
    mkdir -p ${OUTPUT_DIR}/cruxeval/output-cot
    python -u benchmarks/cruxeval/inference/main.py \
        --model ${INPUT_MODEL} \
        --trust_remote_code  \
        --tasks output_prediction \
        --batch_size 1 \
        --save_generations_path ${OUTPUT_DIR}/cruxeval/output-cot/completion.json \
        --save_generations  \
        --tensor_parallel_size $TP \
        --cot

    python benchmarks/cruxeval/evaluation/evaluate_generations.py \
        --generations_path  ${OUTPUT_DIR}/cruxeval/output-cot/completion.json \
        --scored_results_path  ${OUTPUT_DIR}/cruxeval/output-cot/completion_scored.json \
        --mode output
else
    echo "Skip: CRUX-Eval"
fi


#[4]##################################
#[BigCodeBench]#######################
if run_this "BigCodeBench"; then
    # split: full
    mkdir -p ${OUTPUT_DIR}/bigcodebench/full
    python benchmarks/bigcodebench/generate.py \
        --model ${INPUT_MODEL} \
        --split complete \
        --subset full \
        --greedy  \
        --bs 1 \
        --temperature 0 \
        --n_samples 1 \
        --resume  \
        --backend vllm \
        --tp $TP \
        --save_path ${OUTPUT_DIR}/bigcodebench/full/completion.jsonl 

    conda_envs/bigcodebench_env/bin/python benchmarks/bigcodebench/sanitize.py \
        --samples ${OUTPUT_DIR}/bigcodebench/full/completion.jsonl \
        --calibrate

    conda_envs/bigcodebench_env/bin/python benchmarks/bigcodebench/evaluate.py \
        --split complete \
        --subset full \
        --no-gt \
        --samples ${OUTPUT_DIR}/bigcodebench/full/completion-sanitized-calibrated.jsonl

    # split: hard
    mkdir -p ${OUTPUT_DIR}/bigcodebench/hard
    python benchmarks/bigcodebench/generate.py \
        --model ${INPUT_MODEL} \
        --split complete \
        --subset hard \
        --greedy  \
        --bs 1 \
        --temperature 0 \
        --n_samples 1 \
        --resume  \
        --backend vllm \
        --tp $TP \
        --save_path ${OUTPUT_DIR}/bigcodebench/hard/completion.jsonl 

    conda_envs/bigcodebench_env/bin/python benchmarks/bigcodebench/sanitize.py \
        --samples ${OUTPUT_DIR}/bigcodebench/hard/completion.jsonl \
        --calibrate

    conda_envs/bigcodebench_env/bin/python benchmarks/bigcodebench/evaluate.py \
        --split complete \
        --subset hard \
        --no-gt \
        --samples ${OUTPUT_DIR}/bigcodebench/hard/completion-sanitized-calibrated.jsonl
else
    echo "Skip: BigCodeBench"
fi

#[X]##################################
python aggr_results.py ${OUTPUT_DIR}