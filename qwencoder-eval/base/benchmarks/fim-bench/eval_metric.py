import re
import sys
import json
import timeout_decorator
import numpy as np

from tqdm import tqdm
from typing import Callable, List
from fuzzywuzzy import fuzz
import editdistance
from functools import partial
import torch.multiprocessing as mp
from tree_sitter import Language, Parser
from typing import List, Callable, Union
from tree_sitter.binding import Node as TSNode
import os

parser = None


def cal_edit_sim(references, hypotheses):
    total = len(references)
    edit_sim = 0.0
    for pred, gt in zip(hypotheses, references):
        pred = pred.strip()
        gt = gt.strip()
        edit_sim += fuzz.ratio(pred, gt)
    return edit_sim / total


def cal_edit_sim_repoeval(references, hypotheses):
    total = len(references)
    edit_sim = 0.0
    for pred, gt in zip(hypotheses, references):
        pred = pred.strip()
        gt = gt.strip()
        if max(len(pred), len(gt)) == 0:
            continue
        edit_sim += 1 - editdistance.eval(pred, gt) / max(len(pred), len(gt))
    return edit_sim / total


def tokenize_code(code):
    code = re.sub(r"([^A-Za-z0-9_])", r" \1 ", code)
    code = re.sub(r"([a-z])([A-Z])", r"\1 \2", code)
    code = re.sub(r"\s+", " ", code)
    code = code.replace('"', "`")
    code = code.replace("'", "`")
    tokens = [t for t in code.split(" ") if t]
    return tokens


def cal_exact_match(references, hypotheses):
    em_score = []
    for pred, gold in zip(hypotheses, references):
        em_score.append(tokenize_code(pred) == tokenize_code(gold))
    return np.mean(em_score)


def remove_comments(code):
    code = re.sub(r'#.*', '', code)
    return code


def is_parse_valid(parser, code):
    def syntax_error(node):
        if node.type == "ERROR":
            return True
        try:
            for child in node.children:
                if syntax_error(child):
                    return True
        except RecursionError as err:
            return True

        return False

    tree = get_ast(parser, code)
    if tree is not None:
        return not syntax_error(tree.root_node)
    return False


def get_valid_completion(prompt, completion, parser):
    for i in range(len(completion), -1, -1):
        code = prompt + completion[:i]
        if is_parse_valid(parser, code):
            return "parseable", completion[:i].rstrip()

    return "not_parseable", completion


def dfs(
        node: TSNode,
        node_types: List[str],
        callback: Callable,
        ignore_node_types: List[str] = None,
):
    """
    Helper to traverse parsed AST
    """
    if node.type in node_types:
        callback(node)

    for child in node.children:
        if not ignore_node_types or child.type not in ignore_node_types:
            dfs(child, node_types, callback, ignore_node_types)


def collect_nodes(root_node, node_types, ignore_node_types=None):
    """
    Collect all nodes that belong to certain types
    """
    result = list()

    def _cb(n):
        result.append(n)

    if root_node is not None:
        try:
            dfs(root_node, node_types, _cb, ignore_node_types)
        except RecursionError as err:
            print('collection of nodes failed due to RecursionError')
            return []

    return result

@timeout_decorator.timeout(5)
def get_ast(parser, code):
    assert isinstance(code, str) or isinstance(code, bytes)
    if isinstance(code, str):
        code = bytes(code, "utf8")
    try:
        tree = parser.parse(code)
        return tree
    except Exception as e:
        return None


def get_functions(parser, code):
    """
    This function returns all functions (irrespective of whether they are inside a class) in a dict format.
    :param code:
    :return: Dict()
    """
    try:
        tree = get_ast(parser, code)
    except:
        return []
    if tree is None:
        return []

    functions = []
    function_nodes = collect_nodes(tree.root_node, ["function_definition"])
    for fnode in function_nodes:
        assert fnode.children[-1].type == "block"
        body_text = fnode.children[-1].text.decode("utf-8")
        functions.append(body_text)

    return functions


def get_function_completion(prompt, completion, parser):
    code = prompt + "pass"
    target_fn_idx = len(get_functions(parser, code)) - 1
    # assert target_fn_idx != -1

    code = prompt + completion
    function_body = get_functions(parser, code)[target_fn_idx]
    return function_body


def process_examples(task, args):
    sample, ex = args
    global parser

    prediction = sample["pred"]
    target = ex["groundtruth"]
    origin = ""

    if task == "function_completion":
        status, prediction = get_valid_completion(ex["prompt"], prediction, parser)
        if status == "parseable":
            try:
                origin = prediction
                prediction = get_function_completion(ex["prompt"], prediction, parser)
                target = get_function_completion(ex["prompt"], target, parser)
            except:
                print(f'[warning] parsing failed: task_id:{ex["task_id"]}')
        else:
            print(f'[warning] parsing failed: task_id:{ex["task_id"]}')
    else:
        num_target_lines = sum([1 for l in target.split("\n") if l.strip()])
        pred_lines = [l for l in prediction.split("\n") if l.strip()][:num_target_lines]
        prediction = "\n".join(pred_lines)
    
    trunc_s = {
        "task_id": sample["task_id"],
        "pred": prediction,
        "target": target,
        #"origin": origin
    }
    
    return trunc_s


def compute_metric_stmt(args):
    all_task_results = {}
    
    for task in args.tasks:
        print(f"\nComputing metrics for task: {task}")
        with open(f"{args.output_dir}/{args.dataset}/{args.language}/{task}/prediction.jsonl", "r") as f_pred:
            samples = []
            for l in f_pred.readlines():
                samples.append(json.loads(l))

        # 构建task特定的prompt文件路径
        task_prompt_file = args.prompt_file.replace('TASK', task)
        examples = {}
        with open(task_prompt_file, "r") as f_in:
            for l in f_in.readlines():
                ex = json.loads(l)
                if hasattr(args, "focused_repo") and args.focused_repo and args.focused_repo not in re.sub('/', '_', ex['metadata']['repository']):
                    continue
                examples[ex["metadata"]["task_id"]] = {
                    "task_id": ex["metadata"]["task_id"],
                    "prompt": ex["prompt"],
                    "groundtruth": ex["groundtruth"]
                }

        if len(samples) == len(examples):
            print('Warning: len(samples) ({}) == len(examples) ({})'.format(len(samples), len(examples)))

        global parser
        ts_lang = args.language
        if ts_lang == 'csharp':
            ts_lang = 'c_sharp'
        language = Language(args.ts_lib, ts_lang)
        parser = Parser()
        parser.set_language(language)

        truncated_samples = []
        print("post-processing samples ...")
        pool = mp.Pool(mp.cpu_count() - 1)
        worker = partial(process_examples, task)

        with tqdm(total=len(samples)) as pbar:
            for trunc_s in pool.imap_unordered(worker, zip(samples, [examples[s["task_id"]] for s in samples])):
                truncated_samples.append(trunc_s)
                pbar.update()

        pool.close()
        pool.join()

        task_output_dir = os.path.join(args.output_dir, args.dataset, args.language, task)
        # with open(f"{task_output_dir}/prediction_truncated.jsonl", 'w', encoding="utf-8") as pt:
        #     for trunc_s in truncated_samples:
        #         pt.write(json.dumps(trunc_s) + "\n")

        ### Score calculation
        detailed_results = []
        exact_match = 0
        edit_sim = 0
        edit_sim_repoeval = 0

        for idx, trunc_s in enumerate(truncated_samples):
            es = cal_edit_sim([trunc_s["target"]], [trunc_s["pred"]])
            es_repoeval = cal_edit_sim_repoeval([trunc_s["target"]], [trunc_s["pred"]])
            em = cal_exact_match([trunc_s["target"]], [trunc_s["pred"]])
            edit_sim += es
            edit_sim_repoeval += es_repoeval
            exact_match += em

            detailed_results.append({
                "task_id": trunc_s["task_id"],
                "pred": trunc_s["pred"],
                "target": trunc_s["target"],
                "em": em,
                "es": es,
                "es_repoeval": es_repoeval
            })

        total_samples = len(truncated_samples)
        em_ratio = round(exact_match / total_samples * 100, 2)
        edit_sim_avg = round(edit_sim / total_samples, 2)
        edit_sim_repoeval_avg = round(edit_sim_repoeval / total_samples * 100, 2)

        print(
            f"Code Matching for {task}: "
            f"EM {em_ratio:.2f}, "
            f"ES {edit_sim_avg:.2f}, "
            f"ES RepoEval {edit_sim_repoeval_avg:.2f}"
        )

        # 保存详细结果
        with open(f"{task_output_dir}/detailed_results.json", 'w') as f:
            for dr in detailed_results:
                f.write(json.dumps(dr) + "\n")

        # 保存任务级别的结果
        task_results = {
            "em": em_ratio,
            "es": edit_sim_avg,
            "es_repoeval": edit_sim_repoeval_avg,
            "total": total_samples
        }
        
        with open(f"{task_output_dir}/results.json", 'w') as f:
            json.dump(task_results, f, indent=2)
            
        # 将当前任务的结果添加到总结果字典中
        all_task_results[task] = task_results

    # 计算所有任务的加权平均值
    total_samples = sum(res["total"] for res in all_task_results.values())
    weighted_em = sum(res["em"] * res["total"] for res in all_task_results.values()) / total_samples
    weighted_es = sum(res["es"] * res["total"] for res in all_task_results.values()) / total_samples
    weighted_es_repoeval = sum(res["es_repoeval"] * res["total"] for res in all_task_results.values()) / total_samples

    # 创建最终的合并结果
    merged_results = {
        "overall": {
            "em": round(weighted_em, 4),
            "es": round(weighted_es, 4),
            "es_repoeval": round(weighted_es_repoeval, 4),
            "total": total_samples
        },
        "per_task": all_task_results
    }

    # 保存合并后的结果
    with open(f"{args.output_dir}/{args.dataset}/results.json", 'w') as f:
        json.dump(merged_results, f, indent=2)

    print("\nOverall Results (Weighted Average):")
    print(f"EM: {weighted_em:.2f}")
    print(f"ES: {weighted_es:.2f}")
    print(f"ES RepoEval: {weighted_es_repoeval:.2f}")
    print(f"Total Samples: {total_samples}")

def compute_metric_stmt_multilang(args):
    all_task_results = {}
    
    for language in args.languages:
        print(f"\nComputing metrics for language: {language}")
        with open(f"{args.output_dir}/{args.dataset}/{language}/{args.task}/prediction.jsonl", "r") as f_pred:
            samples = []
            for l in f_pred.readlines():
                samples.append(json.loads(l))

        # 构建task特定的prompt文件路径
        task_prompt_file = args.prompt_file.replace('LANGUAGE', language)
        examples = {}
        with open(task_prompt_file, "r") as f_in:
            for l in f_in.readlines():
                ex = json.loads(l)
                if hasattr(args, "focused_repo") and args.focused_repo and args.focused_repo not in re.sub('/', '_', ex['metadata']['repository']):
                    continue
                examples[ex["metadata"]["task_id"]] = {
                    "task_id": ex["metadata"]["task_id"],
                    "prompt": ex["prompt"],
                    "groundtruth": ex["groundtruth"]
                }

        if len(samples) == len(examples):
            print('Warning: len(samples) ({}) == len(examples) ({})'.format(len(samples), len(examples)))

        global parser
        ts_lang = language
        if ts_lang == 'csharp':
            ts_lang = 'c_sharp'

        ts_lib = args.ts_lib.replace('LANGUAGE', language)
        language_ts = Language(ts_lib, ts_lang)
        parser = Parser()
        parser.set_language(language_ts)

        truncated_samples = []
        print("post-processing samples ...")
        pool = mp.Pool(mp.cpu_count() - 1)
        worker = partial(process_examples, args.task)

        with tqdm(total=len(samples)) as pbar:
            for trunc_s in pool.imap_unordered(worker, zip(samples, [examples[s["task_id"]] for s in samples])):
                truncated_samples.append(trunc_s)
                pbar.update()

        pool.close()
        pool.join()

        task_output_dir = os.path.join(args.output_dir, args.dataset, language, args.task)
        # with open(f"{task_output_dir}/prediction_truncated.jsonl", 'w', encoding="utf-8") as pt:
        #     for trunc_s in truncated_samples:
        #         pt.write(json.dumps(trunc_s) + "\n")

        ### Score calculation
        detailed_results = []
        exact_match = 0
        edit_sim = 0
        edit_sim_repoeval = 0

        for idx, trunc_s in enumerate(truncated_samples):
            es = cal_edit_sim([trunc_s["target"]], [trunc_s["pred"]])
            es_repoeval = cal_edit_sim_repoeval([trunc_s["target"]], [trunc_s["pred"]])
            em = cal_exact_match([trunc_s["target"]], [trunc_s["pred"]])
            edit_sim += es
            edit_sim_repoeval += es_repoeval
            exact_match += em

            detailed_results.append({
                "task_id": trunc_s["task_id"],
                "pred": trunc_s["pred"],
                "target": trunc_s["target"],
                "em": em,
                "es": es,
                "es_repoeval": es_repoeval
            })

        total_samples = len(truncated_samples)
        em_ratio = round(exact_match / total_samples * 100, 2)
        edit_sim_avg = round(edit_sim / total_samples, 2)
        edit_sim_repoeval_avg = round(edit_sim_repoeval / total_samples * 100, 2)

        print(
            f"Code Matching for {language}: "
            f"EM {em_ratio:.2f}, "
            f"ES {edit_sim_avg:.2f}, "
            f"ES RepoEval {edit_sim_repoeval_avg:.2f}"
        )

        # 保存详细结果
        with open(f"{task_output_dir}/detailed_results.json", 'w') as f:
            for dr in detailed_results:
                f.write(json.dumps(dr) + "\n")

        # 保存任务级别的结果
        task_results = {
            "em": em_ratio,
            "es": edit_sim_avg,
            "es_repoeval": edit_sim_repoeval_avg,
            "total": total_samples
        }
        
        with open(f"{task_output_dir}/results.json", 'w') as f:
            json.dump(task_results, f, indent=2)
            
        # 将当前任务的结果添加到总结果字典中
        all_task_results[language] = task_results

    # 计算所有任务的加权平均值
    total_samples = sum(res["total"] for res in all_task_results.values())
    weighted_em = sum(res["em"] * res["total"] for res in all_task_results.values()) / total_samples
    weighted_es = sum(res["es"] * res["total"] for res in all_task_results.values()) / total_samples
    weighted_es_repoeval = sum(res["es_repoeval"] * res["total"] for res in all_task_results.values()) / total_samples

    # 创建最终的合并结果
    merged_results = {
        "overall": {
            "em": round(weighted_em, 4),
            "es": round(weighted_es, 4),
            "es_repoeval": round(weighted_es_repoeval, 4),
            "total": total_samples
        },
        "per_language": all_task_results
    }

    # 保存合并后的结果
    with open(f"{args.output_dir}/{args.dataset}/results.json", 'w') as f:
        json.dump(merged_results, f, indent=2)

    print("\nOverall Results (Weighted Average):")
    print(f"EM: {weighted_em:.2f}")
    print(f"ES: {weighted_es:.2f}")
    print(f"ES RepoEval: {weighted_es_repoeval:.2f}")
    print(f"Total Samples: {total_samples}")


def compute_metric_stmt_custom(predictions_file, prompt_file, output_dir, 
                               ts_lib, task, focused_repo=None, anchor_file=None, out_f_suffix=""):
    eval_ids = set()

    if anchor_file:
        with open(anchor_file, "r") as f_pred:
            for l in f_pred.readlines():
                eval_ids.add(json.loads(l)['task_id'])

    with open(predictions_file, "r") as f_pred:
        samples = []
        for l in f_pred.readlines():
            if anchor_file:
                if json.loads(l)['task_id'] in eval_ids:
                    samples.append(json.loads(l))
            else:
                entry = json.loads(l)
                # entry['task_id'] = re.sub('-', '_',entry['task_id'])
                if entry['task_id'] in eval_ids:
                    continue
                if focused_repo is not None:
                    if type(focused_repo) == str and focused_repo not in re.sub('/', '_', entry['task_id']):
                        continue
                    elif type(focused_repo) == list and not any([x in re.sub('/', '_', entry['task_id']) for x in focused_repo]):
                        continue
                samples.append(entry)
                eval_ids.add(entry['task_id'])

    examples = {}
    with open(prompt_file, "r") as f_in:
        for l in f_in.readlines():
            ex = json.loads(l)
            if focused_repo is not None:
                if type(focused_repo) == str and focused_repo not in re.sub('/', '_', ex['metadata']['repository']):
                    continue
                elif type(focused_repo) == list and not any([x in re.sub('/', '_', ex['metadata']['repository']) for x in focused_repo]):
                    continue
            if ex["metadata"]["task_id"] not in eval_ids:
                continue
            examples[ex["metadata"]["task_id"]] = {
                "task_id": ex["metadata"]["task_id"],
                "prompt": ex["prompt"],
                "groundtruth": ex["groundtruth"]
            }

    assert len(samples) == len(examples), f"{len(samples)} != {len(examples)}"

    global parser
    language = Language(ts_lib, "python")
    parser = Parser()
    parser.set_language(language)

    truncated_samples = []
    print("post-processing samples ...")
    pool = mp.Pool(mp.cpu_count() - 1)
    worker = partial(process_examples, task)

    with tqdm(total=len(samples)) as pbar:
        for trunc_s in pool.imap_unordered(worker, zip(samples, [examples[s["task_id"]] for s in samples])):
            truncated_samples.append(trunc_s)
            pbar.update()

    with open(f"{output_dir}/prediction_truncated{out_f_suffix}.jsonl", 'w', encoding="utf-8") as pt:
        for trunc_s in truncated_samples:
            pt.write(json.dumps(trunc_s) + "\n")

    ### Score calculation

    detailed_results = []
    exact_match = 0
    edit_sim = 0
    edit_sim_repoeval = 0

    for idx, trunc_s in enumerate(truncated_samples):
        es = cal_edit_sim([trunc_s["target"]], [trunc_s["pred"]])
        es_repoeval = cal_edit_sim_repoeval([trunc_s["target"]], [trunc_s["pred"]])
        em = cal_exact_match([trunc_s["target"]], [trunc_s["pred"]])
        edit_sim += es
        edit_sim_repoeval += es_repoeval
        exact_match += em

        detailed_results.append({
            "task_id": trunc_s["task_id"],
            "em": em,
            "es": es,
            "es_repoeval": es_repoeval
        })

    em_ratio = round(exact_match / len(truncated_samples) * 100, 2)
    edit_sim = round(edit_sim / len(truncated_samples), 2)
    edit_sim_repoeval = round(edit_sim_repoeval / len(truncated_samples) * 100, 2)

    print(
        f"Code Matching: "
        f"EM {em_ratio:.2f}, "
        f"ES {edit_sim:.2f}, "
        f"ES RepoEval {edit_sim_repoeval:.2f}"
    )

    with open(f"{output_dir}/detailed_results{out_f_suffix}.json", 'w') as f:
        for dr in detailed_results:
            f.write(json.dumps(dr) + "\n")

    # write the results to a file
    with open(f"{output_dir}/results{out_f_suffix}.json", 'w') as f:
        res = {
            "em": em_ratio,
            "es": edit_sim,
            "es_repoeval": edit_sim_repoeval,
            "total": len(truncated_samples)
        }
        f.write(json.dumps(res, indent=2))

def extract_block(text: str) -> str:
    """提取文本中代码块的内容"""
    start = text.find('```') + 3
    end = text.find('```', start)
    content = text[start:end]
    return content