import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_haskell_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Hh]askell)?.*?((import)?.*?{entry_point} ::.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((import)?.*?{entry_point} ::.*?)(\n\n[a-zA-Z])", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Hh]askell)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    if (code.find("main :: IO ()") != -1):
        code = code[:code.find("main :: IO ()")]
    # print(code)
    return code.lstrip() + item["test"]


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Haskell_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_haskell_code(item['raw_generation'][0], item)
