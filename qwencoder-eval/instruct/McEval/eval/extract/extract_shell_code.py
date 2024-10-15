import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_shell_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Bb]ash)?.*?({entry_point}\s*\(\).*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"({entry_point}\s*\(\).*)(\n\n[a-zA-Z]}})", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Bb]ash)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)


    if (code[:2] == "sh"):
        code = code[2:]
    code += '\n'
    # pattern = r"\s*check\s*\(\s*\)\s*\{.*\}"
    # code = re.sub(pattern, "", code, flags=re.DOTALL)

    
    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Shell_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_shell_code(item['raw_generation'][0], item)
