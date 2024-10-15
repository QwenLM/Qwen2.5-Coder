import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_perl_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Pp]erl)?.*?((use)?.*sub\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((use)?.*sub\s+{entry_point}.*?)(\n\n[a-zA-Z])", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Pp]erl)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)


    pattern = r"\s*sub\s+check\w*\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"check\s*\(.*?\);"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    
    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Perl_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_perl_code(item['raw_generation'][0], item)
