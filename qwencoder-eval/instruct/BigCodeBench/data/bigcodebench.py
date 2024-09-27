import hashlib
import json
import os
from typing import Dict
from pathlib import Path

from data.utils import (
    CACHE_DIR,
    completeness_check,
    get_dataset_metadata,
    make_cache,
    stream_jsonl,
)
from datasets import load_dataset

BIGCODEBENCH_OVERRIDE_PATH = os.environ.get("BIGCODEBENCH_OVERRIDE_PATH", None)
BIGCODEBENCH_HF = "bigcode/bigcodebench"
BIGCODEBENCH_VERSION = "v0.1.0_hf"


def _ready_bigcodebench_path(subset="full", version="default") -> str:
    if BIGCODEBENCH_OVERRIDE_PATH:
        return BIGCODEBENCH_OVERRIDE_PATH

    version = BIGCODEBENCH_VERSION if version == "default" else version
    url, path = get_dataset_metadata(BIGCODEBENCH_VERSION, subset)

    extra = "-" + subset if subset != "full" else ""

    try:
        dataset = load_dataset(BIGCODEBENCH_HF + extra, split=BIGCODEBENCH_VERSION)
        make_cache(url, dataset, path)
    except:
        if os.path.exists(path):
            os.remove(path)
        make_cache(url, None, path, gh=True)

    return path


def get_bigcodebench(err_incomplete=True, subset="full", version="default") -> Dict[str, Dict]:
    """Get BigCodeBench from BigCode's github repo and return as a list of parsed dicts.

    Returns:
        List[Dict[str, str]]: List of dicts with keys "complete_prompt", "instruct_prompt", "canonical_solution", "test", "entry_point"

    Notes:
        "task_id" is the identifier string for the task.
        "complete_prompt" is the prompt to be used for BigCodeBench-Complete.
        "instruct_prompt" is the prompt to be used for BigCodeBench-Instruct.
        "canonical_solution" is the ground-truth implementation
        "test" is the `unittest.TestCase` class.
        "entry_point" is the name of the function.
    """
    # # Check if open eval file exists in CACHE_DIR
    # data_path = _ready_bigcodebench_path(subset=subset, version=version)
    # data = {task["task_id"]: task for task in stream_jsonl(data_path)}
    # if err_incomplete:
    #     completeness_check("BigCodeBench", data)
    # return data
    # Load from local jsonl file
    file_path = Path(__file__).resolve().parent / f"bigcodebench_{subset}.json"
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def get_bigcodebench_hash(subset="full", version="default") -> str:
    """Get the hash of BigCodeBench.
    Returns:
        str: The hash of BigCodeBench
    """
    data_path = Path(__file__).resolve().parent / f"bigcodebench_{subset}.json"
    with open(data_path, "rb") as f:
        data = f.read()
    return hashlib.md5(data).hexdigest()
