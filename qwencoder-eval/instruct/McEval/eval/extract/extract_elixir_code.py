import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_elixir_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Ee]lixir)?.*?(def\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(def\s+{entry_point}.*end)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ee]lixir)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)


    defmodule_block = re.search(
        rf".*defmodule.*", text, flags=re.DOTALL)
    
    pattern = r"\s*IO\..*?\n"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    
    pattern = r"defmodule.*?Test\s+do.*end"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    if defmodule_block is None:
        code = item['prompt'].split('\n')[0] + '\n' + code + '\nend\n'
    else:
        code = item['prompt'].split('\n')[0] + '\n' + code + '\n'
    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Elixir_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_elixir_code(item['raw_generation'][0], item)
