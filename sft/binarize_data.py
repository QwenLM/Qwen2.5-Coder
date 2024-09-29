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


def chatml_format_preprocess(sources, tokenizer: transformers.PreTrainedTokenizer, max_len: int, system_message: str = "You are a helpful assistant.", only_last_turn_loss=False) -> Dict:
    IGNORE_INDEX = -1
    roles = {"user": "<|im_start|>user", "assistant": "<|im_start|>assistant"}
    tokenizer.add_special_tokens({"additional_special_tokens": ["<|im_end|>", "<|im_start|>"]})
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
    assert len(input_id) == len(target)
    for j, sentence in enumerate(sources[1:]):
        role = roles[sentence["role"]]
        _input_id = tokenizer(role).input_ids + nl_tokens + tokenizer(sentence["content"], add_special_tokens=False).input_ids + [im_end] + nl_tokens
        input_id += _input_id

        if role == '<|im_start|>user' or (only_last_turn_loss and j < len(sources[1:])):
            _target = [im_start] + [IGNORE_INDEX] * (len(_input_id) - 3) + [im_end] + nl_tokens
        elif role == '<|im_start|>assistant':
            _target = [im_start] + [IGNORE_INDEX] * len(tokenizer(role).input_ids) + _input_id[len(tokenizer(role).input_ids) + 1:-2] + [im_end] + nl_tokens
        else:
            raise NotImplementedError
        target += _target

        if j == len(sources[1:]) - 1:
            test_input_ids += tokenizer(role).input_ids + nl_tokens
        else:
            test_input_ids += _input_id

    assert len(input_id) == len(target)
    return dict(
        test_input_ids=test_input_ids,
        input_ids=input_id,
        label=target,
    )


def read_file_from_position_with_chatml_format_processor(args):
    filename, start_position, end_position, worker_id, args = args
    tokenizer=args["tokenizer"]
    max_len=args["max_len"]
    objs = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        current_position = utils.find_next_line(f, start_position)
        f.seek(current_position)
        if current_position >= end_position:
            print(f"worker_id {worker_id} completed")
            return objs
        for cnt in tqdm.tqdm(itertools.count(), position=worker_id, desc=f"worker_id: {worker_id}"):
            line = f.readline()
            if not line:
                break
            obj = json.loads(line)
            obj = chatml_format_preprocess(obj["messages"], tokenizer, max_len=max_len, only_last_turn_loss=obj["only_last_turn_loss"] if "only_last_turn_loss" in obj else True)
            objs.append(obj)
            if f.tell() >= end_position:
                break
    print(f"worker_id {worker_id} completed")
    return objs


def tokenize_file(workers=64, chunk_size=10000, input_path="./raw/sft.jsonl", output_path="./processed/sft.jsonl", tokenizer=None, max_len=32768):
    output_objs = utils.multi_tasks_from_file(input_path, workers=workers, task=read_file_from_position_with_chatml_format_processor, chunk_size=chunk_size, args={"tokenizer": tokenizer, "max_len": max_len})
    utils.write_jsonl_file(output_objs, output_path)
    np.save(f"{output_path}.npy", output_objs, allow_pickle=True)
    print(f"Successfully saving to {output_path}.npy")


def parse_args():
    parser = argparse.ArgumentParser(description='Argument Parser Example')
    parser.add_argument('--input_path', '-input_path', type=str, default="sft.jsonl", help='Path to output file')
    parser.add_argument('--output_path', '-output_path', type=str, default="sft.jsonl", help='Path to output file')
    parser.add_argument('--workers', '-workers', type=int, default=1, help='Path to output file')
    parser.add_argument('--chunk_size', '-chunk_size', type=int, default=0.01 * 2**30, help='Path to output file')
    parser.add_argument('--max_len', '-max_len', type=int, default=32768, help='Path to output file')
    parser.add_argument('--tokenizer_path', '-tokenizer_path', type=str, default="Qwen/Qwen2___5-Coder-1___5B/", help='Path to output file')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    tokenizer = transformers.AutoTokenizer.from_pretrained(args.tokenizer_path,
                                                           add_eos_token=False,
                                                           add_bos_token=False,
                                                           pad_token='<|extra_0|>',
                                                           eos_token='<|endoftext|>',
                                                           cache_dir=None,
                                                           model_max_length=8192 * 4,
                                                           truncation=True,
                                                           padding_side="left",
                                                           trust_remote_code=True)
    tokenizer.add_special_tokens({"additional_special_tokens": ["<fim_prefix>", "<fim_middle>", "<fim_suffix>", "<fim_pad>"]})
    tokenize_file(workers=args.workers, chunk_size=args.chunk_size, input_path=args.input_path, output_path=args.output_path, tokenizer=tokenizer, max_len=args.max_len)
