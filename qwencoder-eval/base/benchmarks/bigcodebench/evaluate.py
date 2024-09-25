import argparse
import json
import multiprocessing
import os
import pickle
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Tuple
from warnings import warn

import numpy as np
from termcolor import cprint
from tqdm import tqdm

from data import (
    get_bigcodebench,
    get_bigcodebench_hash,
    load_solutions,
)
from data.utils import CACHE_DIR
from eval import (
    PASS,
    compatible_eval_result,
    estimate_pass_at_k,
    untrusted_check,
)
from gen.util import trusted_check

# 1st item: the status
# 2nd item (optional): the detailed pass/fail boolean for each input
Result = Tuple[str, List[bool]]


def get_groundtruth(n_workers, problems, hashcode, check_gt_only, max_as_limit, max_data_limit, max_stack_limit):
    cache_file = os.path.join(CACHE_DIR, f"{hashcode}.pkl")
    if os.path.exists(cache_file):
        if check_gt_only:
            os.remove(cache_file)
        else:
            print(f"Load from ground-truth from {cache_file}")
            with open(cache_file, "rb") as f:
                return pickle.load(f)

    os.makedirs(CACHE_DIR, exist_ok=True)
    print("\nAsserting the groundtruth...")
    tbegin = time.time()

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        n_samples = 0
        expected_time = dict()

        for problem in problems.values():
            args = (
                problem["complete_prompt"] + "\n" + problem["canonical_solution"],
                problem["test"],
                problem["task_id"],
                max_as_limit,
                max_data_limit,
                max_stack_limit,
            )

            futures.append(executor.submit(trusted_check, *args))
            n_samples += 1

        for future in tqdm(as_completed(futures), total=n_samples):
            result = future.result()
            expected_time[result["task_id"]] = result["time"]

    print(f"Expected outputs computed in {time.time() - tbegin:.2f}s")

    if any(expected_time.values()):
        with open(cache_file, "wb") as f:
            pickle.dump(expected_time, f)

    return expected_time


def check_correctness(
    completion_id: int,
    problem: Dict[str, Any],
    solution: str,
    max_as_limit: float,
    max_data_limit: float,
    max_stack_limit: float,
    identifier=None,
    min_time_limit: float = 0.1,
    gt_time_limit: float = 2.0,
) -> Dict[str, Result]:  # {...}, "base" | "plus" -> (status, details)
    ret = {
        "completion_id": completion_id,
        "task_id": problem["task_id"],
        "_identifier": identifier,
        "solution": solution,
    }
    ret["base"] = untrusted_check(
        solution,
        problem["test"],
        problem["entry_point"],
        max_as_limit,
        max_data_limit,
        max_stack_limit,
        min_time_limit,
        gt_time_limit,
    )
    return ret


def evaluate(flags):
    if flags.parallel is None:
        n_workers = max(1, multiprocessing.cpu_count() // 2)
    else:
        n_workers = flags.parallel

    if flags.check_gt_only:
        # bypass the samples
        flags.samples = "__dummy__.jsonl"

    extra = flags.subset + "_" if flags.subset != "full" else ""
    if os.path.isdir(flags.samples):
        result_path = os.path.join(flags.samples, f"{extra}eval_results.json")
    else:
        assert flags.samples.endswith(".jsonl")
        result_path = flags.samples.replace(".jsonl", f"_{extra}eval_results.json")

    problems = get_bigcodebench(subset=flags.subset)
    dataset_hash = get_bigcodebench_hash(subset=flags.subset)

    if not flags.no_gt:
        expected_time = get_groundtruth(
            n_workers, problems, dataset_hash, flags.check_gt_only, flags.max_as_limit, flags.max_data_limit, flags.max_stack_limit
        )
    else:
        expected_time = {task_id: None for task_id in problems}

    gt_pass_rate = np.mean([1 if v is not None else 0 for k, v in expected_time.items() if k in problems])

    if os.path.isfile(result_path):
        print(f"Load from previous results from {result_path}")
        with open(result_path, "r") as f:
            results = json.load(f)

        results = compatible_eval_result(results)
    else:
        if flags.check_gt_only:

            if gt_pass_rate > 0.99:
                cprint(f"Groundtruth pass rate: {gt_pass_rate:.3f}", "green")
            else:
                cprint(f"Groundtruth pass rate: {gt_pass_rate:.3f}\nPlease be cautious!", "red")
            return

        results = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "eval": {},
        }

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = []
            completion_id = Counter()
            n_samples = 0
            eval_results = defaultdict(list)  # task_id ->
            remainings = set()

            print("Reading samples...")
            for sample in tqdm(load_solutions(flags.samples)):
                task_id = sample["task_id"]

                if task_id not in problems:
                    warn(f"Task {task_id} is found in the samples but not found in the dataset")
                    continue
                solution = sample["solution"] if "solution" in sample else problems[task_id]["complete_prompt"] + sample["completion"]
                if "sanitized-calibrated" in flags.samples:
                    solution = problems[task_id]["code_prompt"] + "\n    pass\n" + solution
                remainings.add(sample["_identifier"])
                args = (
                    completion_id[task_id],
                    problems[task_id],
                    solution,
                    flags.max_as_limit,
                    flags.max_data_limit,
                    flags.max_stack_limit,
                    sample["_identifier"],
                    flags.min_time_limit,
                    expected_time[task_id] if expected_time[task_id] else 20,
                )
                futures.append(executor.submit(check_correctness, *args))
                completion_id[task_id] += 1
                n_samples += 1

            assert n_samples == len(remainings), "Missing problems in unfinished"
            assert len(completion_id) == len(problems), "Missing problems in samples"

            def stucking_checker():
                while remainings:
                    last_size = len(remainings)
                    time.sleep(30)
                    if last_size != len(remainings) or len(remainings) == 0:
                        continue
                    # Potential stucking
                    warn("No samples had finished testing in the last 30s")
                    warn(f"{len(remainings)} samples to be tested: {remainings}")

            threading.Thread(target=stucking_checker).start()

            for future in tqdm(as_completed(futures), total=n_samples):
                result = future.result()
                remainings.remove(result["_identifier"])
                eval_results[result["task_id"]].append(result)

        # sort the results for each problem by completion_id
        for task_id, task_results in eval_results.items():
            task_results.sort(key=lambda x: x["completion_id"])
            results["eval"][task_id] = []
            for res in task_results:
                stat, details = res["base"]
                results["eval"][task_id].append(
                    {
                        "task_id": task_id,
                        "solution": res["solution"],
                        "status": stat,
                        "details": details,
                    }
                )

    # Calculate pass@k.
    total = np.array([len(r) for k, r in results["eval"].items() if k in problems])
    base_correct = []

    for key, res in results["eval"].items():
        if key not in problems:
            continue
        bc = sum([r["status"] == PASS for r in res])
        base_correct.append(bc)

    base_correct = np.array(base_correct)

    pass_at_k = {f"pass@{k}": 100 * estimate_pass_at_k(total, base_correct, k).mean() for k in [1, 5, 10, 25, 100] if total.min() >= k}

    mode = "-calibrated" if "sanitized-calibrated" in flags.samples else ""
    extra = flags.subset.capitalize()
    flags.split = flags.split.capitalize()
    cprint(f"BigCodeBench-{flags.split}{mode} ({extra})", "green")

    if flags.no_gt:
        cprint(f"Groundtruth is not checked", "yellow")
    else:
        if gt_pass_rate > 0.99:
            cprint(f"Groundtruth pass rate: {gt_pass_rate:.3f}", "green")
        else:
            cprint(f"Groundtruth pass rate: {gt_pass_rate:.3f}\nPlease be cautious!", "red")

    for k, v in pass_at_k.items():
        cprint(f"{k}:\t{v:.3f}", "green")

    # save results
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2)

    pass_at_k_path = os.path.join(os.path.dirname(result_path), "results.json")
    pass_at_k["model"] = os.path.basename(flags.samples).split("--bigcodebench-")[0]
    pass_at_k["calibrated"] = "sanitized-calibrated" in flags.samples
    pass_at_k["subset"] = flags.subset

    def save_pass_at_k():
        with open(pass_at_k_path, "w") as f:
            json.dump(pass_at_k, f, indent=2)

    save_pass_at_k()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, type=str, choices=["complete", "instruct"])
    parser.add_argument("--subset", default="full", type=str, choices=["full", "hard"])
    parser.add_argument("--samples", required=True, type=str)
    parser.add_argument("--parallel", default=None, type=int)
    parser.add_argument("--min-time-limit", default=1, type=float)
    parser.add_argument("--max-as-limit", default=128 * 1024, type=int)
    parser.add_argument("--max-data-limit", default=4 * 1024, type=int)
    parser.add_argument("--max-stack-limit", default=5, type=int)
    parser.add_argument("--check-gt-only", action="store_true", help="Check the groundtruth")
    parser.add_argument("--no-gt", action="store_true", help="Check the groundtruth")
    args = parser.parse_args()

    evaluate(args)


if __name__ == "__main__":
    main()
