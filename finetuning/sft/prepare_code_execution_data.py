from pathlib import Path
import sys
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils import utils
from utils import code_execute_multiple
import tqdm
import re
import argparse
def pack_code(code, programming_language):
    code_lines = code.splitlines()
    for line in code_execute_multiple.IMPORT_HELPER[programming_language]:
        if line not in code_lines:
            code_lines.insert(0, line)
    code = "\n".join(code_lines)
    return code

def remove_irrelevant_code(code, entry_point):
    code = code.replace("\t", "    ") # blan
    code_lines = code.splitlines()
    new_code_lines = []
    skip_tag = False
    indent = 0
    for line in code_lines:
        if skip_tag and not line[indent:].startswith(" "):
            skip_tag = False
        if line.strip().startswith("def ") and not line.strip().startswith(f"def {entry_point}"):
            indent = len(line.split("def ")[0])
            skip_tag = True
        if not skip_tag:
            new_code_lines.append(line)
    code = "\n".join(new_code_lines)
    if "\ncheck_correctness()" not in code:
        code += "\n" + "check_correctness()"
    return code

def execute_code_task(objs, worker_id=0, workers=1, args = None):
    output_objs = []
    for obj in tqdm.tqdm(objs, position=worker_id, desc=f"Worker {worker_id}"):
        question = obj["messages"][1]["content"]
        answer = obj["gpt-4o_response"]
        unit_test = obj["gpt-4o_unittest"]
        answer_match = re.search(r"```.*?\n(.*?)```", answer, flags=re.DOTALL)
        unittest_match = re.search(r"```.*?\n(.*?)```", unit_test, flags=re.DOTALL)
        programming_language = obj["language"]
        if answer_match is not None and unittest_match is not None:
            unittest_code = unittest_match.group(1)
            unittest_code = remove_irrelevant_code(unittest_code, entry_point = "check_correctness")
            answer_code = answer_match.group(1)
            answer_code = pack_code(answer_code, programming_language)
            code = answer_code + "\n" + unittest_code
            if code_execute_multiple.check_correctness_multiple(code, programming_language):
                output_objs.append({
                    "question": question,
                    "answer": answer,
                    "answer_code": answer_code,
                    "unittest_code": unittest_code,
                    "unittest": unit_test
                })
    print(f"worker {worker_id} finished...")
    return output_objs

def parse_args():
    parser = argparse.ArgumentParser(description='Argument Parser Example')
    parser.add_argument('--input_path', '-input_path', type=str, default="python_evol.jsonl", help='Path to input file')
    parser.add_argument('--output_path', '-output_path', type=str, default="python_evol.jsonl.unittest", help='Path to output file')
    parser.add_argument('--workers', '-workers', type=int, default = 1, help='Path to output file')
    args = parser.parse_args()
    return args
    
def main():
    args = parse_args()
    objs = utils.read_jsonl_file(args.input_path)
    objs = utils.multi_tasks_from_objs(objs, workers = args.workers, task = execute_code_task, chunk_size=None, args = None)
    utils.write_jsonl_file(objs, args.output_path)


if __name__ == "__main__":
    main()
