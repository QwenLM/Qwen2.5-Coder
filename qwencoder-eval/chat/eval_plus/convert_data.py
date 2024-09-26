import numpy as np
import jsonlines
import os
import sys

eval_plus_path = os.path.dirname(os.path.abspath(__file__)) + "/evalplus/"
sys.path = [eval_plus_path] + sys.path
from evalplus.data import get_human_eval_plus, get_mbpp_plus

MBPP_OUTPUT_SET_EQ_TASKS = [
    "similar_elements",  # Mbpp/2
    "find_char_long",  # Mbpp/7
    "common_in_nested_lists",  # Mbpp/111
    "extract_singly",  # Mbpp/140
    "larg_nnum",  # Mbpp/232
    "intersection_array",  # Mbpp/249
    "find_dissimilar",  # Mbpp/579
    "Diff",  # Mbpp/769
]
MBPP_OUTPUT_NOT_NONE_TASKS = ["check_str", "text_match_three", "text_starta_endb"]


def convert_file(root_dir):
    import jsonlines
    from copy import deepcopy
    import sys
    import tqdm
    import re
    sys.set_int_max_str_digits(10000000)

    def write_jsonl_file(objs, target_path):
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with jsonlines.open(target_path, "w") as w:
            for obj in objs:
                w.write(obj)
        print(f"Successfully saving to {target_path}")

    # def get_humaneval_prompt(doc, language):
    #     language = language.lower()
    #     question = doc["prompt"].strip()
    #     return """
    # Please continue to complete the function and return all completed code in a codeblock. Here is the given code to do completion:
    # ```{}
    # {}
    # ```
    # """.strip().format(
    #         language.lower(), question.strip()
    #     )

    def get_prompt(doc, language):
        language = language.lower()
        question = doc["prompt"].strip()
        return """
Can you complete the following Python function?
```{}
{}
```
    """.strip().format(language.lower(), question.strip())

    def create_high_accuracy_function(code, entry_point):
        high_accuracy = """
from decimal import Decimal, getcontext
from functools import wraps
getcontext().prec = 100

def convert_to_decimal(value):
    if isinstance(value, float):
        return Decimal(str(value))
    elif isinstance(value, list):
        return [convert_to_decimal(item) for item in value]
    elif isinstance(value, dict):
        return {k: convert_to_decimal(v) for k, v in value.items()}
    return value

def float_to_decimal(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        new_args = [convert_to_decimal(arg) for arg in args]
        new_kwargs = {k: convert_to_decimal(v) for k, v in kwargs.items()}
        result = func(*new_args, **new_kwargs)
        return result
    return wrapper

def convert_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, list):
        return [convert_to_float(item) for item in value]
    elif isinstance(value, dict):
        return {k: convert_to_float(v) for k, v in value.items()}
    return value

def decimal_to_float(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Execute the wrapped function
        result = func(*args, **kwargs)
        
        # Convert the result back to float, if necessary
        result = convert_to_float(result)
        return result
    return wrapper
"""
        """Execute trusted code in place."""
        code = high_accuracy + code
        code = code.split("\n")
        new_code = []
        cnt = 0
        for c in code:
            if re.search(rf"def {entry_point}\(.*?\)", c) is not None:
                cnt += 1
                new_code.append("@float_to_decimal")
                new_code.append("@decimal_to_float")
            new_code.append(c)
        code = "\n".join(new_code)
        return code

    def trusted_exec(code, inputs, entry_point, record_time=False, output_not_none=False):
        exec_globals = {}
        # if entry_point not in ["triangle_area", "angle_complex", "volume_sphere"]: # avoid special case (a ** b)
        #     code = create_high_accuracy_function(code, entry_point)
        if "**" not in code and entry_point not in ["triangle_area", "angle_complex", "volume_sphere"]:
            code = create_high_accuracy_function(code, entry_point)
        #print(code)
        exec(code, exec_globals)
        fn = exec_globals[entry_point]

        rtime = []
        ret = []
        for inp in inputs:
            inp = deepcopy(inp)
            if record_time:
                start = time.time()
                ret.append(fn(*inp))
                rtime.append(time.time() - start)
            else:
                ret.append(fn(*inp))

        if output_not_none:
            ret = [i is not None for i in ret]

        if record_time:
            return ret, rtime
        else:
            return ret

    def convert(objs, test_set="base_input", task_name=f"evalplus/humaneval"):
        type
        data = []
        for obj in tqdm.tqdm(objs):
            prompt = get_prompt(obj, language="python")
            if test_set == "base_input":
                inputs = obj["base_input"]
            else:
                inputs = obj["base_input"] + obj["plus_input"] if not isinstance(obj["plus_input"], dict) else obj["base_input"]
            #outputs = trusted_exec(code = obj["prompt"] + obj["canonical_solution"], inputs = obj["base_input"], entry_point = obj["entry_point"])
            #tests = create_check_function(test_cases = inputs, entry_point=obj["entry_point"], outputs = outputs)
            outputs = trusted_exec(code=obj["prompt"] + obj["canonical_solution"], inputs=[obj["base_input"][0]], entry_point=obj["entry_point"])
            atol = obj["atol"]
            if atol == 0:
                atol = 1e-6  # enforce atol for float comparison
                #```python
            if obj["entry_point"] == "find_zero":  #humaneval
                tests = create_dynamic_check_function_find_zero(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], atol=atol)
            elif obj["entry_point"] in MBPP_OUTPUT_NOT_NONE_TASKS:
                tests = create_dynamic_check_function(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], check_style="not_none", atol=atol)
            elif obj["entry_point"] in MBPP_OUTPUT_SET_EQ_TASKS:  # mbpp
                tests = create_dynamic_check_function(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], check_style="set", atol=atol)
            elif obj["entry_point"] == "are_equivalent":  # mbpp
                tests = create_dynamic_check_function_are_equivalent(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], atol=atol)
            elif obj["entry_point"] == "sum_div":  # mbpp
                tests = create_dynamic_check_function_sum_div(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], atol=atol)
            elif isinstance(outputs[0], float) or (isinstance(outputs[0], list) and len(outputs[0]) > 0 and isinstance(outputs[0][0], float)):
                tests = create_dynamic_check_function(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], check_style="np.allcose", atol=atol)
            else:
                tests = create_dynamic_check_function(test_cases=inputs, entry_point=obj["entry_point"], prompt=obj["prompt"], correct_solution=obj["canonical_solution"], check_style="==", atol=atol)
            data.append({
                "prompt": prompt,
                "test": tests,
                "entry_point": obj["entry_point"],
                "tags": f"coding,en,python,core",
                "task": task_name,
                "source": f"evalplus",
                "eval_args": {
                    "greedy": True,
                    #"seed": 1234,
                    "out_seq_length": 1024,
                    "repetition_penalty": 1.0,
                    "temperature": 1.0,
                    "top_k": -1,
                    "top_p": 0.95,
                    "presence_penalty": 0,
                    "system_str": "You are an intelligent programming assistant to produce Python algorithmic solutions",
                },
                "extra_response_prefix": "```python\n"
            })
        return data

    def create_check_function(test_cases, entry_point, outputs):
        test_cases_str = "def check():\n"
        for case, output in zip(test_cases, outputs):
            for i in range(len(case)):
                if isinstance(case[i], str) and "\n" in case[i]:
                    case[i] = case[i].replace("\n", "\\n")
            input_params = ", ".join([str(c) if not isinstance(c, str) else f"'{c}'" for c in case])
            output = str(output) if not isinstance(output, str) else f"'{output}'"
            single_test_case_str = f"\tassert {entry_point}({input_params}) == {output}\n"
            test_cases_str += single_test_case_str
        test_cases_str += "check()"
        return test_cases_str

    def create_dynamic_check_function_are_equivalent(test_cases, entry_point, prompt, correct_solution, check_style="np.allclose", atol=0):
        test_cases_str = "import numpy as np\n" + prompt + correct_solution
        test_cases_str = test_cases_str.replace(f"def {entry_point}(", f"def {entry_point}_ground_truth(")
        test_cases_str += "def check():\n"
        for case in test_cases:
            for i in range(len(case)):
                if isinstance(case[i], str) and "\n" in case[i]:
                    case[i] = case[i].replace("\n", "\\n")
            input_params = ", ".join([str(c) if not isinstance(c, str) else f"'{c}'" for c in case])
            single_test_case_str = f"\tassert {entry_point}({input_params}) == {entry_point}_ground_truth({input_params}) or {entry_point}({input_params}) == 0\n"
            test_cases_str += single_test_case_str
        test_cases_str += "check()"
        return test_cases_str

    def create_dynamic_check_function_sum_div(test_cases, entry_point, prompt, correct_solution, check_style="np.allclose", atol=0):
        test_cases_str = "import numpy as np\n" + prompt + correct_solution
        test_cases_str = test_cases_str.replace(f"def {entry_point}(", f"def {entry_point}_ground_truth(")
        test_cases_str += "def check():\n"
        for case in test_cases:
            for i in range(len(case)):
                if isinstance(case[i], str) and "\n" in case[i]:
                    case[i] = case[i].replace("\n", "\\n")
            input_params = ", ".join([str(c) if not isinstance(c, str) else f"'{c}'" for c in case])
            single_test_case_str = f"\tassert {entry_point}({input_params}) == {entry_point}_ground_truth({input_params}) or {entry_point}({input_params}) == 0\n"
            test_cases_str += single_test_case_str
        test_cases_str += "check()"
        return test_cases_str

    def create_dynamic_check_function(test_cases, entry_point, prompt, correct_solution, check_style="np.allclose", atol=0):
        test_cases_str = "import numpy as np\n" + prompt + correct_solution
        test_cases_str = test_cases_str.replace(f"def {entry_point}(", f"def {entry_point}_ground_truth(")
        test_cases_str += "def check():\n"
        for case in test_cases:
            for i in range(len(case)):
                if isinstance(case[i], str) and "\n" in case[i]:
                    case[i] = case[i].replace("\n", "\\n")
            input_params = ", ".join([str(c) if not isinstance(c, str) else f"'{c}'" for c in case])
            if check_style == "np.allcose":
                single_test_case_str = f"\tassert np.allclose({entry_point}({input_params}), {entry_point}_ground_truth({input_params}), rtol=1e-07, atol={atol})\n"
            elif check_style == "==":
                single_test_case_str = f"\tassert {entry_point}({input_params}) == {entry_point}_ground_truth({input_params})\n"
            elif check_style == "set":
                single_test_case_str = f"\tassert set({entry_point}({input_params})) == set({entry_point}_ground_truth({input_params}))\n"
            elif check_style == "not_none":
                single_test_case_str = f"\tif isinstance({entry_point}({input_params}), bool):\n"
                single_test_case_str += f"\t\tassert {entry_point}({input_params}) == ({entry_point}_ground_truth({input_params}) is not None)\n"
                single_test_case_str += f"\telse:\n"
                single_test_case_str += f"\t\tassert ({entry_point}({input_params}) is not None) == ({entry_point}_ground_truth({input_params}) is not None)\n"
            test_cases_str += single_test_case_str
        test_cases_str += "check()"
        return test_cases_str

    def create_dynamic_check_function_find_zero(test_cases, entry_point, prompt, correct_solution, atol=0):
        test_cases_str = "import numpy as np\n" + prompt + correct_solution
        test_cases_str = test_cases_str.replace(f"def {entry_point}(", f"def {entry_point}_ground_truth(")
        test_cases_str += "def check():\n"
        for case in test_cases:
            for i in range(len(case)):
                if isinstance(case[i], str) and "\n" in case[i]:
                    case[i] = case[i].replace("\n", "\\n")
            input_params = ", ".join([str(c) if not isinstance(c, str) else f"'{c}'" for c in case])
            single_test_case_str = f"\tassert abs(poly({input_params}, {entry_point}({input_params}))) <= {atol}\n"
            test_cases_str += single_test_case_str
        test_cases_str += "check()"
        return test_cases_str

    humaneval_data = get_human_eval_plus()
    data1 = convert(humaneval_data.values(), test_set="base_input", task_name="evalplus/humaneval")
    write_jsonl_file(data1, f"{root_dir}/evalplus_v2/humaneval.jsonl")
    data2 = convert(humaneval_data.values(), test_set="plus_input", task_name="evalplus/humaneval_plus")
    write_jsonl_file(data2, f"{root_dir}/evalplus_v2/humaneval_plus.jsonl")

    mbpp_data = get_mbpp_plus()
    data3 = convert(mbpp_data.values(), test_set="base_input", task_name="evalplus/mbpp")
    write_jsonl_file(data3, f"{root_dir}/evalplus_v2/mbpp.jsonl")
    data4 = convert(mbpp_data.values(), test_set="plus_input", task_name="evalplus/mbpp_plus")
    write_jsonl_file(data4, f"{root_dir}/evalplus_v2/mbpp_plus.jsonl")

    all_data = data1 + data2 + data3 + data4
    write_jsonl_file(all_data, f"{root_dir}/evalplus_v2/evalplus.jsonl")

    all_data = np.random.choice(all_data, 10)
    write_jsonl_file(all_data, f"{root_dir}/evalplus_v2/evalplus.jsonl.sampled")


if __name__ == "__main__":
    convert_file(root_dir="data/eval/code/")
