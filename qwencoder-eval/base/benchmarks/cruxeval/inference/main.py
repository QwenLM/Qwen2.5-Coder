# Copyright (c) Meta Platforms, Inc. and affiliates.

import fnmatch
import gc
import json
import random

import datasets
import numpy as np
import torch
import transformers
from generation_arguments import EvalArguments
from generator import Generator
from tasks import ALL_TASKS
from transformers import AutoTokenizer, HfArgumentParser
from vllm import LLM
from vllm.distributed.parallel_state import destroy_distributed_environment, destroy_model_parallel


class MultiChoice:

    def __init__(self, choices):
        self.choices = choices

    # Simple wildcard support (linux filename patterns)
    def __contains__(self, values):
        for value in values.split(","):
            if len(fnmatch.filter(self.choices, value)) == 0:
                return False

        return True

    def __iter__(self):
        for choice in self.choices:
            yield choice


def parse_args():
    parser = HfArgumentParser(EvalArguments)

    parser.add_argument(
        "--model",
        default="codeparrot/codeparrot-small",
        help="Model to evaluate, provide a repo name in Hugging Face hub or a local path",
    )
    parser.add_argument("--tensor_parallel_size", type=int, default=1, help="number of tensor parallel replicas")
    parser.add_argument(
        "--revision",
        default=None,
        help="Model revision to use",
    )
    parser.add_argument(
        "--use_auth_token",
        action="store_true",
        help="Use the token generated when running `huggingface-cli login` (necessary for private model).",
    )
    parser.add_argument(
        "--trust_remote_code",
        action="store_true",
        help="Use a model with custom code, this requires executing code by the author of the model.",
    )
    parser.add_argument(
        "--tasks",
        default=None,
        choices=MultiChoice(ALL_TASKS),
        help=f"Evaluation tasks from {ALL_TASKS}",
    )
    parser.add_argument(
        "--instruction_tokens",
        default=None,
        help="A series of instruction tokens used for instruction-tuning benchamrks separated by comma e.g. <user_message>,<end_user_message>,<assistant_message>",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Batch size for evaluation on each worker, can be larger for HumanEval",
    )
    parser.add_argument(
        "--max_length_generation",
        type=int,
        default=1024,
        help="Maximum length of generated sequence (prompt+generation)",
    )
    parser.add_argument(
        "--precision",
        type=str,
        default="bf16",
        help="Model precision, from: fp32, fp16 or bf16",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle the dataset before evaluation (useful for distributed inference)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only solve the first limit samples in the benchmark (useful with randomize dataset)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Starting index of samples in the benchmark to solve",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Ending index of samples in the benchmark to solve",
    )
    parser.add_argument(
        "--postprocess",
        action="store_false",
        help="Postprocess model outputs before execution, always on except during generation tests",
    )
    parser.add_argument(
        "--cot",
        action="store_true",
        help="Whether to use CoT",
    )
    parser.add_argument(
        "--save_generations",
        action="store_true",
        help="Whether to save code generations",
    )
    parser.add_argument(
        "--save_generations_path",
        type=str,
        default="generations.json",
        help="Path for saving the code generations",
    )
    parser.add_argument(
        "--save_references",
        action="store_true",
        help="Whether to save reference solutions/tests",
    )
    parser.add_argument(
        "--save_references_path",
        type=str,
        default="references.json",
        help="Path for saving the reference solutions/tests",
    )
    args = parser.parse_args()

    precision_map = {
        "fp32": "float32",
        "fp16": "float16",
        "bf16": "bfloat16",
    }

    args.precision = precision_map[args.precision]
    args.tasks = pattern_match(args.tasks.split(","), ALL_TASKS)
    assert len(args.tasks) == 1, f"Only one task is supported at the moment, you gave {args.tasks}"
    args.task_name = args.tasks[0]

    assert args.instruction_tokens is None, "Instruction tokens are not supported yet"
    return args


def pattern_match(patterns, source_list):
    """Returns a list containing all values of the source_list that
    match at least one of the patterns"""
    task_names = set()
    for pattern in patterns:
        for matching in fnmatch.filter(source_list, pattern):
            task_names.add(matching)
    return list(task_names)


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    transformers.logging.set_verbosity_error()
    datasets.logging.set_verbosity_error()

    model = LLM(
        model=args.model,
        dtype=args.precision,
        trust_remote_code=True,
        gpu_memory_utilization=0.95,
        tensor_parallel_size=args.tensor_parallel_size,
        max_model_len=8192,
        distributed_executor_backend="ray",
        enforce_eager=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        revision=args.revision,
        trust_remote_code=True,
        use_auth_token=args.use_auth_token,
        truncation_side="left",
        padding_side="right",
    )
    if not tokenizer.eos_token:
        if tokenizer.bos_token:
            tokenizer.eos_token = tokenizer.bos_token
            print("bos_token used as eos_token")
        else:
            raise ValueError("No eos_token or bos_token found")
    tokenizer.pad_token = tokenizer.eos_token

    generator = Generator(model, tokenizer, args)
    generations, generations_raw, references = generator.generate(args.task_name)

    with open(args.save_generations_path, "w") as fp:
        json.dump(generations, fp, indent=4)
        print(f"generations were saved at {args.save_generations_path}")

    path = args.save_generations_path
    path = path.split(".json")[0] + "_raw" + ".json"
    with open(path, "w") as fp:
        json.dump(generations_raw, fp, indent=4)
        print(f"generations were saved at {path}")
    if args.save_references:
        with open(args.save_generations_path, "w") as fp:
            json.dump(references, fp, indent=4)
            print("references were saved")

    print(f"Try cleanup...")
    destroy_model_parallel()
    destroy_distributed_environment()
    del model.llm_engine.model_executor
    del model
    gc.collect()
    torch.cuda.empty_cache()

    print(f"===============================")
    print(f"------ END OF CRUX-Eval --------")


if __name__ == "__main__":
    main()
