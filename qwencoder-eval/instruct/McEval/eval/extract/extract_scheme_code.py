import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_scheme_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Ss]cheme)?.*?((#lang racket)?.*?\(define \(\s*{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((#lang racket)?.*?\(define \(\s*{entry_point}.*?)(\n\n)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ss]cheme)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    
    if "#lang racket" not in code:
        code = "#lang racket\n(require rackunit)\n" + code
    
    eql = 0
    for ch in code:
        if ch == '(':
            eql+=1
        elif ch == ')':
            eql-=1
    code += '\n)'* eql

    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Scheme_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_scheme_code(item['raw_generation'][0], item)
