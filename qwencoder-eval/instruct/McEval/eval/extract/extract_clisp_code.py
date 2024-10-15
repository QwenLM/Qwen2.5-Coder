import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_clisp_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = ""
    code_block = re.search(
        rf"```(?:[Ll]isp)?.*?(\(defun\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(\(defun\s+{entry_point}.*?)(\n\n)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Li]ip)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)

    eql = 0
    for ch in code:
        if ch == '(':
            eql+=1
        elif ch == ')':
            eql-=1
    code += ')'* eql
    return code + '\n\n' + item["test"]


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Common Lisp_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_clisp_code(item['raw_generation'][0], item)
