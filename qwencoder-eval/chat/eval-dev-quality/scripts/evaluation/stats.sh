#!/bin/bash

# Usage: script.sh <evaluation-file> <meta-file>

# Check if csvkit is installed.
if ! command -v csvsql &> /dev/null
then
    echo "Error: csvkit is not installed. Please install it using 'pip install csvkit'."
    exit 1
fi

evaluation_file="${1%.*}"
evaluation_table=$(basename "$1" .csv)
meta_table=$(basename "$2" .csv)

# SQL does not like hyphens in column names.
sed -i '1s/-/_/g' "$1"
sed -i '1s/-/_/g' "$2"

csvsql --query "\
    SELECT \
        model_id, \
        language, \
        SUM(score) AS score, \
        SUM(coverage) AS coverage, \
        SUM(files_executed) AS files_executed, \
        SUM(files_executed_maximum_reachable) AS files_executed_maximum_reachable, \
        SUM(generate_tests_for_file_character_count) AS generate_tests_for_file_character_count, \
        SUM(processing_time) AS processing_time, \
        SUM(response_character_count) AS response_character_count, \
        SUM(response_no_error) AS response_no_error, \
        SUM(response_no_excess) AS response_no_excess, \
        SUM(response_with_code) AS response_with_code, \
        SUM(tests_passing) AS tests_passing \
    FROM $evaluation_table \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY model_id, language\
    " "$1" > "${evaluation_file}-by-language.csv"

csvsql --query "\
    SELECT \
        model_id, \
        SUM(score) AS score, \
        SUM(CASE WHEN language = 'golang' THEN score ELSE 0 END) AS golang_score, \
        SUM(CASE WHEN language = 'java' THEN score ELSE 0 END) AS java_score, \
        SUM(CASE WHEN language = 'ruby' THEN score ELSE 0 END) AS ruby_score \
    FROM $evaluation_table \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY model_id\
    " "$1" > "${evaluation_file}-by-language-score.csv"

csvsql --query "\
    SELECT \
        model_id, \
        SUM(score) AS score, \
        SUM(CASE WHEN task = 'write-tests' THEN score ELSE 0 END) AS write_tests_score, \
        SUM(CASE WHEN task = 'transpile' THEN score ELSE 0 END) AS transpile_score, \
        SUM(CASE WHEN task = 'code-repair' THEN score ELSE 0 END) AS code_repair_score \
    FROM $evaluation_table \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY model_id\
    " "$1" > "${evaluation_file}-by-task-score.csv"

csvsql --query "\
    SELECT \
        model_id, \
        task, \
        language, \
        SUM(files_executed_maximum_reachable) AS files \
    FROM $evaluation_table \
    GROUP BY model_id, task, language\
    " "$1" > "${evaluation_file}-cases.csv"

csvsql --query "\
    SELECT \
        $evaluation_table.model_id, \
        model_name, \
        (completion + prompt + request) AS cost, \
        SUM(score) AS score, \
        SUM(coverage) AS coverage, \
        SUM(files_executed) AS files_executed, \
        SUM(files_executed_maximum_reachable) AS files_executed_maximum_reachable, \
        SUM(generate_tests_for_file_character_count) AS generate_tests_for_file_character_count, \
        SUM(processing_time) AS processing_time, \
        SUM(response_character_count) AS response_character_count, \
        SUM(response_no_error) AS response_no_error, \
        SUM(response_no_excess) AS response_no_excess, \
        SUM(response_with_code) AS response_with_code, \
        SUM(tests_passing) AS tests_passing \
    FROM $evaluation_table LEFT JOIN $meta_table ON $evaluation_table.model_id = $meta_table.model_id \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY $evaluation_table.model_id\
    " "$1" "$2" > "${evaluation_file}-by-model.csv"

csvsql --query "\
    SELECT \
        model_id, \
        task, \
        SUM(score) AS score, \
        SUM(coverage) AS coverage, \
        SUM(files_executed) AS files_executed, \
        SUM(files_executed_maximum_reachable) AS files_executed_maximum_reachable, \
        SUM(generate_tests_for_file_character_count) AS generate_tests_for_file_character_count, \
        SUM(processing_time) AS processing_time, \
        SUM(response_character_count) AS response_character_count, \
        SUM(response_no_error) AS response_no_error, \
        SUM(response_no_excess) AS response_no_excess, \
        SUM(response_with_code) AS response_with_code, \
        SUM(tests_passing) AS tests_passing \
    FROM $evaluation_table \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY model_id, task\
    " "$1" > "${evaluation_file}-by-task.csv"

csvsql --query "\
    SELECT \
        model_id, \
        task, \
        language, \
        SUM(score) AS score, \
        SUM(coverage) AS coverage, \
        SUM(files_executed) AS files_executed, \
        SUM(files_executed_maximum_reachable) AS files_executed_maximum_reachable, \
        SUM(generate_tests_for_file_character_count) AS generate_tests_for_file_character_count, \
        SUM(processing_time) AS processing_time, \
        SUM(response_character_count) AS response_character_count, \
        SUM(response_no_error) AS response_no_error, \
        SUM(response_no_excess) AS response_no_excess, \
        SUM(response_with_code) AS response_with_code, \
        SUM(tests_passing) AS tests_passing \
    FROM $evaluation_table \
    WHERE task NOT LIKE '%-symflower-fix' \
    GROUP BY model_id, task, language\
    " "$1" > "${evaluation_file}-by-task-by-language.csv"

csvsql --query "\
    SELECT \
        model_id, \
        SUM(CASE WHEN task NOT LIKE '%-symflower-fix' THEN score ELSE 0 END) AS score, \
        SUM(CASE WHEN task LIKE '%-symflower-fix' THEN score ELSE 0 END) AS score_fix, \
        SUM(CASE WHEN task NOT LIKE '%-symflower-fix' THEN files_executed ELSE 0 END) AS files_executed, \
        SUM(CASE WHEN task LIKE '%-symflower-fix' THEN files_executed ELSE 0 END) AS files_executed_fix \
    FROM $evaluation_table \
    WHERE (task LIKE 'transpile%' OR task LIKE 'write-tests%') AND language = 'golang' \
    GROUP BY model_id\
    " "$1" > "${evaluation_file}-by-symflower-fix.csv"
