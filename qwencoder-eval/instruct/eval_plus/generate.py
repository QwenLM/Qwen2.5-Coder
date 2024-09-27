import argparse
import os
from os import PathLike
import sys
eval_plus_path = os.path.dirname(os.path.abspath(__file__)) + "/evalplus/"
sys.path = [eval_plus_path] + sys.path
from model import DecoderBase, make_model
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)


MODEL_MAPPING = {
    #  Can be either repo's name or /path/to/model
    "codeqwen": {
        "base": "Qwen/CodeQwen1.5-7B",
        "chat": "Qwen/CodeQwen1.5-7B-Chat",
        "chat-awq": "Qwen/CodeQwen1.5-7B-Chat-AWQ",
    },
    "qwen2": {
        "chat": "Qwen/CodeQwen1.5-7B-Chat",
    },
}


def construct_contract_prompt(prompt: str, contract_type: str, contract: str) -> str:
    if contract_type == "none":
        return prompt
    elif contract_type == "docstring":
        # embed within the docstring
        sep = ""
        if '"""' in prompt:
            sep = '"""'
        elif "'''" in prompt:
            sep = "'''"
        assert sep != ""
        l = prompt.split(sep)
        contract = "\n".join([x.split("#")[0] for x in contract.splitlines()])
        l[1] = l[1] + contract + "\n" + " " * (len(contract) - len(contract.lstrip()) - 1)
        return sep.join(l)
    elif contract_type == "code":
        # at the beginning of the function
        contract = "\n".join([x.split("#")[0] for x in contract.splitlines()])
        return prompt + contract


def code_generate(args, workdir: PathLike, model: DecoderBase, id_range=None):
    with Progress(
        TextColumn(f"{args.dataset} •" + "[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
    ) as p:
        if args.dataset == "humaneval":
            from evalplus.data import get_human_eval_plus
            dataset = get_human_eval_plus()
        elif args.dataset == "mbpp":
            from evalplus.data import get_mbpp_plus
            dataset = get_mbpp_plus()

        for task_id, task in p.track(dataset.items()):
            if id_range is not None:
                id_num = int(task_id.split("/")[1])
                low, high = id_range
                if id_num < low or id_num >= high:
                    p.console.print(f"Skipping {task_id} as it is not in {id_range}")
                    continue

            p_name = task_id.replace("/", "_")
            if args.contract_type != "none" and task["contract"] == "":
                continue
            os.makedirs(os.path.join(workdir, p_name), exist_ok=True)
            log = f"Codegen: {p_name} @ {model}"
            n_existing = 0
            if args.resume:
                # count existing .py files
                n_existing = len([f for f in os.listdir(os.path.join(workdir, p_name)) if f.endswith(".py")])
                if n_existing > 0:
                    log += f" (resuming from {n_existing})"

            nsamples = args.n_samples - n_existing
            p.console.print(log)

            sidx = args.n_samples - nsamples
            while sidx < args.n_samples:
                model.dataset = args.dataset
                outputs = model.codegen(
                    construct_contract_prompt(task["prompt"], args.contract_type, task["contract"]).strip(),
                    do_sample=not args.greedy,
                    num_samples=args.n_samples - sidx,
                )
                assert outputs, "No outputs from model!"
                for impl in outputs:
                    if "```" in impl:
                        impl = impl.split("```")[0]
                        print("``` exist in generation. Please check the generation results.")

                    try:
                        with open(
                            os.path.join(workdir, p_name, f"{sidx}.py"),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            if model.direct_completion:
                                f.write(task["prompt"] + impl)
                            else:
                                f.write(impl)
                    except UnicodeEncodeError:
                        continue
                    sidx += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_type", required=True, type=str, choices=MODEL_MAPPING.keys())
    parser.add_argument("--model_path", type=str, default=None)
    parser.add_argument("--model_size", required=True, type=str)
    parser.add_argument("--bs", default=1, type=int)
    parser.add_argument("--temperature", default=0.0, type=float)
    parser.add_argument("--dataset", required=True, type=str, choices=["humaneval", "mbpp"])
    parser.add_argument("--root", type=str, required=True)
    parser.add_argument("--n_samples", default=1, type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output", type=str)
    parser.add_argument("--tensor-parallel-size", default=1, type=int)
    parser.add_argument(
        "--contract-type",
        default="none",
        type=str,
        choices=["none", "code", "docstring"],
    )
    parser.add_argument("--greedy", action="store_true")
    # id_range is list
    parser.add_argument("--id-range", default=None, nargs="+", type=int)
    args = parser.parse_args()
    print(args)
    assert args.model_size in MODEL_MAPPING[args.model_type]

    model_path = MODEL_MAPPING[args.model_type][args.model_size]
    if args.model_path is not None:
        model_path = args.model_path
    print(f"Loading model from {model_path}")

    print(f"Running model={args.model_type}, size={args.model_size}")
    print(f"\tLoad from `{model_path}`")

    if args.greedy and (args.temperature != 0 or args.bs != 1 or args.n_samples != 1):
        args.temperature = 0
        args.bs = 1
        args.n_samples = 1
        print("Greedy decoding ON (--greedy): setting bs=1, n_samples=1, temperature=0")

    if args.id_range is not None:
        assert len(args.id_range) == 2, "id_range must be a list of length 2"
        assert args.id_range[0] < args.id_range[1], "id_range must be increasing"
        args.id_range = tuple(args.id_range)

    # Make project dir
    os.makedirs(args.root, exist_ok=True)
    # Make dataset dir
    os.makedirs(os.path.join(args.root, args.dataset), exist_ok=True)
    # Make dir for codes generated by each model

    model = make_model(
        model_type=args.model_type,
        model_size=args.model_size,
        model_path=model_path,
        batch_size=args.bs,
        temperature=args.temperature,
        dataset=args.dataset,
        tensor_parallel_size=args.tensor_parallel_size
    )
    workdir = os.path.join(
        args.root,
        args.dataset,
        args.model_type
        + f"_{args.model_size}"
        + f"_temp_{args.temperature}"
        + ("" if args.contract_type == "none" else f"-contract-{args.contract_type}"),
    )
    os.makedirs(workdir, exist_ok=True)
    print(f"Working dir: {workdir}")

    with open(os.path.join(workdir, "args.txt"), "w") as f:
        f.write(str(args))

    print(f"Model cls: {model.__class__}")
    print(f"EOS tokens: {model.eos}")
    code_generate(args, workdir=workdir, model=model, id_range=args.id_range)


if __name__ == "__main__":
    main()
