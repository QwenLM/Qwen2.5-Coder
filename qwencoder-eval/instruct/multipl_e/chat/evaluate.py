import os
import sys
import argparse
import re
import tqdm
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional, Dict, Sequence, List
import json
import jsonlines
import torch
import transformers
from multiple_metrics.evaluation import evaluate_problem
from multiple_metrics.single_experiment_pass_k import for_file
from multiple_metrics.containerized_eval import eval_string_script
import tempfile
from multiprocessing import cpu_count
import numpy as np
from pathlib import Path
import vllm

IMPORT_HELPER = {
    "python": [
        "import math",
        "import re",
        "import sys",
        "import copy",
        "import datetime",
        "import itertools",
        "import collections",
        "import heapq",
        "import statistics",
        "import functools",
        "import hashlib",
        "import numpy",
        "import numpy as np",
        "import string",
        "from typing import *",
        "from collections import *",
    ],
    "go": [
        "math",
        "strings",
        "fmt",
        "strconv",
        "time",
        "bytes",
        "regexp",
        "sort",
        "math/rand",
        "crypto/md5",
    ],
    "cpp": [
       # "using namespace std;",
        "#include<optional>",
        "#include<cassert>",
        "#include<stdlib.h>",
        "#include<algorithm>",
        "#include<cmath>",
        "#include<math.h>",
        "#include<numeric>",
        "#include<stdio.h>",
        "#include<vector>",
        "#include<set>",
        "#include<map>",
        "#include<queue>",
        "#include<stack>",
        "#include<list>",
        "#include<deque>",
        "#include<boost/any.hpp>",
        "#include<string>",
        "#include<climits>",
        "#include<cstring>",
        "#include<iostream>",
        "#include<sstream>",
        "#include<fstream>",
    ],
    "java": [
        "import java.util.*;",
        "import java.lang.reflect.*;",
        "import org.javatuples.*;",
        "import java.security.*;",
        "import java.math.*;",
        "import java.io.*;",
        "import java.util.stream.*;",
    ],
    "cs": [
        "using System;",
        "using System.Numerics;",
        "using System.Diagnostics;",
        "using System.Collections.Generic;",
        "using System.Linq;",
        "using System.Text;",
        "using System.Security.Cryptography;",
        "using System.Collections.Generic;",
    ],
}

def remove_nth_from_last_brace(code, n=1, ch="}"):
    brace_count = 0
    code_lines = code.split("\n")
    index = 0
    for i in range(len(code_lines) - 1, -1, -1):
        if code_lines[i].strip() == ch:
            brace_count += 1
            index = i
            if brace_count == n:
                return "\n".join(code_lines[:i])
                # return code[:i] + code[i+1: ]
    return "\n".join(code_lines[:index])


def extract_func(text, job, language):
    if language == "py" or language == "python":  # python
        def extract_python_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text

        code = extract_python_code(text)
        if "```" in code:
           code = code.replace("```", "")
        func_name = None
        if "name" in job:
            func_name = "_".join(job["name"].split("_")[2:])
        elif "test" in job:
            func_name = re.search(r"assert (.*?)\(.*?\)", job["test"]).group(1)   
        if func_name is not None and func_name not in code:
            code = job["prompt"] + code
        code = "\n".join(IMPORT_HELPER["python"]) + "\n" + code

    elif language == "java":
        def extract_java_code(text) -> str:
            code_block = re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL)
            if code_block is None:
                return text
            else:
                return code_block.group(1)

        code = extract_java_code(text)
        func_name = re.search(r"assert\((.*?)\(.*?\)\);\n", job["tests"], flags=re.DOTALL).group(1)
        if re.search(rf"public static .*? {func_name}\(.*?\)", code, flags=re.DOTALL) is None:
            code = job["prompt"] + "\n" + code
        elif "class Problem" not in code:
            code = "class Problem {\n" + code
        code = code.replace("public class Problem", "class Problem")
        #func_lines = [line for line in code.split("\n") if line.strip()]
        def remove_main(code):
            code_lines = code.split("\n")
            stack = []
            start = -1
            end = -1
            for i in range(0, len(code_lines)):
                if "public static void main" in code_lines[i]:
                    start = i
                if start >= 0:
                    for c in code_lines[i]:
                        if c == "{":
                            stack.append("{")
                        elif c == "}":
                            stack.pop()
                            if len(stack) == 0 and start >= 0:
                                end = i
                                return "\n".join(code_lines[:start] + code_lines[end + 1 :])
            return code
        if "public static void main" in code:
            code = remove_main(code)
        if code.count("{") - code.count("}") == 0:
            code = remove_nth_from_last_brace(code, n = 2, ch="}")
        elif code.count("{") - code.count("}") == 1:
            code = remove_nth_from_last_brace(code, n = 1, ch="}")
        
        code = "\n".join(IMPORT_HELPER["java"]) + "\n" + code
    elif language == "cpp":
        def extract_func_cpp(code, key_line=""):
            stack = []
            found = False
            func_code = ""
            lines = code.splitlines()
            for line in lines:
                if line.startswith("#include"): #remove using namespace
                    func_code += line + "\n"
                if key_line in line:
                    found = True
                if found:
                    for char in line:
                        if char == "{":
                            stack.append(char)
                        elif char == "}":
                            if stack:
                                stack.pop()
                            if not stack:
                                func_code += line + "\n"
                                return func_code
                    func_code += line + "\n"
            return ""
        def extract_cpp_code(text, job) -> str:            
            if re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL) is not None:
                code = re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL).group(1)
            else:
                code = text
            func_signature = re.search(r"(\S+?\s+?\w+?\s*?)\(.*?\)\s*?\{\n", job["prompt"], flags=re.MULTILINE)
            if func_signature is not None:
                func_signature = func_signature.group(1).strip()
            else:
                print(job["prompt"])
            if code is not None and func_signature not in code:
                code = job["prompt"] + code
            extracted_code = extract_func_cpp(code, key_line = func_signature)
            if extracted_code == "":
                extracted_code = extract_func_cpp(code, key_line = func_signature.split(" ")[1])
            return extracted_code
        def extract_code_snippet(text, job):
            if re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL) is not None:
                code = re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL).group(1)
            else:
                code = text
            return code
        
        def remove_main(code):
            code_lines = code.split("\n")
            stack = []
            start = -1
            end = -1
            for i in range(0, len(code_lines)):
                if "main()" in code_lines[i]:
                    start = i
                if start >= 0:
                    for c in code_lines[i]:
                        if c == "{":
                            stack.append("{")
                        elif c == "}":
                            stack.pop()
                            if len(stack) == 0 and start >= 0:
                                end = i
                                return "\n".join(code_lines[:start] + code_lines[end + 1 :])


        use_rule = False
        if use_rule:
            code = extract_cpp_code(text, job)
        else:
            code = extract_code_snippet(text, job)
            if "main()" in code:
                code = remove_main(code)
            if int(job["task_id"].split("_")[1]) not in [147, 159]:
                code = code.replace("using namespace std;", "")

        test_set_up = ""
        for s in IMPORT_HELPER["cpp"]:
            if s not in code:
                test_set_up += s + "\n"
        code = test_set_up + "\n" + code + "\n"
        code = remove_nth_from_last_brace(code, n=1, ch="}")

    elif language == "go":
        def extract_go_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text
        code = extract_go_code(text)
        func_name = re.search(r"candidate := (.*?)\n", job["tests"], flags=re.DOTALL).group(1)
        if f"func {func_name}" not in code:
            code = job["prompt"] + code
    elif language == "js":  # javascript
        def extract_javascript_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text
        code = extract_javascript_code(text)
        if "function " not in code:
            code = job["prompt"] + code
    elif language == "ts":  # javascript
        def extract_typescript_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text
        code = extract_typescript_code(text)
        if "function" not in code:
            code = job["prompt"] + code
    elif language == "cs":  
        def extract_cs_code(text) -> str:
                code_block = re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL)
                if code_block is None:
                    return text
                else:
                    return code_block.group(1)

        def remove_main(code):
            code_lines = code.split("\n")
            stack = []
            start = -1
            end = -1
            for i in range(0, len(code_lines)):
                if "static void Main" in code_lines[i]:
                    start = i
                if start >= 0:
                    for c in code_lines[i]:
                        if c == "{":
                            stack.append("{")
                        elif c == "}":
                            stack.pop()
                            if len(stack) == 0 and start >= 0:
                                end = i
                                return "\n".join(code_lines[:start] + code_lines[end + 1 :])

        def extract_problem(code):
            code_lines = code.split("\n")
            stack = []
            start = -1
            end = -1
            for i in range(0, len(code_lines)):
                if "class Problem" in code_lines[i]:
                    start = i
                if start >= 0:
                    for c in code_lines[i]:
                        if c == "{":
                            stack.append("{")
                        elif c == "}":
                            stack.pop()
                            if len(stack) == 0 and start >= 0:
                                end = i
                                return "\n".join(code_lines[start : end + 1])
            return code

        code = extract_cs_code(text)
        existing_head = "\n".join([line for line in code.split("\n") if line.startswith("using")])
        func_name = re.search(r"Debug.Assert\((.*?)\(.*?\)\)", job["tests"], flags=re.DOTALL).group(1)
        if f" {func_name}(" not in code:
            code = job["prompt"] + code
        elif "class Problem" not in code:
            code = "class Problem {\n" + code
            if code.count("{") - code.count("}") > 0:
                code = code + "}\n" * (code.count("{") - code.count("}"))
        code = extract_problem(code)
        if "static void Main" in code:  # remove duplicate Main
            code = remove_main(code)
        # func_lines = [line for line in code.split("\n") if line.strip()]
        if code is not None:
            code = remove_nth_from_last_brace(code, n=2, ch="}")
            code = existing_head + "\n" + "\n".join(IMPORT_HELPER["cs"]) + "\n" + code
        else:
            code = extract_cs_code(text)
    elif language == "php":  # python
        def extract_php_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text
        code = extract_php_code(text)
        code = code.replace("?>", "")
        func_name = re.search(r"function (.*?)\(.*?\)", job["prompt"], flags=re.DOTALL).group(1)
        if f"function {func_name}" not in code:
            code = job["prompt"] + code
        if "<?php" not in code:
            code = "<?php\n" + code
    elif language == "sh":  
        def extract_shell_code(text) -> str:
            code_block_pattern = re.compile(rf"```.*?\n(.*?)```", re.DOTALL)
            code_block = code_block_pattern.search(text)
            if code_block is not None:
                return code_block.group(1)
            else:
                return text

        code = extract_shell_code(text)
        func_name = "_".join(job["name"].split("_")[2:])
        if f"{func_name}()" not in code:
            code = job["prompt"] + code
        code = remove_nth_from_last_brace(code, n=1, ch="}")
    return code


def parse_args():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument("--chat_format", "-chat_format", default="chatml", type=str, help="chat format")
    parser.add_argument("--model", "-model", default="", type=str, help="model path")
    parser.add_argument("--data_path", "-data_path", default="../data/", type=str, help="config path")
    parser.add_argument("--benchmark", "-benchmark", default="humaneval", type=str, help="benchmark name")
    parser.add_argument("--language", "-language", default="python", type=str, choices = ["python", "py", "sh", "java", "js", "cpp", "php", "cs", "ts"], help="langauge")
    parser.add_argument("--temperature", "-temperature", default=1.0, type=float)
    parser.add_argument("--tensor_parallel_size", "-tensor_parallel_size", default=4, type=int)
    parser.add_argument("--batch_size", "-batch_size", type=int, default=1, help="batch size")
    parser.add_argument("--do_sample", "-do_sample", default=False, type=bool, help="config path")
    parser.add_argument("--model_max_length", "-model_max_length", type=int, default=2048, help="model max length")
    parser.add_argument("--maxlen_out", "-maxlen_out", default=1024, type=int, help="config path")
    parser.add_argument("--metric_output_path", "-metric_output_path", default="", type=str, help="config path")
    parser.add_argument("--generation_path", "-generation_path", default="", type=str, help="config path")
    parser.add_argument("--generation_only", "-generation_only", action = "store_true")
    parser.add_argument("--evaluation_only", "-evaluation_only", action = "store_true")
    parser.add_argument("--use_vllm", "-use_vllm", action = "store_true")
    parser.add_argument("--worker_args", "-worker_args", default="", type=str, help="")
    args = parser.parse_args()
    return args

def chatml_query_preprocess(sources, tokenizer, max_len, system_message: str = "You are a helpful assistant."):
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

    test_input_ids = []
    system = [im_start] + _system + tokenizer(system_message).input_ids + [im_end] + nl_tokens
    test_input_ids += system
    for j, sentence in enumerate(sources):
        role = roles[sentence["role"]]
        _input_id = tokenizer(role).input_ids + nl_tokens + tokenizer(sentence["content"]).input_ids + [im_end] + nl_tokens
        test_input_ids += _input_id     
    test_input_ids += [im_start] + tokenizer("assistant").input_ids + nl_tokens
    test_input_str = tokenizer.decode(test_input_ids)
    return test_input_str, test_input_ids


def read_jsonl_file(file_name, max_sentence=None):
    data = []
    with jsonlines.open(file_name, "r") as r:
        for i, obj in tqdm.tqdm(enumerate(r)):
            if max_sentence is not None and i >= max_sentence:
                return data
            data.append(obj)
    return data

def write_jsonl_file(objs, path, chunk_size = 1):
    with jsonlines.open(path, "w", flush=True) as w:
        for i in tqdm.tqdm(range(0, len(objs), chunk_size)):
            w.write_all(objs[i: i + chunk_size])
    print(f"Successfully saving to {path}: {len(objs)}")

def get_humaneval_prompt(doc, language):
    language = language.lower()
    question = doc["prompt"].strip()
    return """
Please continue to complete the function and return all completed code in a codeblock. Here is the given code to do completion:
```{}
{}
```
""".strip().format(
        language.lower(), question.strip()
    )

def get_mbpp_prompt(doc, few_shots):
    def format_test_example(q, tests, code: str=None):
        prompt = "{} Your code should pass these tests:\n{}\n".format(q.strip(), "\n".join(tests))
        if code:
            code = code.replace("\r", "").replace("\t", "    ")
            prompt += "\n```python\n{}\n```".format(code)
        return prompt

    def get_few_shot_example():
        examples_str = []
        for i, obj in enumerate(few_shots):
            q, test, code = obj['text'], obj['test_list'], obj['code']
            ex_prompt = format_test_example(q, test, code)
            example_prompt = '- Example {}:\n{}'.format(i + 1, ex_prompt)
            examples_str += [example_prompt]
        return examples_str
    few_shot_prompt = get_few_shot_example()
    q, test, code = doc['text'], doc['test_list'], doc['code'] 
    prompt = format_test_example(q, test, code=None)
    prompt_with_shots = '''
Please refer the given examples and generate a python function for my problem.
Examples are listed as follows:
{}

Here is my problem:
{}
'''.strip().format('\n\n'.join(few_shot_prompt), prompt)
    return prompt_with_shots

def load_evaluation_dataset(chat_format, data_path, name, tokenizer, max_len, language):
    if name == "humaneval":
        test_data = read_jsonl_file(f"{data_path}/humaneval/humaneval-{language}.jsonl")
        for obj in test_data:
            if chat_format == "chatml":
                obj["input_prompt"] = get_humaneval_prompt(obj, language)
                obj["input"], obj["input_ids"] = chatml_query_preprocess([{'role': 'user', 'content': obj["input_prompt"]}], tokenizer, max_len = max_len)
            elif chat_format == "chat_template":
                obj["input_prompt"] = get_humaneval_prompt(obj, language)
                obj["input"] = tokenizer.apply_chat_template([{'role': 'user', 'content': obj["input_prompt"]}], add_generation_prompt=True, tokenize=False)
                obj["input_ids"] = tokenizer(obj["input"]).input_ids
    return test_data

def get_output(generation):
    chatml_pattern = re.compile(r"<\|im_start\|>assistant\n(.*?)<\|im_end\|>", flags=re.DOTALL)
    if chatml_pattern.search(generation) is not None:
        gen = chatml_pattern.search(generation).group(1)
    else:
        gen = generation
    return gen

def generate_one(args, obj, model, tokenizer):
    inputs = torch.tensor(obj["input_ids"]).to(model.device)
    if inputs.dim() == 1:
        inputs = inputs.unsqueeze(0)
    stop_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
    assert isinstance(stop_id, int), "Invalid tokenizer, <|im_end|> id not found"

    outputs = model.generate(
        inputs, 
        max_new_tokens=args.maxlen_out,
        do_sample=False,
        pad_token_id=stop_id,
        eos_token_id=stop_id
    )
    output = tokenizer.decode(outputs[0])
    output = get_output(output)
    obj['generation'] = output
    return obj


def read_log(path):
    data = json.load(open(path, "r"))
    return data["results"][0]

# def process_results(args, objs, language):
#     # get prompts and problem names
#     prompts_names = [{
#         "prompt": doc["prompt"] if "prompt" in doc else doc["text"], 
#         "name": doc["name"] if "name" in doc else f"{i}"} for i, doc in enumerate(objs),
#         "response": doc["generation"]
#     ]
#     #responses = [[obj["generation"]] for obj in objs]
#     generations = [[extract_func(obj["generation"], obj, language=language)] for obj in objs]
#     references = [obj["test"] if "test" in obj else obj["test_list"][0] for obj in objs]
#     # a common temp dir for all the problems
#     with tempfile.TemporaryDirectory() as temp_dir:
#         list_files = []
#         for prompt_name, generation, reference in zip(prompts_names, generations, references):
#             problem = {
#                 "name": prompt_name["name"],
#                 "language": language,
#                 "prompt": prompt_name["prompt"],
#                 "completions": generation,
#                 "response": prompt_name["response"],
#                 "tests": reference,
#             }
#             # each problem is save in a json file
#             temp_file_name = os.path.join(temp_dir, f"{prompt_name['name']}.json")
#             list_files.append(temp_file_name)
#             with open(temp_file_name, "wt") as f:
#                 json.dump(problem, f)
#         print(f"Saved {len(list_files)} problems in {temp_dir} for evaluation, each problem has {len(generations[0])} completions")

#         # execute the problems to evaluate them
#         max_workers = cpu_count() - 1 if cpu_count() > 1 else 1
#         for file in tqdm.tqdm(list_files):
#             evaluate_problem(temp_dir, file, max_workers)

#         # compute pass@k scores
#         result_array = np.array([for_file(p) for p in Path(temp_dir).glob("*.results.json")])
#         result = result_array.mean(axis=0)
#         name = temp_dir.split("/")[-1] if temp_dir.split("/")[-1] != "" else temp_dir.split("/")[-2]
#         results = {f"pass@{k}": v for k, v in zip([1, 10, 100], result) if k <= len(generations[0])}
#         logs = [read_log(f"{temp_dir}/{p.name}") for p in Path(temp_dir).glob("*.results.json")]
#     return results, logs


def check_correctness_multiple(code_string, programming_language):
    success = False
    logs = eval_string_script(programming_language, code_string)
    if logs["status"] == "OK":
        success = True
    return success, logs

def process_results(args, objs, language):
    logs_list = []
    for i, obj in tqdm.tqdm(enumerate(objs)):
        code_string = extract_func(obj["generation"], obj, language=language)
        code_string = code_string + "\n" + obj["test"]
        pass_at_1, logs = check_correctness_multiple(code_string, language)
        obj["pass@1"] = pass_at_1
        logs.update({
            "prompt": obj["prompt"] if "prompt" in obj else obj["text"],
            "name": obj["name"] if "name" in obj else f"{i}",
            "code_string": code_string,
            "pass@1": pass_at_1,
            "response": obj["generation"]
        })
        logs_list.append(logs)
    results = {
        "pass@1": round(sum([obj["pass@1"] for obj in objs]) / float(len(objs)) * 100.0, 1)
    }
    return results, logs_list


def main():
    args = parse_args()
    print(args)
    tokenizer = transformers.AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    #tokenizer.add_special_tokens({"additional_special_tokens": ["<|im_end|>", "<|im_start|>"]})
    
    test_data = load_evaluation_dataset(args.chat_format, data_path = args.data_path, name = args.benchmark, tokenizer = tokenizer, max_len = args.model_max_length, language = args.language)
    if args.use_vllm:
        if "llama-3" in args.model.lower():
            sampling_params = vllm.SamplingParams(temperature=0.0, top_p=0.95, max_tokens=4096, stop_token_ids=[128009])
        else:
            sampling_params = vllm.SamplingParams(temperature=0.0, top_p=0.95, max_tokens=4096)
        model = vllm.LLM(
            model = args.model, tensor_parallel_size = args.tensor_parallel_size,trust_remote_code=True)
        # model = vllm.LLM(
        #     model = args.model, tensor_parallel_size = args.tensor_parallel_size, worker_use_ray=True, trust_remote_code = True,
        #     gpu_memory_utilization=0.98, enforce_eager=True, 
        # )
    else:
        model = transformers.AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
    generated_objs = []
    if not args.evaluation_only:
        if args.use_vllm:
            prompts = [obj["input"] for obj in test_data]
            outputs = model.generate(prompts, sampling_params)
            for obj, o in zip(test_data, outputs):
                obj["generation"] = o.outputs[0].text
                generated_objs.append(obj)
        else:
            model.eval()
            for obj in tqdm.tqdm(test_data, desc='Generating Samples'):
                gen_example = generate_one(args, obj, model, tokenizer)
                generated_objs.append(gen_example)
        write_jsonl_file(generated_objs, args.generation_path)
    else:
        generated_objs = read_jsonl_file(args.generation_path)
    if not args.generation_only:
        results, logs = process_results(args, generated_objs, language = args.language)
        dumped = json.dumps(results, indent=2)
        write_jsonl_file(logs, f"{args.generation_path}.log")
        print(dumped)
        with open(args.metric_output_path, "w") as f:
            f.write(dumped)
 
if __name__ == "__main__":
    main()
