import os
import re
import json

def extract_ts_code(
    text,
    item,
):
    signature_escaped = re.escape(item['signature'])
    code_block = re.search(
        rf"```(?:[Tt](?:ypescript|s))?.*?(const\s+{signature_escaped}.*?)```",
        text,
        flags=re.DOTALL,
    )
    if code_block is None:
        code_block = re.search(
            rf"(const\s+{signature_escaped}.*)", text, flags=re.DOTALL
        )
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Tt](?:ypescript|s))?(.*?)\n```", text, flags=re.DOTALL
        )
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)
        if "```" in code:
            code = code.split("```")[0]

    console_log_regex = re.compile(r"console\.log\(.*?\);", re.DOTALL)

    pattern = r"\s*function\s+check\w*\(\s*\)\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    pattern = r"\s*check\w*\(\s*\)\s*\;"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    # 使用正则表达式删除所有console.log语句
    code = console_log_regex.sub("", code)

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
            "eval/generations/gpt4/completions_TypeScript_humanevalsynthesize.jsonl"
        ).readlines()
        if x
    ]

    for item in [items[9]]:
        prt = extract_ts_code(item["raw_generation"][0], item)
        print('"' * 60)
        print(prt)
        # break
