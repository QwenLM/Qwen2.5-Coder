import os
import re
import json


def extract_lua_code(text, item):
    signature_escaped = re.escape(item["signature"])
    code_block = re.search(
        rf"```lua(.*?local\s+{signature_escaped}.*?|{signature_escaped}.*?)```",
        text,
        flags=re.DOTALL,
    )

    if code_block is None:
        code_block = re.search(rf"```lua(.*?)\n```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(.*?)```",
            text,
            flags=re.DOTALL,
        )
    if code_block is None:
        code_block = re.search(
            rf"(function\s+{item['entry_point']}.*end)",
            text,
            flags=re.DOTALL,
        )

    if code_block is None:
        code = text
    else:
        code = code_block.group(1)
        if "```" in code:
            code = code.split("```")[0]

    pattern = r"\-\-\[\[.*?\]\]\-\-"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    
    # Lua中打印使用print
    print_regex = re.compile(r"print\(.*?\)\s*\n", re.DOTALL)

    # 使用正则表达式删除所有print语句
    code = print_regex.sub("", code)

    pattern = r"function\s+check\s*\(.*?\).*end.*check\(.*\)"
    code = re.sub(pattern, "", code, flags=re.DOTALL)


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
            # "eval/generations/gpt4/completions_Lua_humanevalsynthesize.jsonl"
            "eval/generations/codellama-13b/gen_result_Lua.jsonl"
        ).readlines()
        if x
    ]

    for item in [items[9]]:
        prt = extract_lua_code(item["raw_generation"][0], item)
        print('"' * 60)
        print(prt)
        # break
