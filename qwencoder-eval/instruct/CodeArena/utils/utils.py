import jsonlines
import pandas as pd
import os
import math
import requests
import multiprocessing as mp
import traceback
import tqdm
import itertools
import re
from pathlib import Path
import json
import numpy as np
import itertools
import gc
import glob
import subprocess
import hashlib
import random
import string
import time
import openai


def call_gpt4o(messages, api_key, model="gpt-4o", temperature=0.2, max_tokens=16384):
    openai.api_key = api_key    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return str(e)

##########
#from rank_bm25 import BM25Okapi
class MPLogExceptions(object):
    def __init__(self, callable):
        self.__callable = callable

    def error(msg, *args):
        return mp.get_logger().error(msg, *args) 

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)

        except Exception as e:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            self.error(traceback.format_exc())
            # Re-raise the original exception so the Pool worker can``
            # clean up
            raise

        # It was fine, give a normal answer
        return result

def read_file_from_position(args):
    filename, start_position, end_position, worker_id = args
    objs = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        current_position = find_next_line(f, start_position)
        f.seek(current_position)
        if current_position >= end_position:
            print(f"worker_id {worker_id} completed")
            return objs
        for cnt in tqdm.tqdm(itertools.count(), position=worker_id, desc=f"worker_id: {worker_id}"):
            line = f.readline()  
            if not line:
                break
            obj = json.loads(line)
            objs.append(obj)
            if f.tell() >= end_position:
                break
    print(f"worker_id {worker_id} completed")
    return objs

def find_next_line(f, position):
    if position == 0:
        return position
    f.seek(position)
    f.readline()
    position = f.tell()
    return position

def multi_tasks_from_objs(objs, workers = 64, task=None, chunk_size=None, args=None):
    p = mp.Pool(workers)
    if chunk_size:
        results = []
        job_num = math.ceil(len(objs) / chunk_size)
        print(f"job num: {job_num}")
        for worker_id in range(job_num):
            results.append(p.apply_async(MPLogExceptions(task), args=(objs[worker_id * chunk_size: (worker_id + 1) * chunk_size], worker_id, workers, args)))
    else:
        chunk_size = math.ceil(len(objs) / float(workers))
        results = []
        for worker_id in range(workers):
            results.append(p.apply_async(MPLogExceptions(task), args=(objs[worker_id * chunk_size: (worker_id + 1) * chunk_size], worker_id, workers, args)))
    p.close()
    p.join()
    output_objs = []
    for result in results:
        output_objs.extend(result.get())
    return output_objs

def multi_tasks_from_file(file_name = 'example.txt', workers = 16, chunk_size = None, task = None):    
    file_size = os.path.getsize(file_name)
    print(f"The size of {file_name} is: {file_size} bytes")
    if chunk_size:
        assert chunk_size > 0
        job_num = math.ceil(float(file_size) / chunk_size)
        positions = [chunk_size * i for i in range(job_num)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(job_num)]
        print(f"job num: {job_num}")
    else:
        chunk_size = math.ceil(float(file_size) / workers)
        positions = [chunk_size * i for i in range(workers)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(workers)]
    p = mp.Pool(workers)
    results = []
    for pos in start_positions:
        results.append(p.apply_async(MPLogExceptions(task), args=(pos,)))
    p.close()
    p.join()
    output_objs = []
    for result in results:
        output_objs.extend(result.get())
    print(f"Successfully Loading from {file_name}: {len(output_objs)} samples")
    return output_objs


def multi_read(file_name = 'example.txt', workers = 32, chunk_size = None):    
    file_size = os.path.getsize(file_name)
    print(f"The size of {file_name} is: {file_size} bytes")
    if chunk_size:
        assert chunk_size > 0
        job_num = math.ceil(float(file_size) / chunk_size)
        positions = [chunk_size * i for i in range(job_num)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(job_num)]
        print(f"job num: {job_num}")
    else:
        chunk_size = math.ceil(float(file_size) / workers)
        positions = [chunk_size * i for i in range(workers)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(workers)]
    p = mp.Pool(workers)
    results = []
    for pos in start_positions:
        results.append(p.apply_async(MPLogExceptions(read_file_from_position), args=(pos,)))
    p.close()
    p.join()
    output_objs = []
    for result in results:
        output_objs.extend(result.get())
    print(f"Successfully Loading from {file_name}: {len(output_objs)} samples")
    return output_objs

def filter_code(text):
    def calculate_metrics(text):
        NON_ALPHA = re.compile("[^A-Za-z_0-9]")
        lines = text.strip().split('\n')
        line_lengths = [len(line) for line in lines]
        if len(lines) > 0:
            avg_line_length = sum(line_lengths) / len(lines)
            max_line_length = max(line_lengths)
        else:
            avg_line_length = 0
            max_line_length = 0
        alphanum_count = sum(c.isalnum() for c in text)
        alpha_count = sum(c.isalpha() for c in text)
        if len(text) > 0:
            alphanum_fraction = alphanum_count / len(text)
            alpha_fraction = alpha_count / len(text)
        else:
            alphanum_fraction = 0
            alpha_fraction = 0
        alpha_len = len(NON_ALPHA.split(text))
        char_len = len(text)
        tokens_num = len(text.split())
        return char_len, alpha_len, avg_line_length, max_line_length, alphanum_fraction, alpha_fraction, tokens_num
    char_len, alpha_len, avg_line_length, max_line_length, alphanum_fraction, alpha_fraction, tokens_num = calculate_metrics(text)
    if (1 < avg_line_length < 50) and (1 < max_line_length < 100) and (0.1 < alphanum_fraction < 1.0) and (0.1 < alpha_fraction < 1.0) and (10 < tokens_num < 1024):
        return False
    else:
        return True
    

def read_file_from_position_with_filter(args):
    filename, start_position, end_position, worker_id = args
    objs = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        current_position = find_next_line(f, start_position)
        f.seek(current_position)
        if current_position >= end_position:
            print(f"worker_id {worker_id} completed")
            return objs
        for cnt in tqdm.tqdm(itertools.count(), position=worker_id, desc=f"worker_id: {worker_id}"):
            line = f.readline()  
            if not line:
                break
            obj = json.loads(line)
            #if not filter_code(obj["text"]):
            objs.append(obj)
            if f.tell() >= end_position:
                break
    print(f"worker_id {worker_id} completed")
    return objs

def multi_read_with_filter(file_name = 'example.txt', workers = 32, chunk_size = None):    
    file_size = os.path.getsize(file_name)
    print(f"The size of {file_name} is: {file_size} bytes")
    if chunk_size:
        assert chunk_size > 0
        job_num = math.ceil(float(file_size) / chunk_size)
        positions = [chunk_size * i for i in range(job_num)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(job_num)]
        print(f"job num: {job_num}")
    else:
        chunk_size = math.ceil(float(file_size) / workers)
        positions = [chunk_size * i for i in range(workers)]
        start_positions = [(file_name, positions[i], positions[i] + chunk_size, i) for i in range(workers)]
    p = mp.Pool(workers)
    results = []
    for pos in start_positions:
        results.append(p.apply_async(MPLogExceptions(read_file_from_position_with_filter), args=(pos,)))
    p.close()
    p.join()
    output_objs = []
    for result in results:
        output_objs.extend(result.get())
    print(f"Successfully Loading from {file_name}: {len(output_objs)} samples")
    return output_objs

def read_jsonl_file(file_name, max_sentence=None):
    data = []
    with jsonlines.open(file_name, "r") as r:
        for i, obj in tqdm.tqdm(enumerate(r)):
            if max_sentence is not None and i >= max_sentence:
                return data
            data.append(obj)
    return data

def safe_read_jsonl_file(file_name, max_sentence=None):
    data = []
    with open(file_name, "r", encoding="utf-8", errors="ignore") as r:
        for i, line in tqdm.tqdm(enumerate(r)):
            try:
                obj = json.loads(line)
                if max_sentence is not None and i >= max_sentence:
                    return data
                data.append(obj)
            except:
                continue
    return data


def truncate_prompt(prompt, max_num_tokens, tokenizer, side="right"):
    tokens = tokenizer.tokenize(prompt)
    num_tokens = len(tokens)
    if num_tokens > max_num_tokens:
        if side == 'left':
            prompt_tokens = tokens[num_tokens - max_num_tokens:]
        elif side == 'right':
            prompt_tokens = tokens[:max_num_tokens]
        prompt = tokenizer.convert_tokens_to_string(prompt_tokens)
        new_len = len(tokenizer.tokenize(prompt))
        if new_len > max_num_tokens:
            print(f'Number of tokens after truncation is greater than max tokens allowed: {new_len=} {num_tokens=}')
    return prompt

def read_json_file(path):
    with open(path, "r") as r:
        objs = json.load(r)
    print(f"Successfully loading from {path}")
    return objs


def write_jsonl_file(objs, path, chunk_size = 1):
    os.makedirs(os.path.dirname(path), exist_ok = True)
    with jsonlines.open(path, "w", flush=True) as w:
        for i in tqdm.tqdm(range(0, len(objs), chunk_size)):
            w.write_all(objs[i: i + chunk_size])
    print(f"Successfully saving to {path}: {len(objs)}")

def save_json(data, filename, indent = 4) -> None:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    print(f"Successfully saving to {filename}")

def read_jsonl_file(file_name, max_sentence=None):
    data = []
    with jsonlines.open(file_name, "r") as r:
        for i, obj in tqdm.tqdm(enumerate(r)):
            if max_sentence is not None and i >= max_sentence:
                return data
            data.append(obj)
    return data

def sentence_jaccard_similarity(sentence1, sentence2):
    def tokenize(sentence):
        """
        Tokenize the input sentence into a set of words.
        """
        # Convert to lowercase and split the sentence into words
        words = re.findall(r'\b\w+\b', sentence.lower())
        # Return the set of words
        return set(words)
    """
    Calculate the Jaccard Similarity between two sentences.
    """
    # Tokenize the sentences into sets of words
    set1 = tokenize(sentence1)
    set2 = tokenize(sentence2)
    # Calculate intersection and union
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    # Compute Jaccard Similarity
    similarity = len(intersection) / len(union)
    return similarity

def read_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def multi_write_jsonl_file(objs, path, workers = 16):
    chunk_size = math.ceil(len(objs) / workers)
    positions = [chunk_size * i for i in range(workers)]
    start_positions = [(objs[positions[i]: positions[i] + chunk_size], f"{path}-worker{i}.jsonl") for i in range(workers)]
    p = mp.Pool(workers)
    results = []
    for pos in start_positions:
        results.append(p.apply_async(MPLogExceptions(write_jsonl_file), args=(pos[0], pos[1])))
    p.close()
    p.join()
    p1 = subprocess.Popen(f"ls {path}-worker*.jsonl | sort -V | xargs cat > {path}", shell=True)
    p1.wait()
    print(f"Start merging to {path}")
    p2 = subprocess.Popen(f"rm {path}-worker*.jsonl", shell=True)
    print(f"Successfully Saving to {path}")

def extract_class_name(code):
    if re.search(r"public class\s+(\w*?)\s+{", code, flags=re.DOTALL) is not None:
        return re.search(r"class\s+(\w*?)\s+{", code, flags=re.DOTALL).group(1)
    else:
        return "Main"

class BM25:
    def __init__(self):
        tokenized_corpus = [doc.lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)

    def search(query = "text analysis in python"):  
        tokenized_query = word_tokenize(query.lower())
        doc_scores = bm25.get_scores(tokenized_query)
        best_docs = bm25.get_top_n(tokenized_query, corpus, n=3)
        return best_docs

def minihash_deduplicate(data):
    hash_set = set()
    deduped_data = []
    for item in tqdm.tqdm(data):
        hash_value = hashlib.md5(item["text"].encode()).hexdigest()
        if hash_value not in hash_set:
            deduped_data.append(item)
            hash_set.add(hash_value)
    return deduped_data

def contain_chinese(string):
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def remove_comments(code, language = "python"):
    if language == "python":
        code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', code, flags=re.DOTALL)
        code = re.sub(r'#.*', '', code)
        return code
    elif language == "java":
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*', '', code)
        return code
    elif language == "cpp":
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*', '', code, flags=re.DOTALL)
        # 匹配除了新行符之外的任何单个字符，现在匹配包括行结束符在内的任何单个字符
        # 匹配单行注释 //...
        # (?<!http:|https:) 避免删除URL中的双斜线
        #code = re.sub(r'(?<!http:|https:)\/\/.*', '', code)
    return code

def remove_illegal_chars(text):
    # 删除非中英文字符和标点符号
    legal_chars = string.ascii_letters + string.digits + string.punctuation + ''.join([chr(i) for i in range(ord('一'), ord('龥')+1)])
    pattern = r'[^%s]' % re.escape(''.join(legal_chars))
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def jsonl_to_excel(jsonl_file_path, excel_file_path, keys = None):
    data_list = []
    with open(jsonl_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            if isinstance(keys, list):
                #data = {k: remove_illegal_chars(data[k]) for k in keys}
                data = {k: data[k] for k in keys}
            data_list.append(data)
    df = pd.DataFrame(data_list)
    df.to_excel(excel_file_path, index=False, engine="xlsxwriter")
    print(f"Data has been successfully saved to {excel_file_path}")
