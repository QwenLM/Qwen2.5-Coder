import os
import re
import json


def extract_vimscript_code(text, item):
    signature_escaped = re.escape(item["signature"])
    entry_point = re.escape(item["entry_point"])
    # 假设 Vimscript 代码块被 ```vim 包围
    code_block = re.search(
        rf"```vim(?:script)*(.*?)```",
        text,
        flags=re.DOTALL,
    )
    if code_block is None:
        code_block = re.search(
            rf"```(.*?)```",
            text,
            flags=re.DOTALL,
        )
    if code_block is None:
        code_block = re.search(rf"({signature_escaped}.*|function.*{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        # 如果没有找到代码块，尝试匹配整个文本
        code = text
    else:
        # 如果找到了代码块，提取出代码部分
        code = code_block.group(1)

    print_regex = re.compile(r"print\(.*?\)?$", re.DOTALL)

    # 使用正则表达式删除所有print语句
    code = print_regex.sub("", code)

    # 提取提示（不包括签名行）和测试
    prompt = item["prompt"].split("\n")
    prompt = "\n".join(prompt[:-1])
    if item["signature"] in prompt:
        prompt = prompt.replace(item["signature"], "")
    full_code = prompt + "\n" + code + "\n" + item["test"]

    return full_code


if __name__ == "__main__":
    items = [
        json.loads(x)
        for x in open(
            "eval/generations/gpt4/completions_VimScript_humanevalsynthesize.jsonl"
        ).readlines()
        if x
    ]

    for item in [items[9]]:
        prt = extract_vimscript_code(item["raw_generation"][0], item)
        print('"' * 60)
        print(prt)
