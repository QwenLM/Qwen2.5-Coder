import os
from argparse import ArgumentParser
from pathlib import Path

import torch
from humaneval_qwen2_base import HumanEval as MultiPLERunner
from vllm import LLM

DATA_ROOT = str(Path(__file__).joinpath("../data").resolve())
print(f"{DATA_ROOT = }")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--logdir", type=str, default="")
    parser.add_argument("--modelpath", type=str, default="")
    parser.add_argument("--language", type=str, default="")
    parser.add_argument("--no_batching", action="store_true", default=False)
    args = parser.parse_args()

    logdir = args.logdir
    if logdir == "":
        logdir = "debug/"
    Path(logdir).mkdir(exist_ok=True, parents=True)

    evaluator = MultiPLERunner(
        data_root=DATA_ROOT,
        max_seq_len=4096,
        log_dir=logdir,
        n_sample=1,
        language=args.language,
        max_gen_len=500,
        no_batching=args.no_batching,
    )

    print(f"TP = {torch.cuda.device_count() = }")
    model = LLM(
        model=args.modelpath,
        tensor_parallel_size=torch.cuda.device_count(),
        gpu_memory_utilization=0.95,
        enforce_eager=True,
        disable_custom_all_reduce=True,
        distributed_executor_backend="ray",  # temp fix
    )

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    evaluator.eval_model(model)
