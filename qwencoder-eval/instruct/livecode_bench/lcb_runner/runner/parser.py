import os
import torch
import argparse

from lcb_runner.utils.scenarios import Scenario


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-3.5-turbo-0301",
        help="Name of the model to use matching `lm_styles.py`",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default = None,
        help="Name of the model to use matching `lm_styles.py`",
    )
    parser.add_argument(
        "--output_name",
        type=str,
        default = None,
        help="Name of the model to use matching `lm_styles.py`",
    )
    parser.add_argument(
        "--scenario",
        type=Scenario,
        default=Scenario.codegeneration,
        help="Type of scenario to run",
    )
    parser.add_argument(
        "--n", type=int, default=10, help="Number of samples to generate"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.2, help="Temperature for sampling"
    )
    parser.add_argument("--top_p", type=float, default=0.95, help="Top p for sampling")
    parser.add_argument(
        "--max_tokens", type=int, default=1200, help="Max tokens for sampling"
    )
    parser.add_argument(
        "--multiprocess",
        default=0,
        type=int,
        help="Number of processes to use for generation (vllm runs do not use this)",
    )
    parser.add_argument(
        "--stop",
        default="###",
        type=str,
        help="Stop token (use `,` to separate multiple tokens)",
    )
    parser.add_argument("--continue_existing", action="store_true")
    parser.add_argument(
        "--use_cache", action="store_true", help="Use cache for generation"
    )
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate the results")
    parser.add_argument(
        "--num_process_evaluate",
        type=int,
        default=12,
        help="Number of processes to use for evaluation",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default = None,
        help="Number of processes to use for evaluation",
    )

    parser.add_argument("--timeout", type=int, default=18, help="Timeout for evaluation")
    parser.add_argument(
        "--tensor_parallel_size",
        type=int,
        default=-1,
        help="Tensor parallel size for vllm",
    )
    parser.add_argument("--dtype", type=str, default="bfloat16", help="Dtype for vllm")

    args = parser.parse_args()

    args.stop = args.stop.split(",")

    if args.tensor_parallel_size == -1:
        args.tensor_parallel_size = torch.cuda.device_count()

    if args.multiprocess == -1:
        args.multiprocess = os.cpu_count()

    return args


def test():
    args = get_args()
    print(args)


if __name__ == "__main__":
    test()
