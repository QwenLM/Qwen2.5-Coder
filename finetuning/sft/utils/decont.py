import jsonlines
import requests
import json
import argparse
import multiprocessing as mp
import traceback
import argparse
import tqdm
import time
import tempfile
from datasketch import MinHash, MinHashLSH
import subprocess
import collections
import numpy as np
import hashlib
from func_timeout import func_set_timeout
import pandas as pd
import os
import sys
import xlsxwriter
import itertools
import copy
import re
import numpy as np
import pandas as pd
import math
from sacrebleu import metrics
import ahocorasick
import datasets
import itertools
from pathlib import Path
from utils import utils

DATA_DIR = "./test_data/"


def has_n_gram_overlap(string1, string2, n_gram=10, if_tokenize=False):
    if if_tokenize:
        string1 = nltk.tokenize.word_tokenize(string1)
        string2 = nltk.tokenize.word_tokenize(string2)
        string1 = " ".join(string1)
        string2 = " ".join(string2)
    tokens1 = string1.split()
    tokens2 = string2.split()
    grams1 = set([" ".join(tokens1[i:i + n_gram]) for i in range(len(tokens1) - (n_gram - 1))])
    grams2 = set([" ".join(tokens2[i:i + n_gram]) for i in range(len(tokens2) - (n_gram - 1))])
    overlap = grams1.intersection(grams2)
    return len(overlap) > 0


def has_n_gram_overlap_with_testset(string1, testset, n_gram=10, if_tokenize=False, overlaps=[], verbose=False):
    if if_tokenize:
        string1 = nltk.tokenize.word_tokenize(string1)
        string1 = " ".join(string1)
    tokens1 = string1.split()
    grams1 = set([" ".join(tokens1[i:i + n_gram]) for i in range(len(tokens1) - (n_gram - 1))])
    overlap = grams1.intersection(testset)
    overlaps.extend(list(overlap))
    if len(overlap) > 0 and verbose:
        print(overlap)
    return len(overlap) > 0


def get_n_gram(string, n_gram=10, if_tokenize=False):
    if if_tokenize:
        string1 = nltk.tokenize.word_tokenize(string1)
        string1 = " ".join(string1)
    tokens1 = string.split()
    return set([" ".join(tokens1[i:i + n_gram]) for i in range(len(tokens1) - (n_gram - 1))])


def load_leetcode_test_data():
    data = utils.read_jsonl_file("livecodebench.jsonl")
    samples = []
    for obj in data:
        samples.append({"prompt": obj["prompt"]})
    return samples


def load_humanevalpack_test_data(data_path=f"{DATA_DIR}/humanevalpack"):
    ds1 = datasets.load_dataset(data_path, "python", trust_remote_code=True)["test"]
    ds2 = datasets.load_dataset(data_path, "js", trust_remote_code=True)["test"]
    ds3 = datasets.load_dataset(data_path, "java", trust_remote_code=True)["test"]
    ds4 = datasets.load_dataset(data_path, "go", trust_remote_code=True)["test"]
    ds5 = datasets.load_dataset(data_path, "cpp", trust_remote_code=True)["test"]
    ds6 = datasets.load_dataset(data_path, "rust", trust_remote_code=True)["test"]
    combined_dataset = datasets.concatenate_datasets([ds1, ds2, ds3, ds4, ds5, ds6])
    data = []
    for j, sample in enumerate(combined_dataset):
        data.append(sample)
    return data


def load_multiply_e():
    data = {}
    samples = []
    for lg in ["sh", "ts", "cs", "php", "java", "cpp", "js", "go", "rs"]:
        objs = utils.read_jsonl_file(f"{DATA_DIR}/multiple/data/humaneval-{lg}.jsonl")
        for j, sample in enumerate(objs):
            samples.append({"prompt": sample["prompt"]})
    return samples


def load_mbpp_test_data(data_path=f"{DATA_DIR}/mbpp/"):
    ds = utils.read_jsonl_file(f"{data_path}/mbpp.jsonl")
    data = []
    for j, sample in enumerate(ds):
        data.append(sample)
    return data


def load_ds1000_test_data(data_path="data/ds1000_data/"):

    def extract_ds_1000_prompt(prompt: str):
        if "SOLUTION START" in prompt:
            assert prompt.count("SOLUTION START") == 1
            return prompt.split("SOLUTION START")[0]
        elif "BEGIN SOLUTION" in prompt:
            assert prompt.count("BEGIN SOLUTION") == 1
            return prompt.split("BEGIN SOLUTION")[0]
        else:
            return prompt

    def load_ds_1000(data_path):
        data = []
        for prompt_file in Path(data_path).glob("*/Insertion/q*/prompt.txt"):
            with open(prompt_file) as f:
                data.append(extract_ds_1000_prompt({"insertion": f.read()}))
        return data

    return load_ds_1000(data_path)


def load_codeapex_data():
    ds = utils.read_jsonl_file("data/eval/eval_codeapex_v1.jsonl")
    data = []
    for j, sample in enumerate(ds):
        data.append(sample)
    return data


def get_testset_n_gram(n_gram=10, test_set=["mbpp", "multiple", "humanevalpack"]):
    print("Start Loading decont test set")
    mbpp_data = load_mbpp_test_data()
    humaneval_data = load_humanevalpack_test_data()
    multiply_e_data = load_multiply_e()
    ds1000_data = load_ds1000_test_data()
    codeapex_data = load_codeapex_data()
    #leetcode_data = load_leetcode_test_data()
    print("Successfully Loading decont test set")
    all_grams = set([])
    if "mbpp" in test_set:
        for obj in mbpp_data:
            n_grams = get_n_gram(obj["text"] + "\n" + obj["code"] + "\n".join(obj["test_list"]), n_gram=n_gram)
            all_grams.update(n_grams)
    if "humanevalpack" in test_set:
        for obj in humaneval_data:
            n_grams = get_n_gram(obj["instruction"] + obj["prompt"] + obj["canonical_solution"] + obj["test"], n_gram=n_gram)
            all_grams.update(n_grams)
    if "multiple" in test_set:
        for obj in multiply_e_data:
            n_grams = get_n_gram(obj["prompt"], n_gram=n_gram)
            all_grams.update(n_grams)
    if "ds1000" in test_set:
        for obj in ds1000_data:
            n_grams = get_n_gram(obj["insertion"], n_gram=n_gram)
            all_grams.update(n_grams)
    if "codeapex" in test_set:
        for obj in codeapex_data:
            n_grams = get_n_gram(obj["prompt"], n_gram=n_gram)
            all_grams.update(n_grams)
    # for obj in leetcode_data:
    #     n_grams = get_n_gram(obj["prompt"], n_gram = n_gram)
    #     all_grams.update(n_grams)
    return all_grams


def decontaminate_for_cpt(text, testset_n_gram, testset_func_names, n_gram=10, if_tokenize=False, verbose=False):
    """ 
    True denotes contamination
    """
    if has_n_gram_overlap_with_testset(text, testset_n_gram, n_gram=n_gram, if_tokenize=if_tokenize, verbose=verbose):
        return True
    if contain_func_name(text, testset_func_names):
        return True
    return False


def contain_func_name(text, testset_func_names):
    if f'{extract_func_name(text)}' in testset_func_names:
        return True
    else:
        return False


def extract_func_name(text):
    if re.search(r"def (.*?)\(().*?\)", text) is not None:
        return re.search(r"def (.*?)\(().*?\)", text).group(1).strip()
    if re.search(r"public \w+ \w+ (.*?)\(().*?\)", text) is not None:
        return re.search(r"public \w+ \w+ (.*?)\(().*?\)", text).group(1).strip()
    else:
        return None


def extract_class_name(text):
    if re.search(r"public\w+(\s+)\w*{", text) is not None:
        return re.search(r"def (.*?)\(().*?\)", text).group(1).strip()
    else:
        return None


def get_testset_func_name(datasets=["humaneval", "mbpp"]):
    test_func_names = set()
    if "humaneval" in datasets:
        humaneval_data = load_humanevalpack_test_data()
        test_func_names.update(set([obj["entry_point"] for obj in humaneval_data]))
    if "mbpp" in datasets:
        mbpp_data = load_mbpp_test_data()
        test_func_names.update(set([extract_func_name(obj["code"]) for obj in mbpp_data]))
    return test_func_names


def deduplicate_similar_strings(objs, num_perm=512, jaccard_threshold=0.8):
    """
    # # Example usage
    # strings = ["hello", "h3llo", "helloo", "world", "w0rld", "word", "whirled"]
    # deduplicated = deduplicate_similar_strings(strings, jaccard_threshold=0.8)
    # print(deduplicated)
    """
    # Create an LSH index with a given Jaccard similarity threshold
    lsh = MinHashLSH(threshold=jaccard_threshold, num_perm=num_perm)
    # Create MinHash objects for each string and add to the LSH index
    signatures = {}
    for i, obj in tqdm.tqdm(enumerate(objs)):
        minhash = MinHash(num_perm=num_perm)
        for word in obj["text"].split():
            minhash.update(word.encode('utf8'))
        lsh.insert(f'string_{i}', minhash)
        signatures[f'string_{i}'] = minhash
    unique_strings = []
    processed = set()
    for i, obj in enumerate(objs):
        key = f'string_{i}'
        if key in processed:
            continue
        similar_keys = lsh.query(signatures[key])
        for sim_key in similar_keys:
            processed.add(sim_key)
        unique_strings.append(obj)
    print(f"{len(objs)} -> {len(unique_strings)}")
    return unique_strings


def deduplicate_similar_strings_chatml(objs, num_perm=512, jaccard_threshold=0.6):
    """
    # # Example usage
    # strings = ["hello", "h3llo", "helloo", "world", "w0rld", "word", "whirled"]
    # deduplicated = deduplicate_similar_strings(strings, jaccard_threshold=0.8)
    # print(deduplicated)
    """
    # Create an LSH index with a given Jaccard similarity threshold
    lsh = MinHashLSH(threshold=jaccard_threshold, num_perm=num_perm)
    # Create MinHash objects for each string and add to the LSH index
    signatures = {}
    for i, obj in tqdm.tqdm(enumerate(objs)):
        minhash = MinHash(num_perm=num_perm)
        for word in (obj["messages"][1]["content"] + "\n" + obj["messages"][1]["content"]).split():
            minhash.update(word.encode('utf8'))
        lsh.insert(f'string_{i}', minhash)
        signatures[f'string_{i}'] = minhash
    unique_strings = []
    processed = set()
    for i, obj in enumerate(objs):
        key = f'string_{i}'
        if key in processed:
            continue
        similar_keys = lsh.query(signatures[key])
        for sim_key in similar_keys:
            processed.add(sim_key)
        unique_strings.append(obj)
    return unique_strings


def multi_tasks(objs, workers=64, path="data/system_role/log_gpt.jsonl", task=None, prompt_template=None, chunk_size=None, language=None):
    p = mp.Pool(workers)
    if chunk_size:
        results = []
        job_num = math.ceil(len(objs) / chunk_size)
        print(f"job num: {job_num}")
        for worker_id in range(job_num):
            results.append(p.apply_async(MPLogExceptions(task), args=(objs[worker_id * chunk_size:(worker_id + 1) * chunk_size], worker_id, workers, None, path, prompt_template, language)))
    else:
        chunk_size = math.ceil(len(objs) / float(workers))
        results = []
        for worker_id in range(workers):
            results.append(p.apply_async(MPLogExceptions(task), args=(objs[worker_id * chunk_size:(worker_id + 1) * chunk_size], worker_id, workers, None, path, prompt_template, language)))
    p.close()
    p.join()
    output_objs = []
    for result in results:
        output_objs.extend(result.get())
    return output_objs


if __name__ == "__main__":
    test_n_grams = get_testset_n_gram()
    objs = read_jsonl_file("./sft.jsonl")
    cnt = 0
    for obj in tqdm.tqdm(objs):
        overlaps = []
        dialog = "\n".join([obj["messages"][i]["content"] for i in range(1, len(obj["messages"]))])
        if has_n_gram_overlap_with_testset(obj["text"], test_n_grams, n_gram=10, if_tokenize=False, overlaps=overlaps):
            print(obj["text"])
            cnt += 1
    print(cnt)
