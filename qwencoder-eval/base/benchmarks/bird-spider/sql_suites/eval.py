import argparse
import json
import multiprocessing as mp
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from func_timeout import FunctionTimedOut, func_timeout
from rich.console import Console
from rich.table import Table
from tqdm.contrib.concurrent import process_map

from comparator import quick_rej, result_eq
from utils import read_packed_sql


def execute_sql(db_file, gen_sql, gold_sql, cmp_method="spider"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        cursor.execute(gen_sql)
        predicted_res = cursor.fetchall()

        cursor.execute(gold_sql)
        ground_truth_res = cursor.fetchall()

        res = 0
        if cmp_method == "spider":
            order_matters = "orderby" in re.sub(r"\s+", gold_sql.lower(), "")
            if result_eq(predicted_res, ground_truth_res, order_matters=order_matters):
                res = 1
        elif cmp_method == "bird":
            if set(predicted_res) == set(ground_truth_res):
                res = 1

    return res


def find_detail(reason):
    patterns = [
        "ambiguous column name",
        "no such column",
        "no such table",
        "no such function",
        "syntax error",
    ]

    for p in patterns:
        if p in reason:
            return p
    return "others"


def execute_model(packed):
    db_file, gen_sql, gold_sql, exec_time_out, mode = packed

    status = "failed"
    detail = None
    try:
        res = func_timeout(exec_time_out, execute_sql, args=(db_file, gen_sql, gold_sql, mode))
        status = "success"
    except FunctionTimedOut:
        status = "timeout"
        res = 0
    except Exception as e:
        detail = find_detail(str(e))
        status = "error"
        res = 0

    result = {"res": res, "status": status, "detail": detail}
    return result


def run_sqls_parallel(packed_payload, mode, num_workers=64, exec_time_out=30.0):
    ret = process_map(
        execute_model,
        [(*payload, exec_time_out, mode) for payload in packed_payload],
        max_workers=num_workers,
        chunksize=10,
    )
    return ret


def mean(arr):
    if arr:
        return sum(arr) / len(arr)
    else:
        return 0.0


def compute_score(exec_results):
    # exec_dict = {"simple": [], "moderate": [], "challenging": [], "all": []}
    # acc_dict = {"simple": [], "moderate": [], "challenging": [], "all": []}
    # num_dict = {"simple": 0, "moderate": 0, "challenging": 0, "all": 0}
    exec_dict = {"all": []}
    acc_dict = {"all": []}
    num_dict = {"all": 0}
    error_types = defaultdict(lambda: 0)

    for exec_ret in exec_results:
        can_exec_score = 1 if exec_ret["status"] == "success" else 0
        exec_dict["all"].append(can_exec_score)

        acc_score = exec_ret["res"]
        acc_dict["all"].append(acc_score)
        num_dict["all"] += 1
        error_detail = exec_ret["detail"]
        if error_detail:
            error_types[error_detail] += 1

    error_types = dict(error_types)
    for k, v in error_types.items():
        print(f"\t{k}: {v}")

    acc_score = {k: mean(v) for k, v in acc_dict.items()}
    exec_score = {k: mean(v) for k, v in exec_dict.items()}

    return acc_score, exec_score, num_dict, error_types


def print_scores(acc_score, exec_score, num_dict):
    to_percent = lambda num: f"{num:.2%}"

    table = Table(show_footer=True)
    table.add_column("Part", footer="All", justify="right")
    table.add_column("Executable", footer=to_percent(exec_score["all"]), justify="right")
    table.add_column("Accuracy", footer=to_percent(acc_score["all"]), justify="right")

    # for level in ["simple", "moderate", "challenging"]:
    #     table.add_row(level, to_percent(exec_score[level]), to_percent(acc_score[level]))
    Console().print(table)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--gen_sqls", type=str, required=True, default="")
    args_parser.add_argument("--gold_sqls", type=str, required=True, default="")
    args_parser.add_argument("--db_root", type=str, required=True, default="")
    args_parser.add_argument("--num_workers", type=int, default=1)
    args_parser.add_argument("--exec_time_out", type=float, default=30.0)
    args_parser.add_argument("--mode", type=str, required=True, choices=["bird", "spider"])
    args_parser.add_argument("--save_to", type=str, default=None)
    args_parser.add_argument("--debug", default=False, action="store_true")
    args = args_parser.parse_args()

    gen_sqls, gen_dbs = read_packed_sql(args.gen_sqls, db_root=args.db_root)
    gold_sqls, gold_dbs = read_packed_sql(args.gold_sqls, db_root=args.db_root)

    if not args.debug:
        assert gen_dbs == gold_dbs, f"{len(gen_dbs) = } != {len(gold_dbs) = }"
        assert len(gen_sqls) == len(gold_sqls) == len(gold_dbs)

    packed_payload = zip(gold_dbs, gen_sqls, gold_sqls)

    exec_result = run_sqls_parallel(
        packed_payload,
        mode=args.mode,
        num_workers=args.num_workers,
        exec_time_out=args.exec_time_out,
    )

    acc_score, exec_score, num_dict, error_counter = compute_score(exec_result)
    print_scores(acc_score, exec_score, num_dict)
    metric_dict = {"acc": acc_score, "exec": exec_score, "nums": num_dict, "error_counter": error_counter}

    if args.save_to is not None:
        file_to_save = Path(args.save_to)
        with file_to_save.open("w") as f:
            json.dump(metric_dict, f, indent=2)
