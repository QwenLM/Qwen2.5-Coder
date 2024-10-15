import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_powershell_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Pp]owershell)?.*?(function\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(function\s+{entry_point}.*}})", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Pp]owershell)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)
    # print(code)
    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_PowerShell_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_powershell_code(item['raw_generation'][0], item)
