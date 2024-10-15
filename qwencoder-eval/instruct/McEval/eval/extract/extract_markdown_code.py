import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_md_code(text) -> str:
    code_block = re.search(
        rf"```(?:markdown)(.*?)```", text, flags=re.DOTALL)
    
    if code_block is None:
        code_block = re.search(rf"```.*?\n(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        if ("\n\n" in text):
            return text.split("\n\n")[1].strip()
        return text.strip()
    else:
        # print("right!!!!")
        return code_block.group(1).strip()


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Markdown_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_md_code(item['raw_generation'][0])
