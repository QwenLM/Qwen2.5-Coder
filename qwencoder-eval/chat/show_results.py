import re
import sys
from prettytable import PrettyTable
import json
import numpy as np


def show_evalplus(results_path):
    evalplus_humaneval = open(f"{results_path}/evalplus/humaneval_results.txt").read()
    match = re.search(r"pass@1:(.*?)\n.*?pass@1:(.*?)\n", evalplus_humaneval, flags=re.DOTALL)
    results.extend([match.group(1).strip(), match.group(2).strip()])

    evalplus_mbpp = open(f"{results_path}/evalplus/mbpp_results.txt").read()
    match = re.search(r"pass@1:(.*?)\n.*?pass@1:(.*?)\n", evalplus_mbpp, flags=re.DOTALL)
    results.extend([match.group(1).strip(), match.group(2).strip()])

    results = [float(s) for s in results]
    results.insert(0, np.average(results))
    table = PrettyTable()
    table.field_names = [
        "EvalPlus (avg)",
        'EvalPlus (HumanEval)',
        'EvalPlus (HumanEval+)',
        'EvalPlus (MBPP)',
        'EvalPlus (MBPP+)',
    ]
    table.add_row(results)
    return str(table)


def show_livecodebench(results_path):
    livecodebench = json.load(open(f"{results_path}/livecodebench/results.json"))
    livecodebench_pass_at_1, livecodebench_pass_at_5 = livecodebench[0]["pass@1"], livecodebench[0]["pass@5"]
    results.extend([livecodebench_pass_at_1, livecodebench_pass_at_5])
    results.insert(0, np.average(results))
    table = PrettyTable()
    table.field_names = [
        "Livecodebench (avg)",
        "livecodebench (pass@1)",
        "livecodebench (pass@10)",
    ]
    table.add_row(results)
    return str(results)


def show_multiple(results_path):
    results = []
    lgs = ["python", "cs", "cpp", "java", "php", "ts", "sh", "js"]
    for lg in lgs:
        score = json.load(open(f"{results_path}/MultiPL-E/results_{lg}.jsonl"))
        results.append(score["pass@1"])
    results = [float(r) for r in results]
    results.insert(0, np.average(results))
    table = PrettyTable()
    table.field_names = ["MultiPL-E (avg)", "MultiPL-E (python)", "MultiPL-E (cs)", "MultiPL-E (cpp)", "MultiPL-E (java)", "MultiPL-E (php)", "MultiPL-E (ts)", "MultiPL-E (sh)", "MultiPL-E (js)"]
    table.add_row(results)
    return str(results)


def main(results_path="code-evaluation/results/"):
    tabs = []
    tabs.append(show_evalplus(results_path))
    tabs.append(show_evalplus(results_path))
    tabs.append(show_evalplus(results_path))
    with open(f"{results_path}/all_results.txt", "w") as w:
        for tab in tabs:
            w.write(f"{tab}\n")
        print(f"All results saving to {results_path}/all_results.txt")


if __name__ == "__main__":
    args = sys.argv
    results_path = "results_path"
    if len(args) > 1:
        results_path = args[1]
    main(results_path=results_path)
