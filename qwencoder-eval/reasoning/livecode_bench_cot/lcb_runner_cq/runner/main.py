import os
import json
from pathlib import Path

from lcb_runner_cq.runner.parser import get_args
from lcb_runner_cq.lm_styles import LanguageModelStore
from lcb_runner_cq.runner.vllm_runner import VLLMRunner
from lcb_runner_cq.evaluation import extract_instance_results
from lcb_runner_cq.runner.scenario_router import (
    build_prompt_benchmark,
    combine_results,
    sort_and_extract_save_results,
    get_metrics,
)


def main():
    args = get_args()

    model = LanguageModelStore[args.model]
    if args.model_path is not None and args.output_name is not None:
        model.model_name = args.model_path
        model.model_repr = args.output_name

    benchmark, format_prompt = build_prompt_benchmark(args.scenario, args.start_date, args.end_date)
    # output_path = get_output_path(model, args)

    output_folder = Path(f"{args.output_dir}/{model.model_repr}")
    output_folder.mkdir(exist_ok=True, parents=True)

    output_path = str(output_folder.joinpath(f"{args.scenario}_{args.n}_{args.temperature}_eval_all.json"))

    print(f"=> {output_path = }")

    if args.continue_existing:
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                old_save_results = json.load(f)
        else:
            print(f"File {output_path} does not exist in --continue_existing, starting from scratch")
            old_save_results = []

        old_save_results_question_ids = [instance["question_id"] for instance in old_save_results]
        remaining_benchmark = [instance for instance in benchmark if instance.question_id not in old_save_results_question_ids]
        print(f"Found {len(old_save_results)} existing generations, continuing with {len(remaining_benchmark)} remaining")
    else:
        old_save_results = []
        remaining_benchmark = benchmark

    if len(remaining_benchmark) > 0:
        runner = VLLMRunner(args, model)
        if args.no_batching:
            print(f"No Batching Inference")
            results: list[str] = runner.run_for_long(remaining_benchmark, format_prompt)
        else:
            print(f"Batching Inference")
            results: list[str] = runner.run_main(remaining_benchmark, format_prompt)
    else:
        results = []

    combined_results = combine_results(args.scenario, results, model)

    save_results = [instance.insert_output(outputs_list, extracted_list) for instance, (outputs_list, extracted_list) in zip(benchmark, combined_results)]

    if args.continue_existing:
        save_results += old_save_results

    save_results, combined_results = sort_and_extract_save_results(args.scenario, save_results)

    with open(output_path, "w") as f:
        json.dump(save_results, f, indent=4)

    if args.evaluate:
        # TODO: we can add --continue_existing_evaluation flag to continue from existing evaluation
        metrics = get_metrics(args.scenario, args, benchmark, combined_results)
        graded = extract_instance_results(metrics[1])

        save_eval_results = [
            instance.insert_output_evaluation(outputs_list, extracted_list, graded_list) for instance, (outputs_list, extracted_list), graded_list in zip(benchmark, combined_results, graded)
        ]

        with open(output_path.replace(".json", "_eval.json"), "w") as f:
            json.dump(metrics, f, indent=4)

        with open(output_path.replace(".json", "_eval_all.json"), "w") as f:
            json.dump(save_eval_results, f, indent=4)

        with output_folder.joinpath("generation.json").open("w") as f:
            json.dump(save_results, f, indent=4)
        with output_folder.joinpath("results.json").open("w") as f:
            json.dump(metrics, f, indent=4)
        with output_folder.joinpath("log.json").open("w") as f:
            json.dump(save_eval_results, f, indent=4)


if __name__ == "__main__":
    main()
