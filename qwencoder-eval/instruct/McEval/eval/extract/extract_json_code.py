import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_json_code(text) -> str:
    code_block = re.search(
        rf"```(?:json)(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
        r"(\{.*\})", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
        rf"```(.*?)```", text, flags=re.DOTALL)

    if code_block is None:
        return text 
    else:
        return code_block.group(1)


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_JSON_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_json_code(item['raw_generation'][0])
