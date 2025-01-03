import jsonlines
import os
import numpy as np
import transformers
import tqdm
import sys
from typing import Dict
import argparse
import itertools
import json
from utils import utils
IGNORE_INDEX = -100 #default ignore_index = 100 in transformers
# Set special tokens globally to avoid adding them multiple times.
def setup_tokenizer(tokenizer):
    tokenizer.add_special_tokens({
        "additional_special_tokens": [
            "<|fim_prefix|>", "<|fim_middle|>", "<|fim_suffix|>", "<|repo_name|>",
            "<|file_sep|>", "<|im_start|>", "<|im_end|>"
        ]
    })
    return tokenizer


def chatml_format_preprocess(sources, 
        tokenizer: transformers.PreTrainedTokenizer, max_len: int, 
        system_message: str = "You are a helpful assistant.", 
        only_last_turn_loss=False,
        return_test_input_ids = False
    ) -> Dict:
    """
<|im_start|>[system][\n]
[system_prompt]
<|im_end|>
<|im_start|>[user][\n]
[user_prompt]
<|im_end|>
<|im_start|>[assistant][\n]
response
<|im_end|>
    The tokens such as [...] are masked.
    """
    roles = {"user": "<|im_start|>user", "assistant": "<|im_start|>assistant", "system": "<|im_start|>system"}
    
    im_start = tokenizer("<|im_start|>").input_ids[0]
    im_end = tokenizer("<|im_end|>").input_ids[0]
    nl_tokens = tokenizer('\n').input_ids
    if len(nl_tokens) > 0:
        nl_tokens = nl_tokens[-1:]
    
    _system = tokenizer('system').input_ids + nl_tokens
    _user = tokenizer('user').input_ids + nl_tokens
    _assistant = tokenizer('assistant').input_ids + nl_tokens

    input_id, target, test_input_ids = [], [], []
    if sources[0]["content"] != "" and sources[0]["role"] == "system":
        system_message = sources[0]["content"]
    
    system = [im_start] + _system + tokenizer(system_message).input_ids + [im_end] + nl_tokens
    input_id += system
    test_input_ids += system
    target += [im_start] + [IGNORE_INDEX] * (len(system) - 3) + [im_end] + nl_tokens
    assert len(input_id) == len(target), "Input and target lengths do not match."

    for j, sentence in enumerate(sources[1:]):
        role = roles.get(sentence["role"])
        if not role:
            raise ValueError(f"Unknown role '{sentence['role']}' encountered.")
        
        _input_id = tokenizer(role).input_ids + nl_tokens + tokenizer(sentence["content"], add_special_tokens=False).input_ids + [im_end] + nl_tokens
        input_id += _input_id

        if role == '<|im_start|>user' or (only_last_turn_loss and j < len(sources[1:]) - 1):
            _target = [im_start] + [IGNORE_INDEX] * (len(_input_id) - 3) + [im_end] + nl_tokens
        elif role == '<|im_start|>assistant':
            _target = [im_start] + [IGNORE_INDEX] * len(tokenizer(role).input_ids) + _input_id[len(tokenizer(role).input_ids) + 1: -2] + [im_end] + nl_tokens
        elif role == "<|im_start|>system": # if has more system prompt in the conversion
            _target = [im_start] + [IGNORE_INDEX] * (len(_input_id) - 3) + [im_end] + nl_tokens
        else:
            raise NotImplementedError(f"Role '{role}' is not implemented.")
        
        target += _target

        if j == len(sources[1:]) - 1:
            test_input_ids += tokenizer(role).input_ids + nl_tokens
        else:
            test_input_ids += _input_id

    assert len(input_id) == len(target), "Final input and target lengths do not match."
    if len(input_id) > max_len:
        return None
    if return_test_input_ids:
        return dict(
            test_input_ids=test_input_ids, 
            input_ids=input_id,
            label=target,
        )
    else:
        return dict(
            input_ids=input_id,
            label=target,
            length=[len(input_id)]
        )


def read_file_from_position_with_chatml_format_processor(args):
    filename, start_position, end_position, worker_id, args = args
    tokenizer = args["tokenizer"]
    max_len = args["max_len"]
    objs = []
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:  # Using 'replace' to handle errors better
        current_position = utils.find_next_line(f, start_position)
        f.seek(current_position)
        if current_position >= end_position:
            print(f"worker_id {worker_id} completed")
            return objs
        for cnt in tqdm.tqdm(itertools.count(), position=worker_id, desc=f"worker_id: {worker_id}"):
            line = f.readline()
            if not line:
                break
            try:
                obj = json.loads(line)
            except:
                print("Invalid json!")
                continue
            obj = chatml_format_preprocess(
                obj["messages"], tokenizer, max_len=max_len, 
                only_last_turn_loss=obj.get("only_last_turn_loss", True)
            )
            if obj is not None:
                objs.append(obj)
            if f.tell() >= end_position:
                break
    print(f"worker_id {worker_id} completed")
    return objs

def convert_to_uint32(x):
    return np.array(x, dtype = np.uint32)

def convert_to_int32(x):
    return np.array(x, dtype = np.int32)

def save_mmap(objs, key, output_path, padding_value):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data = []
    max_length = 0
    for obj in tqdm.tqdm(objs):
        vec = obj[key]
        data.append(vec)
        max_length = max(max_length, len(vec))
    n_samples = len(data)
    utils.save_json(data = {
        "n_samples": n_samples,
        "max_len": max_length,
    }, output_path=f"{output_path}.shape.json")
    # Create mmap
    data_shape = (n_samples, max_length)
    data_mmap = np.memmap(
        output_path, 
        dtype=np.int32,
        mode='w+',
        shape=data_shape
    )
    for i, vec in enumerate(data):
        padded_vec = vec + [padding_value] * (max_length - len(vec))
        data_mmap[i] = padded_vec
    data_mmap.flush()


def tokenize_file(workers=64, chunk_size=10000, input_path="./raw/sft.jsonl", output_path="./processed/sft.jsonl", tokenizer=None, max_len=32768, save_format = ".npy"):
    output_objs = utils.multi_tasks_from_file(input_path, workers=workers, task=read_file_from_position_with_chatml_format_processor, chunk_size=chunk_size, args={"tokenizer": tokenizer, "max_len": max_len})
    if save_format == ".jsonl":
        utils.write_jsonl_file(output_objs, output_path)
        print(f"Successfully saved to {output_path}")
    elif save_format == ".npy":
        for obj in output_objs:
            obj["input_ids"] = convert_to_uint32(obj["input_ids"])
            obj["label"] = convert_to_int32(obj["label"])
            if "test_input_ids" in obj:
                obj["test_input_ids"] = convert_to_uint32(obj["test_input_ids"])
        np.save(f"{output_path}.npy", output_objs, allow_pickle=True)
        print(f"Successfully saved to {output_path}.npy")
    elif save_format == ".mmap":
        save_mmap(output_objs, key = "input_ids", output_path = f"{output_path}.input_ids.mmap", padding_value = tokenizer.pad_token_id)
        save_mmap(output_objs, key = "label", output_path = f"{output_path}.labels.mmap", padding_value = IGNORE_INDEX)
        save_mmap(output_objs, key = "length", output_path = f"{output_path}.lengths.mmap", padding_value = IGNORE_INDEX)
        print(f"Successfully saved to {output_path}.input_ids.mmap and {output_path}.label.mmap and {output_path}.lengths.mmap")


def parse_args():
    parser = argparse.ArgumentParser(description='Argument Parser Example')
    parser.add_argument('--input_path', '-input_path', type=str, default="./raw/sft.jsonl.sampled", help='Path to input file')
    parser.add_argument('--output_path', '-output_path', type=str, default="./raw/sft.jsonl.sampled.processed", help='Path to output file')
    parser.add_argument('--workers', '-workers', type=int, default=1, help='Number of workers')
    parser.add_argument('--chunk_size', '-chunk_size', type=float, default=0.1 * 2 ** 30, help='Chunk size for file processing')
    parser.add_argument('--max_len', '-max_len', type=int, default=8192, help='Maximum length for tokenization')
    parser.add_argument('--tokenizer_path', '-tokenizer_path', type=str, default="./pretrained_models/qwen/Qwen2.5-Coder-7B/", help='Path to tokenizer')
    parser.add_argument('--save_format', '-save_format', type=str, default=".npy", help='Path to tokenizer')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(args)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.tokenizer_path,
        add_eos_token=False,
        add_bos_token=False,
        pad_token='<|endoftext|>',
        eos_token='<|im_end|>', 
        cache_dir=None,
        model_max_length=8192 * 5,
        truncation=True,
        padding_side="right",
        trust_remote_code=True
    )
    tokenizer = setup_tokenizer(tokenizer)  # Set special tokens once
    tokenize_file(workers=args.workers, chunk_size=args.chunk_size, input_path=args.input_path, output_path=args.output_path, tokenizer=tokenizer, max_len=args.max_len, save_format = args.save_format)
