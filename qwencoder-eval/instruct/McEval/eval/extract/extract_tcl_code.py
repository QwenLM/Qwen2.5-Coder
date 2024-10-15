import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_tcl_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Tt]cl)?.*?(proc\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(proc\s+{entry_point}.*}})", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Tt]cl)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    
    pattern = r"\s*puts.*?\n"
    code = re.sub(pattern, "", code)


    return code + '\n\n' + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Tcl_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        print(extract_tcl_code(item['raw_generation'][0], item))
