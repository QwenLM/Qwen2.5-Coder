import re
import json



def extract_swift_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Ss]wift)?.*?((import.*?\n)*?func\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"((import.*)?func\s+{entry_point}.*?)(\n\n[a-zA-Z])", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ss]wift)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    
    pattern = r"func\s+check\w*\s*\(.*?\)\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"\s+check\w*\s*\(.*?\)"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    return code + '\n\n'+item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Swift_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_swift_code(item['raw_generation'][0], item)
