from data import get_bigcodebench
import os
import shutil
import json
import argparse


def inspection(args):
    """
    Write a series of files for each task into a directory.
    
    Each Directory Structure:
    -- task_id
        -- ground_truth.py: prompt + canonical_solution
        -- completion.py: prompt + completion
        -- execution_trace.txt: execution trace
    """
    path = os.path.join("inspect", args.eval_results.split("/")[-1].replace(".json", ""))
    if args.in_place:
        shutil.rmtree(path, ignore_errors=True)
    if not os.path.exists(path):
        os.makedirs(path)
    problems = get_bigcodebench()

    eval_results = json.load(open(args.eval_results, "r"))
    for task_id, results in eval_results["eval"].items():
        if all(result["status"] == "pass" for result in results):
            continue
        task_path = os.path.join(path, task_id)
        if not os.path.exists(task_path):
            os.makedirs(task_path)
        task_id_data = problems[task_id]
        with open(os.path.join(task_path, "ground_truth.py"), "w") as f:
            f.write(task_id_data[f"{args.subset}_prompt"] + "\n\n" + task_id_data["canonical_solution"])

        # write test
        with open(os.path.join(task_path, "test_case.py"), "w") as f:
            f.write(task_id_data["test"])

        for i, result in enumerate(results):
            with open(os.path.join(task_path, f"completion_{i}.py"), "w") as f:
                f.write(result["solution"])

        for i, result in enumerate(results):
            with open(os.path.join(task_path, f"complete_{i}_execution_trace.txt"), "w") as f:
                for test_case, execution_trace in result["details"].items():
                    f.write(f"Test Case: {test_case}\n\n")
                    f.write(execution_trace)
                    f.write("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-results", required=True, type=str)
    parser.add_argument("--subset", required=True, type=str)
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    inspection(args)


if __name__ == "__main__":
    main()
