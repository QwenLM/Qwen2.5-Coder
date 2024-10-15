import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_html_code(text) -> str:
    code_block = re.search(
        r"```(?:html)?.*?<body>(.*?)</body>.*?```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:html)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        return text
    else:
        # print("right!!!!")
        return code_block.group(1).strip()


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_HTML_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_html_code(item['raw_generation'][0])
