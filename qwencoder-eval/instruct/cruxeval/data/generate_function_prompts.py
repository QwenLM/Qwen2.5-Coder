# Copyright (c) Meta Platforms, Inc. and affiliates.

import json
from diverse_fewshot_examples import *

def make_prompt(function, examples):
    prompt = "You will be given a function name between [TASK] and [/TASK] tags. Following the examples given, write a Python function that makes use of the given function and 5 test inputs for that function.\n\n"
    prompt += '\n\n'.join(examples)
    prompt += f"\n\n[TASK]\n{function}\n[/TASK]\n[PYTHON]"
    return prompt

def generate():
    str_methods = [f"str.{fn}" for fn in dir(str) if not fn.startswith("_")]
    list_methods = [f"list.{fn}" for fn in dir(list) if not fn.startswith("_")]
    dict_methods = [f"dict.{fn}" for fn in dir(dict) if not fn.startswith("_")]
    all_methods = str_methods + list_methods + dict_methods
    print(f"{len(all_methods)} methods")

    prompts_json = []
    string_examples = [string_1, string_2, string_3, string_4, string_5]
    list_examples = [list_1, list_2, list_3, list_4, list_5]
    for i in str_methods:
        for s in string_examples:
            for l in list_examples[:-1]:
                prompts_json.append(json.dumps({"text": make_prompt(i, [s, l]), "method": i}))

    for i in list_methods + dict_methods:
        for s in string_examples:
            for l in list_examples:
                for _ in range(2):
                    prompts_json.append(json.dumps({"text": make_prompt(i, [s, l]), "method": i}))
                
    write_file = "data_generating_prompt.jsonl"
    with open(write_file, "w") as f:
        f.write('\n'.join(prompts_json))

if __name__ == "__main__":
    generate()