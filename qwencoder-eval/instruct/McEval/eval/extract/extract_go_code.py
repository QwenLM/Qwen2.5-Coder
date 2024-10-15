import os
import re
import json

# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

IMPORT_HELPER = {
    "go": [
        "math",
        "strings",
        "fmt",
        "strconv",
        "time",
        "bytes",
        "regexp",
        "sort",
        "math/rand",
        "math/big",
        "crypto/md5",
        "unicode",
    ],
}


def extract_go_code(text, item):
    entry_point = re.escape(item["entry_point"])
    signature_escaped = re.escape(item["signature"])
    dot = re.escape("}")
    code_block = re.search(
        rf"```(?:[Gg]o)?.*?(func\s+{entry_point}.*?)```", text, flags=re.DOTALL
    )
    if code_block is None:
        code_block = re.search(rf"(func\s+{entry_point}.*{dot}|{signature_escaped}.*{dot})", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Gg]o)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)
        if "```" in code:
            code = code.split("```")[0]

    if "func main" in code:
        main_regex = re.compile(r"func main\(.*?\)?$", re.DOTALL)
        code = main_regex.sub("", code)

    if "func Test" in code or "func test" in code:
        test_regex = re.compile(r"func\s+[Tt]est.*?\(.*?\)\s*\{.*\}", re.DOTALL)
        code = test_regex.sub("", code)


    prompt = item["prompt"].split("\n")
    prompt = "\n".join(prompt[:-1])

    other_pkgs = set()
    other_pkgs.add('"github.com/stretchr/testify/assert"')
    other_pkgs.add('"testing"')
    for pkg in IMPORT_HELPER["go"]:
        if '"' + pkg + '"' not in code:
            p = pkg.split("/")[-1]
            if p + "." in code:
                lines = code.split("\n")
                for line in lines:
                    if (p + "." in line) and not (line.strip().startswith("//")):
                        other_pkgs.add('"' + pkg + '"')
                        break
    other_pkgs_str = ""
    if other_pkgs:
        other_pkgs_str = (
            "import (\n" + "\n".join(["    " + p for p in other_pkgs]) + "\n)\n"
        )

    if item["signature"] in prompt:
        prompt = prompt.replace(item["signature"], "")

    # full_code = prompt + "\n" + other_pkgs_str + '\n' + code + "\n" + item["test"]
    full_code = "package main\n" + other_pkgs_str + "\n" + code + "\n" + item["test"]

    return full_code


if __name__ == "__main__":
    items = [
        json.loads(x)
        for x in open(
            # "eval/generations/gpt4/completions_Go_humanevalsynthesize.jsonl"
            "eval/generations/codellama-7b/gen_result_Go.jsonl"
        ).readlines()
        if x
    ]

    for item in [items[5]]:
        prt = extract_go_code(item["raw_generation"][0], item)
        print('"' * 60)
        print(prt)
        # break
