import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_racket_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Rr]acket)?.*?((#lang racket)?.*?\(define \(\s*{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((#lang racket).*?\(define \(\s*{entry_point}.*?)(\n\n)", text, flags=re.DOTALL)
    # print(code_block)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Rr]acket)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Rr]acket)?(.*?)$", text, flags=re.DOTALL)
        
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)



    pattern = r"\(module\+\s+test.*?\n\)"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    if "#lang racket" not in code:
        code = "#lang racket\n(require rackunit)\n" + code
    # print(code)
    if "(require rackunit)" not in code:
        code = code.replace("#lang racket", "#lang racket\n(require rackunit)\n")


    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Racket_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_racket_code(item['raw_generation'][0], item)
