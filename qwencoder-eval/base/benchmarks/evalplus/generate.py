import json
import re
import subprocess
from os import PathLike
from pathlib import Path
from typing import List
from vllm.distributed.parallel_state import destroy_distributed_environment, destroy_model_parallel
import torch
import gc

from model import DecoderBase, make_model


def codegen(
    target_file: PathLike,
    model: DecoderBase,
    dataset: str,
    greedy=False,
    n_samples=1,
    no_new_line_at_last=False,
):

    if dataset == "humaneval":
        from evalplus.data import get_human_eval_plus

        dataset = get_human_eval_plus()
    elif dataset == "mbpp":
        from evalplus.data import get_mbpp_plus

        dataset = get_mbpp_plus()

    task_ids, prompts = [], []
    for task_id, task in dataset.items():
        task_ids.append(task_id)
        if not no_new_line_at_last:  # qwen, +\n
            prompts.append(task["prompt"].strip() + "\n")
        else:  # no_new_line_at_last, strip it
            prompts.append(task["prompt"].strip())

    outputs = model.codegen(prompts, do_sample=not greedy, num_samples=n_samples)
    assert outputs, "No outputs from model!"

    with Path(target_file).open("w") as f:
        print(f"Saving ... => {target_file}")
        for task_id, prompt, completion in zip(task_ids, prompts, outputs):
            solution = prompt + completion if model.is_direct_completion() else completion
            d = {
                "task_id": task_id,
                "completion": solution,
            }
            json.dump(d, f, indent=None, ensure_ascii=False)
            f.write("\n")
    print(f"Save Done.")


def extract_scores(output):
    pattern = r"([\w+]+) \(.+?\)\n(pass@.+?).+?(0.\d+)"
    matches = re.findall(pattern, output)
    result = {name: {pass_k: round(float(score) * 100, 2)} for name, pass_k, score in matches}
    return result


def main(
    model: str,
    dataset: str,
    save_folder: str,
    bs: int = 1,
    n_samples: int = 1,
    temperature: float = 0.0,
    greedy: bool = False,
    backend: str = "vllm",
    no_batching: bool = False,
    tp: int = 1,
    chat_mode: bool = False,
    no_new_line_at_last: bool = False,
):
    assert dataset in ["humaneval", "mbpp"], f"Invalid dataset {dataset}"

    if greedy and (temperature != 0 or bs != 1 or n_samples != 1):
        temperature = 0.0
        bs = 1
        n_samples = 1
        print("Greedy decoding ON (--greedy): setting bs=1, n_samples=1, temperature=0")

    instruction_prefix = "Please provide a self-contained Python script that solves the following problem in a markdown code block:"
    response_prefix = "Below is a Python script with a self-contained function that solves the problem and passes corresponding tests:"

    # Model creation
    model_runner = make_model(
        model=model,
        backend=backend,
        batch_size=bs,
        temperature=temperature,
        dataset=dataset,
        tp=tp,
        instruction_prefix=instruction_prefix,
        response_prefix=response_prefix,
        no_batching=no_batching,
        chat_mode=chat_mode,
    )

    save_folder = Path(save_folder)
    save_folder.mkdir(exist_ok=True, parents=True)
    target_file = save_folder.joinpath("generated.jsonl")
    print(f"Generation will => {target_file}")

    print(f"{no_new_line_at_last = }")
    codegen(
        target_file=target_file,
        model=model_runner,
        dataset=dataset,
        greedy=greedy,
        n_samples=n_samples,
        no_new_line_at_last=no_new_line_at_last,
    )

    # Evaluation
    resolved = str(Path(target_file).resolve())
    print(f"Generation success, now testing...")
    command = f"evalplus.evaluate --dataset {dataset} --samples {resolved}"
    output = subprocess.check_output(command, shell=True).decode()
    results = extract_scores(output)
    print(f"Captured: {results}")

    save_metric_file = Path(save_folder).joinpath("result.json")
    with Path(save_metric_file).open("w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"=> {save_metric_file}")

    if backend == "vllm":
        print(f"Try cleanup...")
        destroy_model_parallel()
        destroy_distributed_environment()
        del model_runner.llm.llm_engine.model_executor
        del model_runner.llm
        gc.collect()
        torch.cuda.empty_cache()

    print(f"===============================")
    print(f"------ END OF EvalPlus --------")


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
