import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_vb_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = text
    code_block = re.search(
        rf"```(?:[Vv]b)?.*?(Function\s+{entry_point}.*?End Function).*?```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(Function\s+{entry_point}.*?End Function)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Vv]b)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        # print("error!!!!!!!!")
        code = text
    else:
        # print("right!!!!")
        code = code_block.group(1)
    code = "Module Module1\n" + code
    import_block = re.search(rf"Imports(.*?)\n", text, flags=re.DOTALL)
    if import_block is not None:
        code = "Imports" + import_block.group(1) + "\n" + code
    # print(code)
    return code + '\n\n' + item["test"]


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Visual Basic_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        print(extract_vb_code(item['raw_generation'][0], item))
