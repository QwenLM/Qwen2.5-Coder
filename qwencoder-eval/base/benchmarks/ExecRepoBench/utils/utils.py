import jsonlines
import glob
import pandas as pd
import os
import math
import multiprocessing as mp
import traceback
import tqdm
import itertools
import re
import collections
import argparse
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
import tree_sitter_languages
import io
import importlib
from fuzzywuzzy import fuzz
language_symbols = {
    "python": {
        "CLASS_TYPE": ["class_definition"],
        "FUNCTION_TYPE": ["function_definition"],
        "IMPORT_TYPE": ["import_statement", "import_from_statement"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["attribute"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["assignment"],
        "COMMENT_TYPE": ["comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"]
    },
    "java": {
        "CLASS_TYPE": ["class_declaration"],
        "FUNCTION_TYPE": ["method_declaration"],
        "IMPORT_TYPE": ["import_declaration"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["field_access"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["local_variable_declaration", "field_declaration"],
        "COMMENT_TYPE": ["comment", "line_comment", "block_comment"],
        "IF_STATEMENT_TYPE": ["if_statement", "try_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement", "enhanced_for_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"]
    },
    "cpp": {
        "CLASS_TYPE": ["class_specifier"],
        "FUNCTION_TYPE": ["function_definition"],
        "TEMPLATE_DECLARATION_TYPE": ["template_declaration"],
        "IMPORT_TYPE": ["using_declaration", "namespace_definition", "preproc_include"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["field_expression", "method_invocation"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement", "declaration"],
        "ASSIGNMENT_STATEMENT_TYPE": ["declaration"],
        "COMMENT_TYPE": ["comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement", "range_based_for_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"],
        "STRUCT_DECLARATION_TYPE": ["struct_specifier"],
        "ENUM_DECLARATION_TYPE": ["enum_specifier"],
    },
    "c_sharp": {
        "CLASS_TYPE": ["class_declaration"],
        "FUNCTION_TYPE": ["method_declaration"],
        "IMPORT_TYPE": ["using_directive"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["simple_name", "qualified_name"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["local_declaration_statement"],
        "COMMENT_TYPE": ["single_line_comment", "multi_line_comment", "documentation_comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement", "foreach_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"]
    },  
    "typescript": {
        "CLASS_TYPE": ["class_declaration"],
        "FUNCTION_TYPE": ["function_declaration", "method_definition"],
        "IMPORT_TYPE": ["import_statement", "import_clause", "import_require_statement"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["property_access_expression"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["variable_declaration", "variable_statement"],
        "COMMENT_TYPE": ["comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement", "for_of_statement", "for_in_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"],
        "INTERFACE_DECLARATION_TYPE": ["interface_declaration"],
        "ENUM_DECLARATION_TYPE": ["enum_declaration"],
        "TYPE_ALIAS_DECLARATION_TYPE": ["type_alias_declaration"],
        "DECORATOR_TYPE": ["decorator"]
    },
    "javascript": {
        "CLASS_TYPE": ["class_declaration"],
        "FUNCTION_TYPE": ["function_declaration", "arrow_function"],
        "IMPORT_TYPE": ["import_statement", "export_statement"],
        "IDENTIFIER_TYPE": ["identifier"],
        "ATTRIBUTE_TYPE": ["member_expression"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["variable_declaration"],
        "COMMENT_TYPE": ["comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement", "for_in_statement", "for_of_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"],
        "OBJECT_DECLARATION_TYPE": ["object"],
        "ARRAY_DECLARATION_TYPE": ["array"],
        "TEMPLATE_STRING_TYPE": ["template_string"],
        "ASYNC_FUNCTION_DECLARATION_TYPE": ["async_function_declaration", "async_arrow_function"]
    },
    "php": {
        "CLASS_TYPE": ["class_declaration"],
        "FUNCTION_TYPE": ["function_definition"],
        "IMPORT_TYPE": ["use_declaration", "use_statement"],
        "IDENTIFIER_TYPE": ["name"],
        "ATTRIBUTE_TYPE": ["property_declaration"],
        "EXPRESSION_STATEMENT_TYPE": ["expression_statement"],
        "ASSIGNMENT_STATEMENT_TYPE": ["assignment_expression"],
        "COMMENT_TYPE": ["comment", "_comment"],
        "IF_STATEMENT_TYPE": ["if_statement"],
        "FOR_STATEMENT_TYPE": ["for_statement"],
        "WHILE_STATEMENT_TYPE": ["while_statement"],
        "RETURN_STATEMENT_TYPE": ["return_statement"]
    }
}

class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = self._compute_doc_lengths()
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths)
        self.idf_scores = self._compute_idf()

    def _compute_doc_lengths(self):
        return [len(doc) for doc in self.corpus]

    def _compute_idf(self):
        num_docs = len(self.corpus)
        idf_scores = {}

        for doc in self.corpus:
            for term in set(doc):
                idf_scores[term] = idf_scores.get(term, 0) + 1

        for term, freq in idf_scores.items():
            idf_scores[term] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)

        return idf_scores

    def _bm25_score(self, query, doc_index):
        doc = self.corpus[doc_index]
        score = 0
        doc_terms = collections.Counter(doc)
        for term in query:
            if term in doc_terms:
                tf = doc_terms[term]
                idf = self.idf_scores[term] if term in self.idf_scores else 0
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_lengths[doc_index] / self.avgdl)
                score += idf * tf * (self.k1 + 1) / denom 
        return score


    def get_scores(self, query):
        scores = {}
        for index in range(len(self.corpus)):
            scores[index] = self._bm25_score(query, index)
        return scores

    def get_similarity(self, doc_index):
        target_doc = self.corpus[doc_index]
        similarities = []
        for index in range(len(self.corpus)):
            if index != doc_index:
                similarity = self._bm25_score(target_doc, index)
                similarities.append(similarity)
        return similarities

def is_installed_package(module_name, project_root):
    try:
        module = importlib.import_module(module_name)
        module_path = getattr(module, '__file__', None)
        if module_path is None:
            return True
        module_path = Path(module_path).resolve()
        project_root = Path(project_root).resolve()
        return project_root in module_path.parents
    except:
        #print(f"Cannot import module {module_name}. It may not be installed or the name may be incorrect.")
        return False

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

def read_json_file(path):
    with open(path, "r") as r:
        objs = json.load(r)
    print(f"Successfully loading from {path}")
    return objs
    
def write_jsonl_file(objs, path, chunk_size = 1):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok = True)
    with jsonlines.open(path, "w", flush=True) as w:
        for i in tqdm.tqdm(range(0, len(objs), chunk_size)):
            try:
                w.write_all(objs[i: i + chunk_size])
            except:
                print(objs[i])
                exit()
    print(f"Successfully saving to {path}: {len(objs)}")

def get_avg_score(samples, key):
    return float(np.average([obj[key] for obj in samples]))

def copy_src_to_dest(src_dir, tgt_dir, cur):
    os.makedirs(tgt_dir, exist_ok=True)
    source_dir = f"{src_dir}/{cur}"
    target_dir = f"{tgt_dir}/{cur}"
    subprocess.run(["cp", "-r", source_dir, target_dir])


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

def save_json(data, file_name):
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Successfully saving to {file_name}")

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

def extract_code(text):
    if re.search(r"```(.*?)\n(.*?)```", text, flags=re.DOTALL) is not None:
        return re.search(r"```(.*?)\n(.*?)```", text, flags=re.DOTALL).group(2)
    else:
        return text

def extract_class_name(code):
    if re.search(r"public class\s+(\w*?)\s+{", code, flags=re.DOTALL) is not None:
        return re.search(r"class\s+(\w*?)\s+{", code, flags=re.DOTALL).group(1)
    else:
        return "Main"

# class BM25:
#     def __init__(self):
#         tokenized_corpus = [doc.lower().split() for doc in corpus]
#         bm25 = BM25Okapi(tokenized_corpus)

#     def search(query = "text analysis in python"):  
#         tokenized_query = word_tokenize(query.lower())
#         doc_scores = bm25.get_scores(tokenized_query)
#         best_docs = bm25.get_top_n(tokenized_query, corpus, n=3)
#         return best_docs

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


def remove_blank_line(code):
    code_lines = code.split("\n")
    code_lines = [c for c in code_lines if c.strip() != ""]
    code = "\n".join(code_lines)
    return code

def cal_edit_sim(references, hypotheses):
    total = len(references)
    edit_sim = 0.0
    for pred, gt in zip(hypotheses, references):
        pred = pred.strip()
        gt = gt.strip()
        edit_sim += fuzz.ratio(pred, gt)
    return edit_sim / total

def remove_comments(code, language = "python", remove_blank_line = True):
    if language == "python":
        code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', code, flags=re.DOTALL)
        #code = re.sub(r'#.*', '', code)
    elif language == "java":
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*', '', code)
    elif language == "cpp":
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*', '', code, flags=re.DOTALL)
        # 匹配除了新行符之外的任何单个字符，现在匹配包括行结束符在内的任何单个字符
        # 匹配单行注释 //...
        # (?<!http:|https:) 避免删除URL中的双斜线
        #code = re.sub(r'(?<!http:|https:)\/\/.*', '', code)
    if remove_blank_line:
        code_lines = code.split("\n")
        code_lines = [c for c in code_lines if c.strip() != ""]
        code = "\n".join(code_lines)
    return code

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

def safe_read_files(files):
    data = {}
    for f in files:
        try:
            data[f] = open(f, "r").read()
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
            print(f'Number of tokens after truncation is greater than max tokens allowed {max_num_tokens}: {new_len} {num_tokens}')
    return prompt

def get_definition_name(node, node_types):
    for child in node.children:
        if child.type == node_types["IDENTIFIER_TYPE"]:
            return child.text.decode("utf8")

def has_return_statement(node, node_types):
    traverse_nodes = traverse_tree(node)
    for node in traverse_nodes:
        if node.type == node_types["RETURN_TYPE"]:
            return True
    return False

def traverse_tree(node):
    cursor = node.walk()
    depth = 0

    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            if not cursor.goto_first_child():
                depth += 1
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent() or depth == 0:
            break
        else:
            depth -= 1


def extract_imports(code, language="python"):
    code_bytes = bytes(code, "utf8")
    parser = tree_sitter_languages.get_parser(language)
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    parser = tree_sitter_languages.get_parser(language)
    imports = []
    all_nodes = list(traverse_tree(root_node))
    for child in all_nodes:
        if child.type == 'import_statement':
            for imported_name in child.named_children:
                if imported_name.type == 'dotted_name':
                    module_name = imported_name.text.decode("utf-8")
                    imports.append(module_name)
        elif child.type == 'import_from_statement':
            module_name = []
            for sub_child in child.children:
                if sub_child.type == 'dotted_name':
                    module_name.append(sub_child.text.decode("utf-8"))
                elif sub_child.type == 'relative_import':
                    module_name.append(sub_child.text.decode("utf-8").replace(".", ""))
            if module_name:
                imports.extend(module_name)
    return imports

def get_relevance(obj, tokenizer, python_path="./miniconda3/envs/"):
    code = obj["prefix_code"] + obj["middle_code"] + obj["suffix_code"]
    all_imported_modules = extract_imports(code)
    imported_modules = []
    for m in all_imported_modules:
        if not is_installed_package(m, python_path):
            imported_modules.append(m)
    context_code_files = obj["context_code"]
    dependencies = np.array([0.0 for i in range(len(context_code_files))])
    for m in imported_modules:
        for index, file_name in enumerate(context_code_files):
            if f"{m}.py" in file_name:
                dependencies[index] += 1.0
    corpus = [tokenizer.tokenize(code)]
    for file_name in context_code_files:
        doc = tokenizer.tokenize(context_code_files[file_name])
        corpus.append(doc)
    bm25 = BM25(corpus)
    target_doc_index = 0
    similarities = bm25.get_similarity(target_doc_index)
    similarities = np.array(similarities) / np.sum(similarities)
    relevance = dependencies + similarities
    return relevance

