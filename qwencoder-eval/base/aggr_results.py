import json
from pathlib import Path
import argparse
from rich.console import Console
from rich.table import Table


file_cache = {}


def ret(file, *fields):
    if file not in file_cache:
        with Path(file).open("r") as f:
            content = json.load(f)
        file_cache[file] = content

    cur = file_cache[file]
    for field in fields:
        cur = cur[field]

    return cur


def err_payload():
    return {"-": "Err"}


def try_collect_evalplus(path):
    try:
        payload = {
            "HumanEval": ret(path / "humaneval" / "result.json", "humaneval", "pass@1"),
            "HumanEval+": ret(path / "humaneval" / "result.json", "humaneval+", "pass@1"),
            "MBPP": ret(path / "mbpp" / "result.json", "mbpp", "pass@1"),
            "MBPP+": ret(path / "mbpp" / "result.json", "mbpp+", "pass@1"),
        }
    except:
        payload = err_payload()

    return {"EvalPlus": payload}


def try_collect_multipl_e(path):
    try:
        lang_mapper = {"java": "Java", "cpp": "C++", "js": "JavaScript", "cs": "C#", "php": "php", "sh": "Shell", "ts": "TypeScript"}
        d = ret(path / "results.json")
        payload = {lang_mapper[k]: v for k, v in d.items()}
    except Exception as e:
        payload = err_payload()

    return {"MultiPL-E": payload}


def try_collect_cruxeval(path):
    try:
        payload = {
            "Input-CoT": ret(path / "input-cot" / "results.json", "pass@1"),
            "Output-CoT": ret(path / "output-cot" / "results.json", "pass@1"),
        }
    except:
        payload = err_payload()

    return {"CRUX-Eval": payload}


def try_collect_bigcodebench(path):
    try:
        payload = {
            "full": ret(path / "full" / "results.json", "pass@1"),
            "hard": ret(path / "hard" / "results.json", "pass@1"),
        }
    except:
        payload = err_payload()

    return {"BigCodeBench": payload}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()

    folder = Path(args.folder)
    assert folder.is_dir(), f"{folder} is not dir"

    collected = {}
    collected.update(try_collect_evalplus(folder / "evalplus"))
    collected.update(try_collect_multipl_e(folder / "multipl-e"))
    collected.update(try_collect_cruxeval(folder / "cruxeval"))
    collected.update(try_collect_bigcodebench(folder / "bigcodebench"))

    table = Table(title=f"[b][u][red]{args.folder}[/red][/u][/b]")
    table.add_column("Benchmark", justify="left", no_wrap=True)
    table.add_column("Metric", justify="left", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)

    for bench, details in collected.items():
        center = (len(details) - 1) // 2
        for idx, (k, v) in enumerate(details.items()):
            if not isinstance(v, str):
                v = f"{float(v):5.1f}"
            table.add_row(f"[b]{bench}[/b]" if idx == center else "", k, v)
        table.add_section()

    print()
    Console().print(table)
    print()

    saved = folder.joinpath("all_results.json")
    with Path(saved).open("w") as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)

    print(f"All results => {saved}")
