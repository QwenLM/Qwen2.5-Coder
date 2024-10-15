import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_fs_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Ff]sharp)?.*?((open)?.*let\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((open)?.*let\s+{entry_point}.*?)(\n\n[a-zA-Z])", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ff]sharp)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    if (code.find("[<EntryPoint>]") != -1):
        code = code[:code.find("[<EntryPoint>]")]
    # print(code)
    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_F#_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_fs_code(item['raw_generation'][0], item)
