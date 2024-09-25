import gc
import json
import os
from argparse import ArgumentParser
from pathlib import Path

import torch
from humaneval_qwen2_base_multilangs import HumanEval as MultiPLERunner
from vllm import LLM
from vllm.distributed.parallel_state import destroy_distributed_environment, destroy_model_parallel

DATA_ROOT = str(Path(__file__).joinpath("../data").resolve())
print(f"{DATA_ROOT = }")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--logdir", type=str, default="")
    parser.add_argument("--modelpath", type=str, default="")
    parser.add_argument("--tp", default=1, type=int)
    parser.add_argument("--just_eval", action="store_true", default=False)
    parser.add_argument("--langs", type=str, nargs="+", default=["java", "cpp", "js", "cs", "php", "sh", "ts"])
    parser.add_argument("--no_batching", action="store_true", default=False)
    parser.add_argument("--no_new_line_at_last", action="store_true", default=False)
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
        max_gen_len=500,
        no_batching=args.no_batching,
        no_new_line_at_last=args.no_new_line_at_last,
    )

    if not args.just_eval:
        print(f"TP = {args.tp = }")
        model = LLM(
            model=args.modelpath,
            max_model_len=8192,
            tensor_parallel_size=args.tp,
            gpu_memory_utilization=0.95,
            enforce_eager=True,
            disable_custom_all_reduce=True,
            trust_remote_code=True,
            distributed_executor_backend="ray",  # temp fix
        )
    else:
        model = None
        print(f"Skip model loading, just eval...")

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    aggr_result = evaluator.eval_model_multiple(model, langs=args.langs, just_eval=args.just_eval)

    res_file = Path(logdir).joinpath("results.json")
    with Path(res_file).open("w") as f:
        json.dump(aggr_result, f, ensure_ascii=False, indent=2)

    if not args.just_eval:
        print(f"Try cleanup...")
        destroy_model_parallel()
        destroy_distributed_environment()
        del model.llm_engine.model_executor
        del model
        gc.collect()
        torch.cuda.empty_cache()

    print(f"===============================")
    print(f"------ END OF MultiPL-E -------")
