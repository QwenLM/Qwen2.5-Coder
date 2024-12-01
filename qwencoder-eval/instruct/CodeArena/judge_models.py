import yaml
import argparse
from utils import utils
import os
import re
import collections
import tqdm
import jsonlines
import json
import numpy as np
def make_config(config_file):
    config_kwargs = {}
    with open(config_file, "r") as f:
        config_kwargs = yaml.load(f, Loader=yaml.SafeLoader)
    return config_kwargs

def get_score(judgment, pattern, pairwise=True):
    matches = pattern.findall(judgment)
    matches = [m for m in matches if m != ""]
    if len(set(matches)) == 0:
        return None, True
    elif len(set(matches)) == 1:
        if pairwise:
            return matches[0].strip("\n"), False
        return int(matches[0])
    else:
        return None, False

def start_judgement(obj, model_name, baseline_name, reference = None, configs = None):
    num_games = 2
    baseline = [obj[baseline_name]] if baseline_name in obj else [obj["baseline"]]
    answer = [obj[model_name]]
    question = obj["question"]
    obj["games"] = []
    for game in range(num_games):
        conv = [{"role": "system", "content": configs["system_prompt"]}]
        for template in configs["prompt_template"]:
            prompt_args = {}
            for i, q in enumerate(question):
                prompt_args[f"question_{i+1}"] = q
            base = 1
            if baseline:
                if game % 2 == 1: # swap position
                    answer, baseline = baseline, answer
                for i, a in enumerate(baseline):
                    prompt_args[f"answer_{i+1}"] = a
                    base += 1
            if answer:
                for i, a in enumerate(answer):
                    prompt_args[f"answer_{i+base}"] = a
            if reference:
                for j, ref_answer in enumerate(reference):
                    for i, turn in enumerate(ref_answer["choices"][0]["turns"]):
                        prompt_args[f"ref_answer_{i+j+1}"] = turn["content"]      
            user_prompt = template.format(**prompt_args)
            conv.append({"role": "user", "content": user_prompt})
        judgment = ""
        score = None
        for _ in range(configs['number_of_judgment_attempts']):
            openai_args = {
                "model": "gpt-4o",  # gpt-4o model='gpt-3.5-turbo-0613',  gpt-3.5-turbo-16k-0613 model='gpt-4' gpt-3.5-turbo-16k chatgpt-4o-latest
                "temperature": 0.2,
                "max_tokens": 16384,
                "messages": conv,
            }
            try:
                new_judgment = utils.call_gpt4o(**openai_args)
            except:
                continue
            # if new_judgment == "[[API FAIL]]":
            #     continue
            judgment += ("\n" + new_judgment)
            score, try_again = get_score(judgment, configs["regex_pattern"])
            conv.append({"role": "assistant", "content": new_judgment})
            if not try_again:
                break
            conv.append({"role": "user", "content": "continue your judgment and finish by outputting a final verdict label"})
        result = {
            "user_prompt": conv[1]["content"],
            "judgment": judgment,
            "score": score
        }
        obj["games"].append(result)
    return obj

def start_judgements(objs, worker_id, workers, args):
    data = []
    output_path = args["output_path"]
    with jsonlines.open(f"{output_path}.worker-{worker_id}", "a", flush=True) as w:
        for obj in tqdm.tqdm(objs, position=worker_id, desc=f"Worker {worker_id}/{workers}"):
            obj = start_judgement(obj, model_name = args["model_name"], baseline_name = args["baseline_name"], reference = args["reference"], configs = args["configs"])
            data.append(obj)
            w.write(obj)
    return data

def load_data(input_path, output_path):
    _objs = utils.read_jsonl_file(input_path)
    for obj in _objs:
        obj["question"] = [ obj["messages"][0]["content"] ]
        # obj["GPT-4"] = [ obj["gpt-4-turbo-2024-04-09_response"] ]
        # obj["Qwen2-72B"] = [ obj["qwen2-72B-generation"] ]

    def load_cached_objs(output_path):
        result_name = os.path.basename(output_path)
        root_dir = os.path.dirname(output_path)
        file_names = [f for f in os.listdir(root_dir) if f.startswith(f"{result_name}.")]
        cached_objs = {}
        for file_name in file_names:
            objs = utils.read_jsonl_file(f"{root_dir}/{file_name}")
            for obj in objs:
                if obj.get("id"):
                    cached_objs[obj["id"]] = obj
        print(f"Successfully loading {len(cached_objs)} cached objs")
        return cached_objs
    cached_objs = load_cached_objs(output_path)

    cached_cnt = 0
    left_objs = []
    for i, obj in enumerate(_objs):
        obj["id"] = i
        if obj["id"] in cached_objs:
            cached_cnt += 1
            continue
        if len(obj["question"][0].split()) < 1024:
            left_objs.append(obj)
    return left_objs, cached_objs


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", "-input_path", type=str, default="./results.jsonl")
    parser.add_argument("--output_path", "-output_path", type=str, default="./results.jsonl.judge")
    parser.add_argument("--setting_file", "-setting_file", type=str, default="./utils/judge_config.yaml")
    parser.add_argument("--mapping_file", "-mapping_file", type=str, default="./utils/tasktype_to_levels.json")
    parser.add_argument("--workers", "-workers", type=int, default=1)
    parser.add_argument("--judgement_only", "-judgement_only", action = "store_true")
    parser.add_argument("--evaluation_only", "-evaluation_only", action = "store_true")
    parser.add_argument("--baseline_name", "-baseline_name", type = str, default = "gpt-4-turbo-2024-04-09", choices=["gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13"])
    args = parser.parse_args()
    return args

def format_score(s):
    return round(s * 100, 1)

def calculate_classified_score(objs, tasktype_to_levels):
    def wash_tag(e):
        e = e.replace("-", " ")
        return e.lower()
    main_classified_objs = collections.defaultdict(list)
    sub_classified_objs = collections.defaultdict(list)
    for obj in objs:
        task_type = wash_tag(obj["meta"]["parsed"]["task_type"][0])
        main_class, sub_class = tasktype_to_levels[task_type][0]
        main_classified_objs[main_class].append(obj)
        sub_classified_objs[sub_class].append(obj)
    main_classified_scores = {}
    for k in main_classified_objs:
        main_classified_scores_win = np.average([o["if_win"] for o in main_classified_objs[k]])
        main_classified_scores_tie = np.average([o["if_tie"] for o in main_classified_objs[k]])
        main_classified_scores[k] = f"{format_score(main_classified_scores_win)}/{format_score(main_classified_scores_tie)}"
    sub_classified_scores = {}
    for k in sub_classified_objs:
        sub_classified_scores_win = np.average([o["if_win"] for o in sub_classified_objs[k]])
        sub_classified_scores_tie = np.average([o["if_tie"] for o in sub_classified_objs[k]])
        sub_classified_scores[k] = f"{format_score(sub_classified_scores_win)}/{format_score(sub_classified_scores_tie)}"
    return main_classified_scores, sub_classified_scores

def get_scores(objs, tasktype_to_levels, strict=False):
    def score(scores):
        win = 0
        for i in range(len(scores)):
            if (i % 2 == 0 and scores[i] in ["A>>B", "A>B"]) or (i % 2 == 1 and scores[i] in ["A<<B", "A<B"]):
                win += 1
            elif (i % 2 == 0 and scores[i] in ["A<<B", "A<B"]) or (i % 2 == 1 and scores[i] in ["A>>B", "A>B"]):
                win -= 1
        return win

    def strict_score(scores):
        win = 0
        for i in range(len(scores)):
            if (i % 2 == 0 and scores[i] in ["A>>B"]) or (i % 2 == 1 and scores[i] in ["A<<B"]):
                win += 1
            elif (i % 2 == 0 and scores[i] in ["A<<B"]) or (i % 2 == 1 and scores[i] in ["A>>B"]):
                win -= 1
        return win
    win_num = 0
    tie_num = 0
    def loose_score(scores):
        win = 0
        for i in range(len(scores)):
            if i % 2 == 0:
                if scores[i] in ["A>>B", "B<<A"]:
                    win -= 2
                elif scores[i] in ["A>B", "B<A"]:
                    win -= 1
                elif scores[i] in ["A<<B", "B>>A"]:
                    win += 2
                elif scores[i] in ["A<B", "B>A"]:
                    win += 1
            else:
                if scores[i] in ["A<<B", "B>>A"]:
                    win -= 2
                elif scores[i] in ["A<B", "B>A"]:
                    win -= 1
                elif scores[i] in ["A>>B", "B<<A"]:
                    win += 2
                elif scores[i] in ["A>B", "B<A"]:
                    win += 1
        return win
    score = 0
    for obj in objs:
        scores = [g["score"] for g in obj["games"]]
        win = loose_score(scores)
        if win > 0:
            score += 2
            win_num += 1
        elif win == 0:
            score += 1
            tie_num += 1
        obj["if_win"] = 1.0 if win > 0 else 0.0
        obj["if_tie"] = 1.0 if win == 0 else 0.0

    score = float(score) / len(objs) / 2
    win_rate = win_num / float(len(objs))
    tie_rate = tie_num / float(len(objs))
    main_classified_scores, sub_classified_scores = calculate_classified_score(objs, tasktype_to_levels)
    return score, win_rate, tie_rate, main_classified_scores, sub_classified_scores

def main():
    args = parse_args()
    print(args)
    configs = make_config(args.setting_file)
    if configs["regex_pattern"]:
        configs["regex_pattern"] = re.compile(configs["regex_pattern"])
    if not args.evaluation_only:
        os.makedirs(os.path.dirname(args.output_path), exist_ok = True)
        objs, cached_objs = load_data(args.input_path, args.output_path)
        input_args ={
            "model_name": "response",
            "baseline_name": f"{args.baseline_name}_response",
            "reference": None,
            "configs": configs,
            "output_path": args.output_path
        }
        output_objs = utils.multi_tasks_from_objs(objs, workers = args.workers, task = start_judgements, chunk_size = 2, args = input_args)
        output_objs += list(cached_objs.values())
        os.makedirs(os.path.dirname(args.input_path), exist_ok = True)
        utils.write_jsonl_file(output_objs, args.output_path)
    if not args.judgement_only:
        objs = utils.safe_read_jsonl_file(args.output_path)
        tasktype_to_levels = json.load(open(args.mapping_file, "r"))
        score = get_scores(objs, tasktype_to_levels)
        results = {
            "score": score[0],
            "win_rate": score[1],
            "tie_rate": score[2],
            "model": objs[0]["model"] if "model" in objs[0] else None,
            "main_classified_win_rate": score[3],
            "main_classified_win_rate_latex": " & ".join([str(s) for s in list(score[3].values())] + [f"{format_score(score[1])}/{format_score(score[2])}"]),
            "sub_classified_win_rate": score[4],
            "sub_classified_win_rate_latex": " & ".join([str(s) for s in list(score[4].values())] + [f"{format_score(score[1])}/{format_score(score[2])}"])
        }
        print(results)
        utils.save_json(results, f"{args.output_path}.metric")

if __name__ == "__main__":
    main()
