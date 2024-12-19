from utils import utils
import argparse
import transformers
import json
import tqdm
import vllm
import tempfile
from utils import prompt_template
import os
import subprocess
import numpy as np
import collections
def parse_args():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument("--model_name", "-model_name", default="deepseek-coder-33B", type=str, help="model path")
    parser.add_argument("--model_dir", "-model_dir", default="./deepseek-ai/deepseek-coder-33b-base", type=str, help="model path")
    parser.add_argument("--input_path", "-input_path", default="./exec_repo_bench.jsonl", type=str, help="")
    parser.add_argument("--output_path", "-output_path", default="./results/deepseek-coder-33b-base/test.jsonl", type=str, help="")
    parser.add_argument("--generation_only", "-generation_only", action="store_true", help="")
    parser.add_argument("--evaluation_only", "-evaluation_only", action="store_true", help="")
    parser.add_argument("--tensor_parallel_size", "-tensor_parallel_size", default = 1, type=int, help="")
    parser.add_argument("--workers", "-workers", default = 64, type=int, help="")
    parser.add_argument("--chunk_size", "-chunk_size", default = 10, type=int, help="")
    parser.add_argument("--context_order", "-context_order", default="close", choices=["far", "close"], help="")
    parser.add_argument("--env_path", "-env_path", default="./repo/envs/", type=str, help="")
    parser.add_argument("--repo_dir", "-repo_dir", default="./repos", type=str, help="")
    #
    parser.add_argument("--max_context_tokens", "-max_context_tokens", default=4096, type=int, help="")
    parser.add_argument("--max_generation_tokens", "-max_generation_tokens", default=512, type=int, help="")
    parser.add_argument("--max_tokens", "-max_tokens", default=8192, type=int, help="")
    parser.add_argument("--verbose", "-verbose", action="store_true", help="")
    args = parser.parse_args()
    return args


def evaluate_correctness(obj, args):
    repo_name = obj["repo_name"]
    masked_file = obj["file_name"]
    prefix_code = obj["prefix_code"]
    middle_code = obj["generated_middle_code"] if "generated_middle_code" in obj else obj["middle_code"]
    suffix_code = obj["suffix_code"]
    code = prefix_code + middle_code + suffix_code
    repo_dir = args.repo_dir
    env_path = args.env_path
    with tempfile.TemporaryDirectory() as executable_repo_root_path:
        utils.copy_src_to_dest(repo_dir, executable_repo_root_path, repo_name)
        masked_file = f"{executable_repo_root_path}/{masked_file}"
        with open(masked_file, "w") as w:
            w.write(code)
        if args.verbose:
            print(f"Executing {repo_name} ({masked_file})")
        os.environ["PATH"] = f"{env_path}/repo_{repo_name}/bin:" + os.environ["PATH"]
        os.chdir(os.path.join(executable_repo_root_path, repo_name))
        timeout_seconds = 240
        try:
            results = subprocess.run(f"python evaluate_repo.py", shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout = timeout_seconds) #f"{executable_repo_root_path}/{repo_name}"
        except subprocess.TimeoutExpired:
            return 0.0, f"The command timed out after {timeout_seconds} seconds."
        if results.returncode != 0:
            return 0.0, results.stderr.decode("utf8")
    return 1.0, ""

def evaluate_objs_correctness(objs, worker_id, workers, args):
    for obj in tqdm.tqdm(objs, position=worker_id, desc=f"Worker {worker_id}/{workers}"):
        is_pass, stderr = evaluate_correctness(obj, args)
        obj["is_pass"] = is_pass
        obj["stderr"] = stderr
    return objs

def evaluate_es_score(obj):
    hypo = utils.remove_comments(obj["middle_code"], language = "python")
    ref = utils.remove_comments(obj["generated_middle_code"], language = "python")
    es_score = utils.cal_edit_sim([ref], [hypo])
    return es_score

def evaluate_all_correctness(objs, args):
    if objs is None:
        objs = utils.read_jsonl_file(args.output_path)
    for obj in tqdm.tqdm(objs):
        obj["es"] = evaluate_es_score(obj)
    objs = utils.multi_tasks_from_objs(objs, workers = args.workers, task = evaluate_objs_correctness, chunk_size = args.chunk_size, args = args)
    results = {}
    results["pass_at_1"] = round(utils.get_avg_score(objs, "is_pass") * 100, 1)
    results["es"] = round(utils.get_avg_score(objs, "es"), 1)
    results_dict = collections.defaultdict(list)
    for obj in objs:
        results_dict[obj["fill_type"]].append(obj)
    for k in results_dict:
        results[f"{k}:es"] = round(utils.get_avg_score(results_dict[k], "es"), 1)
        results[f"{k}:pass@1"] = round(utils.get_avg_score(results_dict[k], "is_pass") * 100, 1)
    #
    keys = ['Random Span Completion', 'Random Single-line Completion', 'Random Multi-line Completion', 'grammar-based: expression', 'grammar-based: statement', 'grammar-based: block']
    all_results = []
    for k in keys:
        pass_at_1 = results[f"{k}:es"]
        es = results[f"{k}:pass@1"]
        all_results.append(str(pass_at_1))
        all_results.append(str(es))
    all_results.append(str(results["es"]))
    all_results.append(str(results["pass_at_1"]))
    #all_results = [f"\colornum{{{r}}}" for r in all_results]
    results["latex_str"] = " & ".join(all_results)
    return objs, results

def get_continue_prompt_with_suffix(file_name, context_code, prefix_code, suffix_code):
    suffix_code_lines = suffix_code.split("\n")
    suffix_code_lines = ["# " + line for line in suffix_code_lines]
    suffix_code = "\n".join(suffix_code_lines)
    suffix_code = f"## Suffix code of {file_name}\n{suffix_code}"
    prefix_code = f"## Prefix code of {file_name}\n{prefix_code}"
    return f"{context_code}\n{file_name}\n{suffix_code}\n{prefix_code}"

def get_prompt(tokenizer, obj, args):
    context_code_files, prefix_code, suffix_code = obj["context_code"], obj["prefix_code"], obj["suffix_code"]
    context_code = []
    context_code_file_names = []
    context_code_tokens = 0
    for file_name, file_code in context_code_files:
        cur_tokens = tokenizer.tokenize(file_code)
        if len(cur_tokens) + context_code_tokens < args.max_context_tokens:
            context_code_tokens += len(cur_tokens)
            context_code.append(f"##{file_name}##:\n{file_code}")
            context_code_file_names.append(file_name)
        else:
            _context_code = f"##{file_name}##:\n{file_code}"
            _context_code = utils.truncate_prompt(_context_code, max_num_tokens = args.max_context_tokens - context_code_tokens, tokenizer = tokenizer, side="right")
            _context_code = "\n".join(_context_code.split("\n")[:-1])
            context_code.append(_context_code)
            context_code_file_names.append(file_name)
            break
    if args.context_order == "close":
        context_code = context_code[::-1]
        context_code_file_names = context_code_file_names[::-1]
    max_in_file_tokens = args.max_tokens - args.max_generation_tokens - args.max_context_tokens
    prefix_code = utils.truncate_prompt(prefix_code, max_num_tokens = max_in_file_tokens // 2, tokenizer = tokenizer, side="left")
    suffix_code = utils.truncate_prompt(suffix_code, max_num_tokens = max_in_file_tokens // 2, tokenizer = tokenizer, side="right")
    if "codeqwen1.5-base" in args.model_name:
        repo_start = f"<repo_name>{obj['repo_name']}"
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n<file_sep>{f}\n{c}"
        context_code = repo_start + repo_content + f"\n<file_sep>{obj['file_name']}\n"
        input_prompt = prompt_template.CODEQWEN_BASE_TEMPLATE.format(context_code, prefix_code, suffix_code)
        obj["input"] = input_prompt
    elif "qwen2.5-coder-base-" in args.model_name:
        repo_start = f"<|repo_name|>{obj['repo_name']}"
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n<|file_sep|>{f}\n{c}"
        context_code = repo_start + repo_content + f"\n<|file_sep|>{obj['file_name']}\n"
        input_prompt = prompt_template.QWEN_CODER_TEMPLAT.format(context_code, prefix_code, suffix_code)
        obj["input"] = input_prompt
    elif "starcoder-" in args.model_name:
        prompt_with_suffix = False
        if prompt_with_suffix:
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n## {f}\n{c}"
            obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
        else:
            repo_start = f"<repo_name>{obj['repo_name']}"
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n<file_sep>{f}\n{c}"
            context_code = repo_start + repo_content + f"\n<file_sep>{obj['file_name']}\n"
            input_prompt = prompt_template.CODEQWEN_BASE_TEMPLATE.format(context_code, prefix_code, suffix_code)
            obj["input"] = input_prompt
    elif "starcoder2-" in args.model_name:
        prompt_with_suffix = True
        if prompt_with_suffix:
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n## {f}\n{c}"
            obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
        else:
            repo_start = f"<repo_name>{obj['repo_name']}"
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n<file_sep>{f}\n{c}"
            context_code = repo_start + repo_content + f"\n<file_sep>{obj['file_name']}\n"
            input_prompt = prompt_template.STARCODER2_BASE_TEMPLATE.format(context_code, prefix_code, suffix_code)
            obj["input"] = input_prompt
    elif "deepseek-coder" in args.model_name:
        prompt_with_suffix = False
        if prompt_with_suffix:
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n## {f}\n{c}"
            obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
        else:
            repo_content = []
            for c, f in zip(context_code, context_code_file_names):
                repo_content.append(f"#{f}\n{c}")
            context_code = "\n".join(repo_content)
            input_prompt = prompt_template.DEEPSEEK_CODER_BASE_TEMPLATE.format(context_code, prefix_code, suffix_code)
            obj["input"] = input_prompt
    elif "codegeex" in args.model_name:
        prompt_with_suffix = True
        if prompt_with_suffix:
            repo_content = ""
            for c, f in zip(context_code, context_code_file_names):
                repo_content += f"\n## {f}\n{c}"
            obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
        else:
            repo_content = []
            for c, f in zip(context_code, context_code_file_names):
                repo_content.append(f"#{f}\n{c}")
            context_code = "\n".join(repo_content)
            input_prompt = prompt_template.DEEPSEEK_CODER_TEMPLATE.format(context_code, prefix_code, suffix_code)
    elif "qwen2.5-coder-C" in args.model_name:
        context_code = "\n".join(context_code)
        input_prompt = prompt_template.REPO_COMPLETE_TEMPLATE.format(context_code, prefix_code, suffix_code)
        system_prompt = prompt_template.SYSTEM_PROMPT
        obj["input"] = {
            "messages": [
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": input_prompt}, 
            ],
        }
        obj["input"] = tokenizer.apply_chat_template(obj["input"]["messages"], add_generation_prompt=True, tokenize=False)
    elif "codellama" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "granite-coder-base" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "opencoder-base" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "codestral-" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "codegeex-" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "yi-coder" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    elif "codegemma" in args.model_name:
        repo_content = ""
        for c, f in zip(context_code, context_code_file_names):
            repo_content += f"\n## {f}\n{c}"
        obj["input"] = get_continue_prompt_with_suffix(obj["file_name"], repo_content, prefix_code, suffix_code)
    else:
        raise NotImplementedError(f"Undefined Model Name!")
    return obj

def generate_samples(args):
    test_data = utils.read_jsonl_file(args.input_path, max_sentence=None)
    objs = []
    tokenizer = transformers.AutoTokenizer.from_pretrained(args.model_dir, trust_remote_code=True)
    config = json.load(open(f"{args.model_dir}/config.json", "r"))
    if "max_position_embeddings" in config:
        supported_max_length = config["max_position_embeddings"]
    elif "n_positions" in config:
        supported_max_length = config["n_positions"]
    else:
        supported_max_length = 8192
        #raise NotImplementedError(f"Can not find supported max length in config file!")
    if supported_max_length < args.max_tokens:
        args.max_tokens = supported_max_length
        args.max_context_tokens = supported_max_length // 2
    print(f"generating {len(test_data)} prompts...")
    min_gen_tokens_len = 100000000
    max_gen_tokens_len = -1
    for obj in tqdm.tqdm(test_data):
        prefix_code = obj["prefix_code"]
        suffix_code = obj["suffix_code"]
        context_code_files = obj["context_code"]
        obj = get_prompt(tokenizer, obj, args)
        gen_tokens_len = len(tokenizer.tokenize(obj["middle_code"]))
        if max_gen_tokens_len < gen_tokens_len:
            max_gen_tokens_len = gen_tokens_len + 10
        if min_gen_tokens_len > gen_tokens_len:
            min_gen_tokens_len = gen_tokens_len
        #obj["input"] = tokenizer.apply_chat_template(obj["input"]["messages"], add_generation_prompt=True, tokenize=False)
        objs.append(obj)
    print(f"Suggusting min: {min_gen_tokens_len}, max: {max_gen_tokens_len} tokens")
    extra_params = {}
    if "codeqwen-base" in args.model_name:
        extra_params["stop_token_ids"] = [tokenizer.convert_tokens_to_ids("<file_sep>")]
    sampling_params = vllm.SamplingParams(temperature = 0.0, top_p = 0.95, max_tokens = args.max_generation_tokens, **extra_params)
    model = vllm.LLM(
        model = args.model_dir, tensor_parallel_size = args.tensor_parallel_size, worker_use_ray=True, trust_remote_code=True, enforce_eager=True
    )
    generated_objs = []
    prompts = [obj["input"] for obj in objs]
    outputs = model.generate(prompts, sampling_params)
    for obj, o in zip(objs, outputs):
        obj["generated_middle_code"] = o.outputs[0].text
        generated_objs.append(obj)
    utils.write_jsonl_file(generated_objs, args.output_path)
    return generated_objs

def main():
    args = parse_args()
    print(args)
    generated_samples = None
    if not args.evaluation_only:
        generated_samples = generate_samples(args)
    if not args.generation_only:
        objs, results = evaluate_all_correctness(generated_samples, args)
        utils.write_jsonl_file(objs, f"{args.output_path}.results")
        results.update(vars(args))
        utils.save_json(results, f"{args.output_path}.metrics")
        print(results)

if __name__ == "__main__":
    main()
