import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_awk_code(text) -> str:
    code = text
    code_block = re.search(
        r"```(?:bash)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
        r"```(.*)```", text, flags=re.DOTALL)  
    if code_block is None:
        code = text.split('\n\n')[1]
    else:
        code = code_block.group(1)
    # print(code)
    if (code[:2] == "sh"):
        code = code[2:]
    return code.strip()


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_AWK_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        print(extract_awk_code(item['raw_generation'][0]))
