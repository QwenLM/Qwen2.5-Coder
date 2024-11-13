#!/bin/bash
export MODEL_DIR=${1}
export OUTPUT_DIR=${2}


export OPENAI_API_BASE=http://${HOST}:${PORT}/v1
export OPENAI_API_KEY=token-abc123

# define the tasks
TASKS=("spider-dev-chat" "bird-dev-chat")

for TASK in "${TASKS[@]}"; do
    # setting the mode and db_root
    if [ "$TASK" = "spider-dev-chat" ]; then
        MODE="spider"
        DB_ROOT="sql_suites/data/spider-dev/database"
        GOLD_SQLS="sql_suites/data/spider-dev/golden.sql"
    elif [ "$TASK" = "bird-dev-chat" ]; then
        MODE="bird"
        DB_ROOT="sql_suites/data/bird-dev/database"
        GOLD_SQLS="sql_suites/data/bird-dev/golden.sql"
    fi

    RESULTS_DIR="$OUTPUT_DIR/$TASK"
    mkdir -p "$RESULTS_DIR"

    # run the model
    python -u main.py \
        --backend openai \
        --model ${MODEL_DIR} \
        --tasks ${TASK} \
        --max_length_input 4096 \
        --max_new_tokens 1024 \
        --n_samples 1 \
        --batch_size 1 \
        --generation_only \
        --save_generations \
        --save_generations_path ${RESULTS_DIR}/generations.json \
        --chat_mode \
        2>&1 | tee ${RESULTS_DIR}/log.log 2>&1

    # convert the generations to sql
    python -u dog_utils.py \
        --in_f ${RESULTS_DIR}/generations.json \
        --out_f ${RESULTS_DIR}/generations.sql \
        2>&1 | tee -a ${RESULTS_DIR}/log.log

    # run the evaluation
    python -u sql_suites/eval.py \
        --db_root ${DB_ROOT} \
        --gen_sqls ${RESULTS_DIR}/generations.sql \
        --gold_sqls ${GOLD_SQLS} \
        --num_workers 16 \
        --mode ${MODE} \
        --exec_time_out 30 \
        --save_to ${RESULTS_DIR}/result.json \
        2>&1 | tee -a ${RESULTS_DIR}/log.log
done
