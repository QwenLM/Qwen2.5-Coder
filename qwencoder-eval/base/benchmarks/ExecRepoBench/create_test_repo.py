import glob
import os
import subprocess
import tree_sitter_languages
import copy
from utils import utils
import numpy as np
import tqdm
import tempfile
import collections
import transformers
import argparse
from pathlib import Path

def get_repo_data(repo_name):
    file_names = glob.glob(f"{repo_root_path}")
    for file_name in file_names:
        print(file_name)

def get_all_tests(repo_name = "dpath-python"):
    file_paths = glob.glob(f"{repo_root_path}/{repo_name}/tests/*.py")
    for file_path in file_paths:
        code = open(file_path, "r").read()
        get_all_functions(code)

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

def prepare_multi_level_completion(code, language = "python") -> str:
    code_bytes = bytes(code, "utf8")
    if language == "c-sharp":
        language = "c_sharp"
    parser = tree_sitter_languages.get_parser(language)
    tree = parser.parse(code_bytes)
    class_names = set()
    function_names = set()
    variable_names = set()
    root_node = tree.root_node
    all_nodes = list(traverse_tree(root_node))
    definition_nodes = []
    #nodes
    import_nodes = []
    comment_nodes = []
    return_statement_nodes = []
    if_statement_nodes = []
    for_statement_nodes = []
    while_statement_nodes = []
    class_nodes = []
    function_nodes = []
    assignment_nodes = []
    expression_nodes = []
    collected_nodes = []
    #
    node_types = utils.language_symbols[language]
    for child in all_nodes:
        if child.type in node_types["IMPORT_TYPE"]:
            import_nodes.append(child)
        elif child.type in node_types["COMMENT_TYPE"]:
            comment_nodes.append(child)
        elif child.type in node_types["IF_STATEMENT_TYPE"]:
            if_statement_nodes.append(child)
        elif child.type in node_types["FOR_STATEMENT_TYPE"]:
            for_statement_nodes.append(child)
        elif child.type in node_types["WHILE_STATEMENT_TYPE"]:
            while_statement_nodes.append(child)
        elif child.type in node_types["RETURN_STATEMENT_TYPE"]:
            return_statement_nodes.append(child)
        elif child.type in node_types["EXPRESSION_STATEMENT_TYPE"]:
            expression_nodes.append(child)
        elif child.type in node_types["ASSIGNMENT_STATEMENT_TYPE"]:
            assignment_nodes.append(child)
        elif child.type in node_types["CLASS_TYPE"]:
            name = get_definition_name(child, node_types)
            if not (
                name in class_names or name in variable_names or name in function_names
            ):
                definition_nodes.append((name, child))
                class_names.add(name)
                class_nodes.append(child)
        elif child.type in node_types["FUNCTION_TYPE"]:
            name = get_definition_name(child, node_types)
            if not (
                name in function_names or name in variable_names or name in class_names
            ):
                definition_nodes.append((name, child))
                function_names.add(get_definition_name(child, node_types))
                function_nodes.append(child)
        

    multi_level_nodes = [ 
        import_nodes, comment_nodes, return_statement_nodes, if_statement_nodes, for_statement_nodes, 
        while_statement_nodes, class_nodes, function_nodes, assignment_nodes, expression_nodes
    ]
    _sampling_ratio = {
        "IMPORT_TYPE": 0.1 if len(import_nodes) > 0 else 0,
        "COMMENT_TYPE": 0.05 if len(comment_nodes) > 0 else 0,
        "RETURN_STATEMENT_TYPE": 0.1 if len(return_statement_nodes) > 0 else 0,
        "IF_STATEMENT_TYPE": 0.15 if len(if_statement_nodes) > 0 else 0,
        "FOR_STATEMENT_TYPE": 0.15 if len(for_statement_nodes) > 0 else 0,
        "WHILE_STATEMENT_TYPE": 0.1 if len(while_statement_nodes) > 0 else 0,
        "CLASS_TYPE": 0.1 if len(class_nodes) > 0 else 0,
        "FUNCTION_TYPE": 0.1 if len(function_nodes) > 0 else 0,
        "ASSIGNMENT_STATEMENT_TYPE": 0.05 if len(assignment_nodes) > 0 else 0,
        "EXPRESSION_STATEMENT_TYPE": 0.05 if len(expression_nodes) > 0 else 0
    }
    sampling_ratio = np.array(list(_sampling_ratio.values()))
    if sampling_ratio.sum() == 0:
        return "", "", "", None
    sampling_ratio = sampling_ratio / np.sum(sampling_ratio)
    assert len(sampling_ratio) == len(multi_level_nodes)
    chosen_type_idx = np.random.choice(list(range(0, len(multi_level_nodes))), p = list(sampling_ratio), size = 1, replace = False)[0]
    chosen_type_nodes = multi_level_nodes[chosen_type_idx]
    #print(code)
    #
    masked_node = np.random.choice(chosen_type_nodes, size=1, replace=True)[0]
    all_parts_code = code_bytes[masked_node.start_byte : masked_node.end_byte].decode("utf-8")
    all_parts = list(traverse_tree(masked_node))
    max_line = 10
    if np.random.rand() < 0.8 and len(all_parts_code.split("\n")) < max_line and (masked_node.start_byte != 0 and masked_node.end_byte != len(code_bytes)):
        masked_part = masked_node
    else:
        masked_part = np.random.choice(all_parts, size=1, replace=True)[0]
        
    prefix = code_bytes[: masked_part.start_byte].decode("utf-8")
    middle = code_bytes[masked_part.start_byte : masked_part.end_byte].decode("utf-8")
    suffix = code_bytes[masked_part.end_byte :].decode("utf-8")
    node_type = masked_part.type
    return prefix, suffix, middle, node_type 


def create_prefix_suffix_code(code, random_lines_to_mask=False, random_spans_to_mask=False, grammar_based_mask=False, language="python", max_masked_line = 15, max_masked_char = 50):
    if code.strip() == "":
        return "", "", ""
    if random_lines_to_mask:
        code_lines = code.split("\n")
        try:
            start_line_index = np.random.randint(0, len(code_lines)) # [0, N - 1]
            end_line_index = np.random.randint(start_line_index + 1, start_line_index + 1 + max_masked_line)
        except:
            print(f"Error Index: {start_line_index} {end_line_index}")
        prefix_code = code_lines[:start_line_index]
        suffix_code = code_lines[end_line_index:]
        middle_code = code_lines[start_line_index: end_line_index]
        middle_code, prefix_code, suffix_code = "\n".join(middle_code), "\n".join(prefix_code), "\n".join(suffix_code)
        if prefix_code != "":
            prefix_code = prefix_code + "\n"
        if suffix_code != "":
            suffix_code = "\n" + suffix_code
    elif random_spans_to_mask:
        try:
            start_char_index = np.random.randint(0, len(code))
            end_char_index = np.random.randint(start_char_index + 1, start_char_index + 1 + max_masked_char) #[start, end)
        except:
            print(f"Error Index: {start_line_index} {end_line_index}")
        prefix_code = code[ :start_char_index]
        suffix_code = code[end_char_index: ]
        middle_code = code[start_char_index: end_char_index]
    elif grammar_based_mask:
        prefix_code, suffix_code, middle_code = code, entrypoint, language = "python"
    else:
        raise NotImplementedError("This function hasn't been implemented yet.")
    return prefix_code, suffix_code, middle_code

def create_samples(repo_root_path, all_repo_files, python_repo_files, repo_name):
    n_samples = 100
    test_data = []
    i = 0
    middle_code_set = set()
    while i < n_samples:
        masked_file = np.random.choice(list(python_repo_files.keys()), size=1).tolist()[0]
        code = python_repo_files[masked_file]
        #code = utils.remove_blank_line(code)
        #code = utils.remove_comments(code, language = "python", remove_blank_line = True)
        context_code = {}
        for file_name in python_repo_files:
            if file_name != masked_file:
                new_file_name = file_name.replace(repo_root_path, "")
                context_code[new_file_name] = python_repo_files[file_name]
        if i < 3: #single Line
            prefix_code, suffix_code, middle_code = create_prefix_suffix_code(code = code, random_lines_to_mask = True, max_masked_line=1)
            if len(middle_code.split("\n")) != 1:
                continue
            type = "Random Single-line Completion"
        elif i < 6: #Multi Line
            prefix_code, suffix_code, middle_code = create_prefix_suffix_code(code = code, random_lines_to_mask = True, max_masked_line = 10)
            type = "Random Multi-line Completion"
        elif i < 9: #Span
            prefix_code, suffix_code, middle_code = create_prefix_suffix_code(code = code, random_spans_to_mask = True, max_masked_char = 30)
            type = "Random Span Completion"
        else: #Grammar-based
            prefix_code, suffix_code, middle_code, node_type = prepare_multi_level_completion(code, language = "python")
            NODE_TYPE2LEVEL = {
                "class_definition": "block",
                "function_definition": "block",
                "=": "expression",
                "import_from_statement": "statement",
                "import_statement": "statement",
                "identifier": "expression",
                "attribute": "expression",
                "expression_statement": "expression",
                "assignment": "expression",
                "comment": "statment",
                "if_statement": "block",
                "for_statement": "block",
                "while_statement": "block",
                "return_statement": "statement"
            }
            if node_type not in NODE_TYPE2LEVEL:
                node_level = "expression"
            else:
                node_level = NODE_TYPE2LEVEL[node_type]
            type = f"grammar-based: {node_level}"
        if len(middle_code.strip()) <= 10 or len(middle_code.strip()) >= 512 or middle_code.strip() in middle_code_set or "#" in middle_code:
            continue
        created_sample = {
            "repo_name": repo_name,
            "file_name": masked_file.replace(repo_root_path, ""),
            "prefix_code": prefix_code,
            "suffix_code": suffix_code,
            "middle_code": middle_code,
            "context_code": context_code,
            "fill_type": type
        }
        #sort relevance
        relevance = utils.get_relevance(created_sample, tokenizer, "./miniconda3/envs")
        sorted_context_code_files = list(created_sample["context_code"].items())
        sorted_index = np.argsort(relevance)
        sorted_context_code_files = [sorted_context_code_files[index] for index in sorted_index][::-1]
        created_sample["context_code"] = sorted_context_code_files
        #
        test_data.append(created_sample)
        middle_code_set.add(middle_code.strip())
        i += 1
    return test_data



def prepare_test_repo_data(tokenizer, repo_root_path, testset_path):
    def is_valid_file(file_name):
        if "tests/" in file_name or "test/" in file_name:
            return False
        elif "evaluate_repo.py" in file_name:
            return False
        elif "setup.py" in file_name:
            return False
        elif "docs/" in file_name:
            return False
        elif "build/" in file_name:
            return False
        return True
    repo_names = os.listdir(repo_root_path)
    repo_names.sort()
    data = []
    for repo_name in tqdm.tqdm(repo_names):
        if repo_name == "build" or repo_name.startswith("."):
            continue
        repo_file_names = glob.glob(f"{repo_root_path}/{repo_name}/**/*", recursive=True)
        all_repo_file_names = [f for f in repo_file_names if os.path.isfile(f)]
        python_file_names = [f for f in repo_file_names if os.path.isfile(f) and f.endswith(".py") and is_valid_file(f)]
        print(f"Loading repo files from {repo_name}...")
        python_repo_files = utils.safe_read_files(python_file_names) 
        print(f"Successfully Loading all python files {repo_name}")
        samples = create_samples(repo_root_path, python_repo_files, python_repo_files, repo_name)
        data.extend(samples)
        print(f"==========================Complete creating f{repo_name} samples==========================")
    statistics_data = collections.defaultdict(int)
    for obj in data:
        statistics_data[obj["fill_type"]] += 1
    print(statistics_data)
    utils.write_jsonl_file(data, testset_path)


def prepare_test_repo_environment(repo_root_path, conda_dir, env_dir):
    repo_names = os.listdir(repo_root_path)
    repo_names.sort()
    for repo_name in repo_names:
        if repo_name == "build" or repo_name.startswith("."):
            continue
        print(f"==========================Creating {repo_name} test samples...=======================================")
        os.environ["PATH"] = f"{conda_dir}/bin:" + os.environ["PATH"]
        print(f"==========================Conda repo_{repo_name} Setup...=======================================")
        if not os.path.exists(f"{env_dir}/envs/repo_{repo_name}"):
            subprocess.run(f"conda create -p {env_dir}/envs/repo_{repo_name} python=3.9 -y", shell=True)
        os.environ["PATH"] = f"{env_dir}/envs/repo_{repo_name}/bin:" + os.environ["PATH"]
        if os.path.exists(f"{repo_root_path}/{repo_name}/requirements.txt"):
            subprocess.run(f"cd {repo_root_path}/{repo_name}; pip install -r requirements.txt", shell=True)
        # if os.path.exists(f"{repo_root_path}/{repo_name}/setup.py"):
        #     subprocess.run(f"cd {repo_root_path}/{repo_name}; python setup.py install", shell=True)  
        subprocess.run(f"cd {repo_root_path}/{repo_name}; pip install -e .", shell=True)
        subprocess.run(f"pip install install pytest pytest-cov pytest-benchmark coincidence cssutils docutils openpyxl hypothesis pycodestyle", shell=True)  
        print(f"==========================Successfully install environment {repo_name}==========================")

def evaluate_correctness(obj, env_dir, repo_root_path):
    repo_name = obj["repo_name"]
    masked_file = obj["file_name"]
    prefix_code = obj["prefix_code"]
    middle_code = obj["generated_middle_code"] if "generated_middle_code" in obj else obj["middle_code"]
    suffix_code = obj["suffix_code"]
    code = prefix_code + middle_code + suffix_code
    with tempfile.TemporaryDirectory() as executable_repo_root_path:
        utils.copy_src_to_dest(repo_root_path, executable_repo_root_path, repo_name)
        masked_file = f"{executable_repo_root_path}/{masked_file}"
        with open(masked_file, "w") as w:
            w.write(code)
        #print(f"Executing {repo_name} ({masked_file})")
        os.environ["PATH"] = f"{env_dir}/envs/repo_{repo_name}/bin:" + os.environ["PATH"]
        os.chdir(os.path.join(executable_repo_root_path, repo_name))
        timeout_seconds = 120
        try:
            results = subprocess.run(f"python evaluate_repo.py", shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout = timeout_seconds) #f"{executable_repo_root_path}/{repo_name}"
        except subprocess.TimeoutExpired as e:
            return 0.0, f"timeout: {timeout_seconds}s"
        if results.returncode != 0:
            return 0.0, results.stderr.decode()
    return 1.0, ""

def evaluate_objs_correctness(objs, worker_id, workers, args):
    env_dir = args["env_dir"]
    repo_root_path = args["repo_root_path"]
    for obj in tqdm.tqdm(objs, position=worker_id, desc=f"Worker {worker_id}/{workers}"):
        is_pass, stderr = evaluate_correctness(obj, env_dir = env_dir, repo_root_path = repo_root_path)
        obj["is_pass"] = is_pass
        obj["stderr"] = stderr
    return objs


def evaluate_all_correctness(workers = 1, chunk_size = 10, conda_dir = "", env_dir = "", repo_root_path = "", output_path = ""):
    objs = utils.read_jsonl_file(f"{Path(__file__).resolve().parent}/test_set/test.jsonl")
    objs = utils.multi_tasks_from_objs(objs, workers = workers, task = evaluate_objs_correctness, chunk_size = chunk_size, args = {"conda_dir": conda_dir, "env_dir": env_dir, "repo_root_path": repo_root_path})
    pass_at_1 = [obj["is_pass"] for obj in objs]
    pass_at_1 = np.average(pass_at_1) * 100
    pass_at_1 = round(pass_at_1, 1)
    save_objs = [{
            "repo_name": obj["repo_name"],
            "file_name": obj["file_name"],
            "is_pass": obj["is_pass"],
            "srderr": obj["stderr"]
        } 
        for obj in objs
    ]
    utils.write_jsonl_file(save_objs, output_path)
    print(f"pass@1: {pass_at_1}")

def output_environs(repo_root_path, env_dir):
    repo_names = os.listdir(repo_root_path)
    repo_names.sort()
    os.makedirs(f"{env_dir}/repo_requirements/", exist_ok = True)
    for repo_name in tqdm.tqdm(repo_names):
        if repo_name == "build" or repo_name.startswith("."):
            continue
        if not os.path.exists(f"{env_dir}/envs/repo_{repo_name}"):
            os.environ["PATH"] = f"{env_dir}/envs/repo_{repo_name}/bin:" + os.environ["PATH"]
            subprocess.run(f"pip freeze > {env_dir}/repo_requirements/requirements_{repo_name}.txt", shell=True)
    print(f"==========================Successfully output environments to {env_dir}/repo_requirements/ ==========================")


def parse_args():
    parser = argparse.ArgumentParser(description="Argument Parser Example")
    parser.add_argument("--repo_root_path", "-repo_root_path", type=str, default="./repos/", help="Path to output file")
    parser.add_argument("--conda_dir", "-conda_dir", type=str, default="./miniconda3/", help="Path to output file")
    parser.add_argument("--env_dir", "-env_dir", type=str, default="./envs/", help="Path to output file")
    parser.add_argument("--tokenizer_path", "-tokenizer_path", type=str, default="./pretrained_models/Qwen/Qwen2.5-Coder-1.5B", help="Path to output file")
    parser.add_argument("--action", "-action", type=str, default="verify_all_repo_correctness", help="Path to output file")
    parser.add_argument("--eval_workers", "-eval_workers", type=int, default=1, help="Path to output file")
    parser.add_argument("--testset_path", "-testset_path", type=str, default="./exec_repo_bench.jsonl", help="Path to output file")
    parser.add_argument("--output_path", "-output_path", type=str, default="./results/verify.jsonl", help="Path to output file")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    np.random.seed(1)
    if args.action == "prepare_environments":
        prepare_test_repo_environment(repo_root_path = args.repo_root_path, conda_dir = args.conda_dir, env_dir = args.env_dir)
    elif args.action == "prepare_repo_test_data":
        tokenizer = transformers.AutoTokenizer.from_pretrained(args.tokenizer_path, trust_remote_code = True)
        prepare_test_repo_data(tokenizer = tokenizer, repo_root_path = args.repo_root_path, testset_path = args.testset_path)
    elif args.action == "verify_all_repo_correctness":
        evaluate_all_correctness(workers = args.eval_workers, chunk_size = 20, conda_dir = args.conda_dir, env_dir = args.env_dir, repo_root_path = args.repo_root_path, output_path = args.output_path)
    elif args.action == "output_environments":
        output_environs(repo_root_path = args.repo_root_path, env_dir = args.env_dir)
