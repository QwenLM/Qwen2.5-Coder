import gzip
import json
import os
from os import PathLike
from typing import Dict, Iterable

import tempdir
import wget
from appdirs import user_cache_dir

CACHE_DIR = user_cache_dir("bigcodebench")


def get_dataset_metadata(version: str, subset: str="full"):
    extra = "-" + subset.capitalize() if subset != "full" else ""
    url = f"https://github.com/bigcode-project/bigcodebench-annotation/releases/download/{version}/BigCodeBench{extra}.jsonl.gz"
    cache_path = os.path.join(CACHE_DIR, f"BigCodeBench{extra}-{version}.jsonl")
    return url, cache_path


def make_cache(gzip_url, hf_data, cache_path, gh=False):
    # Check if open eval file exists in CACHE_DIR
    
    if not os.path.exists(cache_path):
        if gh:
            # Install BigCodeBench dataset and parse as jsonl
            print(f"Downloading dataset from {gzip_url}")
            with tempdir.TempDir() as tmpdir:
                gz_path = os.path.join(tmpdir, f"data.jsonl.gz")
                wget.download(gzip_url, gz_path)

                with gzip.open(gz_path, "rb") as f:
                    data = f.read().decode("utf-8")

            # create CACHE_DIR if not exists
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)

            # Write the original open eval file to CACHE_DIR
            with open(cache_path, "w") as f:
                f.write(data)
        else:
            hf_data.to_json(cache_path)


def write_jsonl(
    filename: str, data: Iterable[Dict], append: bool = False, drop_builtin: bool = True
):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = "ab"
    else:
        mode = "wb"
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode="wb") as gzfp:
                for x in data:
                    if drop_builtin:
                        x = {k: v for k, v in x.items() if not k.startswith("_")}
                    gzfp.write((json.dumps(x) + "\n").encode("utf-8"))
    else:
        with open(filename, mode) as fp:
            for x in data:
                if drop_builtin:
                    x = {k: v for k, v in x.items() if not k.startswith("_")}
                fp.write((json.dumps(x) + "\n").encode("utf-8"))


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt") as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def load_solutions(sample_path: PathLike) -> Iterable[Dict]:
    """We accept two formats of inputs.
    + `sample.jsonl` which is the format from BigCodeBench, i.e., {task_id, completion or solution}.
    + A folder which contains sub-folders named after the task_id. Each sub-folder
    contains samples named in `[?].py` where `?` is the solution id starting with 0.
    Different from `sample.jsonl`, the solutions must be complete (with prompt prefix).
    """

    # if it is a file
    if os.path.isfile(sample_path):
        for i, sample in enumerate(stream_jsonl(sample_path)):
            assert (
                "completion" in sample or "solution" in sample
            ), "No completion or solution found in sample!"
            assert "solution" not in sample or isinstance(
                sample["solution"], str
            ), "Solution must be a string! If you have multiple solutions, please repeat the task_id."
            assert "completion" not in sample or isinstance(
                sample["completion"], str
            ), "Completion must be a string! If you have multiple solutions, please repeat the task_id."

            sample["_identifier"] = (
                sample["task_id"] + f" (line {i+1} in {sample_path})"
            )
            yield sample
    else:
        # if it is a folder
        for task_id in os.listdir(sample_path):
            task_path = os.path.join(sample_path, task_id)
            if not os.path.isdir(task_path):
                continue

            for solution_id in os.listdir(task_path):
                solution_path = os.path.join(task_path, solution_id)
                if os.path.isfile(solution_path) and solution_path.endswith(".py"):
                    with open(solution_path, "r") as f:
                        completion = f.read()
                    yield {
                        "_identifier": solution_path,
                        "_path": solution_path,
                        "task_id": task_id.replace("_", "/"),
                        "solution": completion,
                    }


def write_directory(directory: PathLike, data: Iterable[Dict]):
    os.makedirs(directory, exist_ok=True)
    counters = {}
    for sample in data:
        assert "solution" in sample, "Samples must come with `solution` field!"
        task_id = sample["task_id"].replace("/", "_")
        task_dir = os.path.join(directory, task_id)
        os.makedirs(task_dir, exist_ok=True)
        if task_id not in counters:
            counters[task_id] = 0
        sample_id = counters[task_id]
        with open(os.path.join(task_dir, f"{sample_id}.py"), "w") as f:
            f.write(sample["solution"])
        counters[task_id] += 1


def completeness_check(name, data):
    for task_id, task in data.items():
        for key in [
            "complete_prompt",
            "instruct_prompt",
            "canonical_solution",
            "code_prompt",
            "test",
            "entry_point"
        ]:
            assert key in task, f"{key} not found in {name} #{task_id}!"


def to_raw(string):
    return string.encode("unicode-escape").decode().replace("\\\\", "\\")
