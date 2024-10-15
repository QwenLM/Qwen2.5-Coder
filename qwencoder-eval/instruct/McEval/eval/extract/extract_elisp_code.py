import re
import json
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_elisp_code(text, item) -> str:
    entry_point = item["entry_point"]
    code = ""
    code_block = re.search(
        rf"```(?:emacs)?.*?(\(defun\s+{entry_point}.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"(\(defun\s+{entry_point}.*?)(\n\n)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:emacs)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)

    code = "(require 'cl-lib)\n\n" + code
    return code + '\n\n' + item['test']



