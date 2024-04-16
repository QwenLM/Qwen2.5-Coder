from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import jsonlines
import re
import torch
import argparse
from vllm import LLM, SamplingParams
from dataset import JsonlDataset, my_collate_fn
import time
from tqdm import tqdm
import importlib
import sys
import os

sys.path.append('./prompt_function/')
print(sys.path)

def evaluate(batch_prompts, llm, samplingparams):
    generation_config = samplingparams.__dict__
    batch_output = llm.generate(batch_prompts, samplingparams)

    return generation_config, batch_output

def main():
    parser = argparse.ArgumentParser(description="Run inference with the specified model and dataset.")
    parser.add_argument("--base_model", default="Model_Path", type=str, help="Path to the model.")
    parser.add_argument("--dataset", default="debug", type=str, help="Name of dataset.")
    parser.add_argument("--input_data_dir", default="Input.jsonl", type=str, help="Path to input data.")
    parser.add_argument("--output_data_dir", default="Output.jsonl", type=str, help="Path to output data.")
    parser.add_argument("--batch_size", default=16, type=int, help="Batch size for processing.")
    parser.add_argument("--num_of_sequences", default=20, type=int, help="Number of sequences to generate.")
    parser.add_argument("--num_gpus", default=4, type=int, help="Number of GPUs to use.")
    parser.add_argument("--prompt_type", default="zero", type=str, help="Type of Prompts, zero or three.")
    parser.add_argument("--swap_space", default=4, type=int, help="Swap space for the model.")
    parser.add_argument("--start_idx", default=0, type=int, help="Start index for data processing.")
    parser.add_argument("--end_idx", default=-1, type=int, help="End index for data processing.")

    args = parser.parse_args()
    print(args)

    assert args.base_model, "Please specify a --base_model, e.g., --base_model='bigcode/octocoder'"

    max_model_len = 16384
    frequency_penalty = 0.0
    presence_penalty = 0.0
    module = importlib.import_module(f'prompt_function.prompt_{args.dataset}')
    # Choose prompt function
    if 'Wizard' in args.base_model:
        model_choice = 'wizardcoder'
        group = 'group1'
        if '15B' in args.base_model:
            max_model_len = 8192
    elif 'Magic' in args.base_model:
        model_choice = 'magicoder'
        group = 'group1'
        max_model_len = 32768
        if 'CL' in args.base_model:
            max_model_len = 16384
    elif 'octo' in args.base_model:
        model_choice = 'octocoder'
        group = 'group1'
        max_model_len = 8192
    elif 'codefuse' in args.base_model:
        model_choice = 'codefuse'
        group = 'group1'
        max_model_len = 16384    
    elif 'deepseek' in args.base_model:
        model_choice = 'deepseek'
        group = 'group1'
    elif 'Phind' in args.base_model:
        model_choice = 'phind'
        group = 'group1'
    elif 'Instruct-hf' in args.base_model:
        model_choice = 'codellama-inst'
        group = 'cot' if args.prompt_type == 'cot' else 'group1'
    elif 'CodeLlama-34b-hf' in args.base_model:
        model_choice = 'codellama'
        group = 'group1'
    elif 'bloom' in args.base_model:
        model_choice = 'bloom'
        group = 'group1'
    elif 'OpenCode' in args.base_model:
        model_choice = 'deepseek'
        group = 'group1'
    elif 'CodeQwen' in args.base_model:
        model_choice = 'codeqwen'
        group = 'group1'
    else:
        raise ValueError(f"Invalid model name: {args.base_model}")
    get_prompt_function_name = f"generate_prompt_{group}"
    prompt_function = getattr(module, get_prompt_function_name) # Get the prompt function

    # Set hyperparameters
    if args.num_of_sequences == 1:        
        samplingparams=SamplingParams(n=args.num_of_sequences, temperature=0.0, max_tokens=2048, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty)
    else:
        samplingparams=SamplingParams(n=args.num_of_sequences, temperature=0.8, top_p=0.9, top_k=40, max_tokens=2048, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty) 
    
    # Input file name
    input_data_path = args.input_data_dir + f"code_{args.dataset}_primary.jsonl"
    model_name = args.base_model.split('/')[-1].replace('-', '_').replace('.', '_')\
    
    # Output file name
    # Make sure the directory exists
    end = args.end_idx if args.end_idx != -1 else "end"
    if args.prompt_type == "zero":
        output_data_path = args.output_data_dir + f"code_{args.dataset}/{model_name}_{args.start_idx}_{end}.jsonl"
    elif args.prompt_type == "three":
        output_data_path = args.output_data_dir + f"code_{args.dataset}/Few_Shot_{model_name}_{args.start_idx}_{end}.jsonl"
    elif args.prompt_type == "cot":
        output_data_path = args.output_data_dir + f"code_{args.dataset}/Cot_{model_name}_{args.start_idx}_{end}.jsonl"
    else:
        raise ValueError("Invalid prompt type.")

    print(f"Input file: {input_data_path}")
    print(f"Output file: {output_data_path}")

    meta_data_flag = False
    if os.path.exists(output_data_path):
        output_data = jsonlines.open(output_data_path, mode='a', flush=True)
        with open(output_data_path, 'r') as f:
            line_count = sum(1 for _ in f)
            print(f"Output file exists. Appending to {output_data_path}. Line count: {line_count}")
        if line_count >= 1:
            meta_data_flag = True
        # Update start index
        args.start_idx = max(0, line_count - 1)
    else:
        output_data = jsonlines.open(output_data_path, mode='w', flush=True)
    
    # Load data
    if args.end_idx == -1:
        args.end_idx = None
    dataset = JsonlDataset(input_data_path)[args.start_idx:args.end_idx]
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=my_collate_fn)

    # Load model
    if len(dataloader) > 0:
        print("Loading model...")
        llm = LLM(model=args.base_model, trust_remote_code=True, tensor_parallel_size=args.num_gpus, max_model_len=max_model_len, swap_space=args.swap_space)
        print("Model loaded.")

    start_time = time.time()

    # Inference
    for batch in tqdm(dataloader, desc="Inference"):
        if args.prompt_type == "zero":
            batch_prompts = prompt_function(batch, model_choice, "zero") # Generate prompt
        elif args.prompt_type == "three":
            batch_prompts = prompt_function(batch, model_choice, "three")
        elif args.prompt_type == "cot":
            batch_prompts = prompt_function(batch, model_choice, "cot")
        generation_config, batch_output = evaluate(batch_prompts, llm, samplingparams) # Get output
        if not meta_data_flag:
            meta_data_flag = True
            meta_data = {
                "model": args.base_model,
                # "model_size": model.num_parameters(),
                "model_url": f"https://huggingface.co/{args.base_model}",
                "greedy_search_decoding": generation_config["best_of"] == 1,
                # "do_sample": generation_config["do_sample"],
                "num_output": generation_config["n"],
                "temperature": generation_config["temperature"],
                "top_p": generation_config["top_p"],
                "top_k": generation_config["top_k"],
            }
            output_data.write(meta_data)
        for idx, output in enumerate(batch_output):
            output = [data.text for data in output.outputs]
            if args.dataset == 'debug':
                new_data = {
                    "problem_id": batch["idx"][idx].item(),
                    "completion_id": 0,
                    "language": batch["code_language"][idx],
                    "error_type": batch["type"][idx],
                    "difficulty": batch["difficulty"][idx],
                    "prompt": batch_prompts[idx],
                    "code": output,
                }
            elif args.dataset == "translate":
                new_data = {
                    "problem_id": batch["idx"][idx].item(),
                    "completion_id": 0,
                    "source_lang": batch["source_lang"][idx],
                    "target_lang": batch["target_lang"][idx],
                    "difficulty": batch["difficulty"][idx],
                    "prompt": batch_prompts[idx],
                    "code": output,
                }
            elif args.dataset == "polishment":
                new_data = {
                    "problem_id": batch["idx"][idx].item(),
                    "completion_id": 0,
                    "language": batch["source_lang"][idx],
                    "difficulty": batch["difficulty"][idx],
                    "prompt": batch_prompts[idx],
                    "code": output,
                }
            elif args.dataset == "switch":
                new_data = {
                    "problem_id": batch["idx"][idx].item(),
                    "completion_id": 0,
                    "language": batch["language"][idx],
                    "pair": batch["pair_id"][idx],
                    "prompt": batch_prompts[idx],
                    "code": output,
                }
            else:
                raise ValueError("Invalid dataset type.")
            output_data.write(new_data)

    end_time = time.time()
    print("Time used: ", end_time-start_time)
    if len(dataloader) == 0:
        print("No data in the dataset.")
    else:
        print("Each batch time: ", (end_time-start_time)/len(dataloader))

if __name__ == '__main__':
    main()