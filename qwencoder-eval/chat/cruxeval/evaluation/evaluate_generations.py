# Copyright (c) Meta Platforms, Inc. and affiliates.

import json
import argparse

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from utils_general import (
    evaluate_score,
    pass_at_k,
)


def evaluate_generations(generations, mode):
    # Load the samples
    file_path = str(Path(__file__).resolve().parent.parent / "data/cruxeval.jsonl")

    dataset = [json.loads(l) for l in open(file_path, "r").readlines()]
    references = [(doc["code"], doc["input"], doc["output"]) for doc in dataset]

    # Run the samples
    try:
        generations_list = [generations[f"sample_{i}"] for i in range(len(dataset))]
    except:
        assert False, "check format of generations, should be dictionary of lists with keys of id's in the form sample_i"

    with ProcessPoolExecutor() as executor:
        args_list = zip(generations_list, references, [mode] * len(generations_list))
        results = executor.map(evaluate_score, args_list)
    all_scores = list(results)

    # Compute pass@k scores
    pass_at_1s, pass_at_5s = [], []
    for execution_result in all_scores:
        c, n = execution_result.count(True), len(execution_result)
        pass_at_1s.append(pass_at_k(n, c, 1))
        pass_at_5s.append(pass_at_k(n, c, 5))

    return {
        "raw_generations": generations,
        "raw_scored_generations": {
            f"sample_{i}": all_scores[i] for i in range(len(dataset))
        },
        "pass_at_1": sum(pass_at_1s) / len(pass_at_1s) * 100,
        "pass_at_5": sum(pass_at_5s) / len(pass_at_5s) * 100,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generations_path",
        help="JSON path containing outputs to evaluate. Should contain a list of \
              length 800, where each element is a list of different generations \
              for that benchmark sample.",
        type=str,
    )
    parser.add_argument(
        "--scored_results_path",
        help="path to dump scored results",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--mode",
        help="either input or output, depending on which one to evaluate",
        type=str,
        default=None,
    )

    args = parser.parse_args()
    generations = json.load(open(args.generations_path, "r"))
    print(f"Scoring {args.generations_path}... expect around a minute")

    results = evaluate_generations(generations, args.mode)
    print(f"Finished!")
    print("pass@1:", round(results["pass_at_1"], 1), "pass@5:", round(results["pass_at_5"], 1))
    if args.scored_results_path != None:
        print(f"Dumping to {args.scored_results_path}")
        with open(args.scored_results_path, "w") as f:
            json.dump(results, f, indent=4)

    simple_results_path = Path(args.scored_results_path).parent / "results.json"
    simple_results = {"pass@1": round(results["pass_at_1"], 1)}
    with open(simple_results_path, "w") as f:
        json.dump(simple_results, f, indent=4)
