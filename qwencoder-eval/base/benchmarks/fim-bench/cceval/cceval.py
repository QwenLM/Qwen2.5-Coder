#!/usr/bin/env python
# coding=utf-8

import argparse
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vllm import LLM, SamplingParams
from typing import Optional
from utils import prepare_prompt
from eval_metric import compute_metric_stmt_multilang, extract_block
#from eval_metric_cceval import compute_metric_stmt_cceval
from tqdm import tqdm
import time
import torch
from typing import List, Dict
from transformers import AutoTokenizer




def build_dataset(args) -> Dict[str, List[Dict]]:
    """
    Build datasets for each task and return them in a dictionary
    """
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    datasets = {}
    
    for language in args.languages:
        # Construct task-specific prompt file path
        task_prompt_file = args.prompt_file.replace('LANGUAGE', language)
        if not os.path.exists(task_prompt_file):
            raise FileNotFoundError(f"Prompt file for language {language} not found at {task_prompt_file}")
            
        with open(task_prompt_file) as f:
            raw_data = [json.loads(line) for line in f.readlines()]

        task_data = []
        for entry in raw_data:
            model_type = args.model_type
            model_name = args.model_name_or_path
            left_cxt = entry["prompt"]
            if 'full_right_context' in entry:
                right_cxt = entry["full_right_context"]
            else:
                right_cxt = entry["right_context"]
            crossfile_cxt = None
            if 'crossfile_context' in entry:
                crossfile_cxt = entry["crossfile_context"] if isinstance(entry["crossfile_context"], str) else entry["crossfile_context"]['text']
                
            prompt = prepare_prompt(tokenizer, args.task, model_type, model_name, left_cxt, right_cxt, crossfile_cxt, args)
            entry['llm_prompt'] = prompt
            entry['task_type'] = args.task  # Add task type to entry for later identification
            task_data.append(entry)
        
        datasets[language] = task_data
    
    return datasets


def model_inference(args):
    llm = LLM(model=args.model_name_or_path, tensor_parallel_size=args.tp, trust_remote_code=True,distributed_executor_backend="ray",
        enforce_eager=True)
    sampling_params = SamplingParams(temperature=0, top_p=1, max_tokens=args.gen_length)

    # Get datasets for all tasks
    task_datasets = build_dataset(args)
    
    # Create output directory for each task
    for language in args.languages:
        task_output_dir = os.path.join(args.output_dir, args.dataset, language, args.task)
        os.makedirs(task_output_dir, exist_ok=True)

    # Process each task separately
    for language in args.languages:
        print(f"\nProcessing language: {language}")
        data = task_datasets[language]
        all_preds = []
        
        prompts = [entry["llm_prompt"] for entry in data]
        #prompts = prompts[:10]
        cur_preds = llm.generate(prompts, sampling_params, use_tqdm=True)

        for cur_pred, entry in zip(cur_preds, data):
            all_preds.append({
                "task_id": entry["metadata"]["task_id"],
                "pred": cur_pred.outputs[0].text.split("<|fim_pad|>")[0].split("<|file_sep|>")[0],
                "task_type": args.task,
                "inputs": entry["llm_prompt"]
            })
            
        # Save predictions for current task
        task_output_file = os.path.join(args.output_dir, args.dataset, language, args.task, "prediction.jsonl")
        with open(task_output_file, "w", encoding="utf-8") as f_pred:
            for entry in all_preds:
                f_pred.write(json.dumps(entry) + "\n")


def cceval(custom_args: Optional[argparse.Namespace] = None) -> None:
    """
    Args:
        custom_args: Optional pre-configured arguments
    """
    if custom_args is None:
        parser = argparse.ArgumentParser()
    
        parser.add_argument("--languages", nargs="+", 
        choices=["python", "java", "csharp", "typescript"], default=["python"], help="language name")
        parser.add_argument("--model_name_or_path", type=str, required=True)
        parser.add_argument(
            "--model_type",
            type=str,
            default="codelm",
            choices=["codelm", "codelm_cfc", "codelm_leftright_context", 'codelm_right_cfc_left'],
            help="Model type to be loaded"
        )
        parser.add_argument("--prompt_file", type=str, default=None, 
                        help="file with a list of prompts (use 'TASK' as placeholder for task name)")
        parser.add_argument("--gen_length", type=int, default=50, help="max length of generated token sequence")
        parser.add_argument("--max_seq_length", type=int, default=2048, help="max length of prompt")
        parser.add_argument(
            "--cfc_seq_length",
            type=int,
            default=512,
            help="For model_type=codelm_cfc: Text sequence length corresponding to the retrieved nodes"
        )
        parser.add_argument(
            "--right_context_length",
            type=int,
            default=512,
            help="For model_type=codelm_leftright_context: Text sequence length corresponding to the right context"
        )
        parser.add_argument("--output_dir", type=str, default="output_dir", help="output directory to save predictions")
        parser.add_argument("--num_return_sequences", type=int, default=1, help="The number of samples to generate.")
        parser.add_argument("--dataset", type=str, default="cclong", help="dataset name")
        parser.add_argument("--tp", type=int, default=8, help="tensor_parallel_size")
        # compute metric args
        parser.add_argument(
            "--ts_lib",
            type=str,
            default="build/python-lang-parser.so",
            help="tree-sitter lib for tokenize code"
        )
        # only compute metric
        parser.add_argument("--only_compute_metric", action="store_true", help="only compute metric")
        # for cceval metric
        parser.add_argument("--compute_cceval_metric", action='store_true', help="use cceval metric")
        parser.add_argument("--task", type=str, required=True, choices=["line_completion", "function_completion", "api_completion"])
        args = parser.parse_args()
    else:
        args = custom_args

    predictions = model_inference(args)

    
    compute_metric_stmt_multilang(args)

    return predictions
    


if __name__ == "__main__":
    cceval()