import json
import datasets
import os
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
import jsonlines
import tqdm
import numpy as np
class PromptConstants:
    SYSTEM_MESSAGE_GENERIC = f"You are an expert Python programmer. You will be given a question (problem specification) and will generate a correct Python program that matches the specification and passes all tests. You will NOT return anything except for the program."

    SYSTEM_MESSAGE_DEEPSEEK = f"You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you answer questions related to computer science."

    SYSTEM_MESSAGE_CODEQWEN = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user"

    SYSTEM_MESSAGE_MAGIC = f"You are an exceptionally intelligent coding assistant that consistently delivers accurate and reliable responses to user instructions.\n\n@@ Instruction\n"

    SYSTEM_MESSAGE_WIZARD = "Below is an instruction that describes a task. Write a response that appropriately completes the request."

    SYSTEM_MESSAGE_PHIND = f"""You are an expert Python programmer. You will be given a question (problem specification) and will generate a correct Python program that matches the specification and passes all tests. You will NOT return anything except for the program. Put your fixed program within code delimiters, for example: 
```python 
# YOUR CODE HERE
```"""

    FORMATTING_MESSAGE_WITH_STARTER_CODE = "You will use the following starter code to write the solution to the problem and enclose your code within delimiters."

    FORMATTING_WITHOUT_STARTER_CODE = "Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Enclose your code within delimiters as follows."

class Platform(Enum):
    LEETCODE = "leetcode"
    CODEFORCES = "codeforces"
    ATCODER = "atcoder"


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestType(Enum):
    STDIN = "stdin"
    FUNCTIONAL = "functional"

@dataclass
class Test:
    input: str
    output: str
    testtype: TestType

    def __post_init__(self):
        self.testtype = TestType(self.testtype)
        
@dataclass
class CodeGenerationProblem:
    question_title: str
    question_content: str
    platform: Platform
    question_id: str
    contest_id: str
    contest_date: datetime
    starter_code: str
    difficulty: Difficulty
    public_test_cases: list[Test]
    private_test_cases: list[Test]
    metadata: dict

    def __post_init__(self):
        self.platform = Platform(self.platform)
        self.difficulty = Difficulty(self.difficulty)

        self.public_test_cases = json.loads(self.public_test_cases)
        self.public_test_cases = [Test(**t) for t in self.public_test_cases]

        self.private_test_cases = json.loads(self.private_test_cases)
        self.private_test_cases = [Test(**t) for t in self.private_test_cases]

        self.metadata = json.loads(self.metadata)

    def insert_output(self, output_list: list[str], code_list: list[str]) -> dict:
        return {
            "question_title": self.question_title,
            "question_content": self.question_content,
            "platform": self.platform.value,
            "question_id": self.question_id,
            "contest_id": self.contest_id,
            "contest_date": self.contest_date.isoformat(),
            "starter_code": self.starter_code,
            "difficulty": self.difficulty.value,
            "output_list": output_list,
            "code_list": code_list,
        }

    def insert_output_evaluation(
        self, output_list: list[str], code_list: list[str], graded_list: list[bool]
    ) -> dict:
        output = self.insert_output(output_list, code_list)
        output["graded_list"] = graded_list
        output["pass@1"] = graded_list.count(True) / len(graded_list)
        return output

    def get_evaluation_sample(self):
        return {
            "input_output":
                json.dumps(
                    {
                        "inputs": [
                            t.input
                            for t in self.public_test_cases + self.private_test_cases
                        ],
                        "outputs": [
                            t.output
                            for t in self.public_test_cases + self.private_test_cases
                        ],
                        "fn_name": self.metadata.get("func_name", None),
                    }
                )
        }


def convert_file(source_path, target_path):
    def get_codeqwen_question_template_answer(question: CodeGenerationProblem):
        prompt = "You will be given a question (problem specification) and will generate a correct Python program that matches the specification and passes all tests. You will NOT return anything except for the program.\n\n"
        prompt += f"Question: {question.question_content}\n\n"
        if question.starter_code:
            prompt += (
                f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
            )
            prompt += f"```python\n{question.starter_code}\n```\n\n"
        else:
            prompt += (
                f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
            )
            prompt += f"```python\n# YOUR CODE HERE\n```\n\n"
        return prompt

    def convert(sample):
        prompt = get_codeqwen_question_template_answer(sample)
        tests = sample.get_evaluation_sample()
        data = {
            "prompt": prompt,
            "_test": tests,
            "entry_point": sample.starter_code,
            "tags": f"coding,en,python,core",
            "task": f"livecodebench",
            "source": f"livecodebench",
            "eval_args": {
                "greedy": False,
                "seed": 1234,
                "out_seq_length": 1200,		                             
                "repetition_penalty": 1.0,
                "temperature": 0.2,
                #"beam_size": 10,
                #"presence_penalty": 2.0,
                #"system_str": "你是一个专业的数学家，擅长解答数学问题。",  
                "top_k": -1,
                "top_p": 0.95,
            }
        }
        return data

    if not os.path.exists(os.path.dirname(target_path)):
        os.makedirs(os.path.dirname(target_path))

    with jsonlines.open(target_path, 'w') as w:
        dataset = datasets.load_dataset(source_path)["test"]
        dataset = [CodeGenerationProblem(**p) for p in dataset]
        for i, sample in tqdm.tqdm(enumerate(dataset)):
            new_data = convert(sample)
            new_data[f"sampling_cluster"] = i
            n_sampling = 1
            for _ in range(n_sampling):
                w.write(new_data)
    

    with jsonlines.open(target_path + ".sampled", 'w') as w:
        dataset = datasets.load_dataset(source_path)["test"]
        dataset = [CodeGenerationProblem(**p) for p in dataset][:5]
        for i, sample in tqdm.tqdm(enumerate(dataset)):
            new_data = convert(sample)
            new_data[f"sampling_cluster"] = i
            n_sampling = 1
            for _ in range(n_sampling):
                w.write(new_data)


if __name__ == "__main__":
    convert_file("./data/livecodebench___code_generation", "./data/livecodebench.jsonl")

