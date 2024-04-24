<a name="readme-top"></a>

<p align="center">
    <img src="https://qianwen-res.oss-accelerate-overseas.aliyuncs.com/assets/blog/codeqwen1.5/codeqwen_logo_final.png" width="400"/>
<p>

<p align="center">
    <img src="https://qianwen-res.oss-accelerate-overseas.aliyuncs.com/assets/blog/codeqwen1.5/intro.png" width="800"/>
<p>


<p align="center">
        🤗 <a href="https://huggingface.co/Qwen/CodeQwen1.5-7B-Chat">Hugging Face</a>&nbsp&nbsp | &nbsp&nbsp🤖 <a href="https://modelscope.cn/organization/qwen">ModelScope</a>&nbsp&nbsp | &nbsp&nbsp 📑 <a href="https://qwenlm.github.io">Blog</a> &nbsp&nbsp ｜ &nbsp&nbsp📖 <a href="https://qwen.readthedocs.io/">Documentation</a>
<br>
🖥️ <a href="https://huggingface.co/spaces/Qwen/Qwen1.5-72B-Chat">Demo</a>&nbsp&nbsp | &nbsp&nbsp💬 <a href="https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png">WeChat (微信)</a>&nbsp&nbsp | &nbsp&nbsp🫨 <a href="https://discord.gg/CV4E9rpNSD">Discord</a>&nbsp&nbsp
</p>


Visit our Hugging Face or ModelScope organization (click links above), search checkpoints with names starting with `CodeQwen1.5-`, and you will find all you need! Enjoy!


## Introduction

CodeQwen1.5 is the Code-Specific version of Qwen1.5. It is a transformer-based decoder-only language model pretrained on a large amount of data of codes.

1. ✨ Strong code generation capabilities and competitve performance across a series of benchmarks;
2. ✨ Supporting long context understanding and generation with the context length of 64K tokens;
3. ✨ Supporting 92 coding languages;
```
['ada', 'agda', 'alloy', 'antlr', 'applescript', 'assembly', 'augeas', 'awk', 'batchfile', 'bluespec', 'c', 'c#', 'c++', 'clojure', 'cmake', 'coffeescript', 'common-lisp', 'css', 'cuda', 'dart', 'dockerfile', 'elixir', 'elm', 'emacs-lisp', 'erlang', 'f#', 'fortran', 'glsl', 'go', 'groovy', 'haskell', 'html', 'idris', 'isabelle', 'java', 'java-server-pages', 'javascript', 'json', 'julia', 'jupyter-notebook', 'kotlin', 'lean', 'literate-agda', 'literate-coffeescript', 'literate-haskell', 'lua', 'makefile', 'maple', 'markdown', 'mathematica', 'matlab', 'objectc++', 'ocaml', 'pascal', 'perl', 'php', 'powershell', 'prolog', 'protocol-buffer', 'python', 'r', 'racket', 'restructuredtext', 'rmarkdown', 'ruby', 'rust', 'sas', 'scala', 'scheme', 'shell', 'smalltalk', 'solidity', 'sparql', 'sql', 'stan', 'standard-ml', 'stata', 'swift', 'systemverilog', 'tcl', 'tcsh', 'tex', 'thrift', 'typescript', 'verilog', 'vhdl', 'visual-basic', 'vue', 'xslt', 'yacc', 'yaml', 'zig']
```
4. ✨ Excellent performance in text-to-SQL, bug fix, etc.

Detailed performance and introduction are shown in this <a href="https://qwenlm.github.io/blog/codeqwen1.5"> 📑 blog</a>.

## Requirements
* `python>=3.9`
* `transformers>=4.37.0` for Qwen1.5 dense models.

> [!Warning]
> <div align="center">
> <b>
> 🚨 This is a must because `transformers` integrated Qwen2 codes since `4.37.0`.
> </b>
> </div>

You can install the required packages with the following command:
```bash
pip install -r requirements.txt
```

## Quick Start

> [!Important]
>
> **CodeQwen1.5-7B-Chat** is a model instruction tuned for chatting;
> **CodeQwen1.5-7B** is a base model typically used for completion, serving as a better starting point for fine-tuning.
> 

### 👉🏻 Chat with CodeQwen1.5-7B-Chat
You can just write several lines of code with `transformers` to chat with CodeQwen1.5-7B-Chat. Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform chatting with the help of chat template provided by the tokenizer. Below is an example of how to chat with CodeQwen1.5-7B-Chat:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B-Chat")
model = AutoModelForCausalLM.from_pretrained("Qwen/CodeQwen1.5-7B-Chat", device_map="auto").eval()

# tokenize the input into tokens

# Instead of using model.chat(), we directly use model.generate()
# But you need to use tokenizer.apply_chat_template() to format your inputs as shown below
prompt = "write a quick sort algorithm."
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(device)

# Directly use generate() and tokenizer.decode() to get the output.
# Use `max_new_tokens` to control the maximum output length.
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens=2048
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
```

The `apply_chat_template()` function is used to convert the messages into a format that the model can understand. 
The `add_generation_prompt` argument is used to add a generation prompt, which refers to `<|im_start|>assistant\n` to the input. Notably, we apply ChatML template for chat models following our previous practice. 
The `max_new_tokens` argument is used to set the maximum length of the response. The `tokenizer.batch_decode()` function is used to decode the response. In terms of the input, the above messages is an example to show how to format your dialog history and system prompt.

### 👉🏻 Code with CodeQwen1.5-7B-Base

#### 1. Basic Usage
The model completes the code snipplets according to the given prompts, without any additional formatting, which is usually termed as `code completion` in the code generation tasks.

Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform code completion. Below is an example on how to chat with CodeQwen1.5-base:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/CodeQwen1.5-7B", device_map="auto").eval()

# tokenize the input into tokens
input_text = "#write a quick sort algorithm"
model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```
The `max_new_tokens` argument is used to set the maximum length of the response.
The `input_text` could be any text that you would like model to continue with.

#### 2. File-Level Code Completion (Fill in the middle)
The code insertion task, also referred to as the "fill-in-the-middle" challenge, requires the insertion of code segments in a manner that bridges the gaps within a given code context. 
For an approach aligned with best practices, we recommend adhering to the formatting guidelines outlined in the paper "Efficient Training of Language Models to Fill in the Middle"[[arxiv](https://arxiv.org/abs/2207.14255)]. This involves the use of three specialized tokens`<fim_prefix>`, `<fim_suffix>`, and `<fim_middle>` to denote the respective segments of the code structure. 
The prompt should be structured as follows:
```python
prompt = '<fim_prefix>' + prefix_code + '<fim_suffix>' + suffix_code + '<fim_middle>'
```
Following the approach mentioned, an example would be structured in this manner:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
# load model
device = "cuda" # the device to load the model onto

TOKENIZER = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/CodeQwen1.5-7B", device_map="auto").eval()

input_text = """<fim_prefix>def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    <fim_suffix>
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)<fim_middle>"""

model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False)[0]
# The generated_ids include prompt_ids, we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```

#### 3. Repository-Level Code Completion
The repository level code completion task involves feeding the model the content of multiple files from the same repository. This enables the model to understand the interrelationships between different calls within these files, thereby facilitating the completion of code content.
We recommend using the two special tokens `<reponame>` and `<file_sep>` to indicate the repository structure.
For example, assuming the repository name is stored in `repo_name`, and it contains files with their respective paths and contents listed as [(`file_path1`, `file_content1`), (`file_path2`, `file_content2`)], the format of the final input prompt would be as follows:
```python
input_text = f'''<reponame>{repo_name}
<file_sep>{file_path1} 
{file_content1}
<file_sep>{file_path2} 
{file_content2}'''
```

<details><summary>👇🏻 Below is a complete example of a repository level code completion task: <i>:: click to expand ::</i></summary>
<div>

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/CodeQwen1.5-7B", device_map="auto").eval()

# tokenize the input into tokens
input_text = """<reponame>library-system
<file_sep>library.py
class Book:
    def __init__(self, title, author, isbn, copies):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.copies = copies

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, Copies: {self.copies}"

class Library:
    def __init__(self):
        self.books = []

    def add_book(self, title, author, isbn, copies):
        book = Book(title, author, isbn, copies)
        self.books.append(book)

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def list_books(self):
        return self.books

<file_sep>student.py
class Student:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.borrowed_books = []

    def borrow_book(self, book, library):
        if book and book.copies > 0:
            self.borrowed_books.append(book)
            book.copies -= 1
            return True
        return False

    def return_book(self, book, library):
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
            book.copies += 1
            return True
        return False

<file_sep>main.py
from library import Library
from student import Student

def main():
    # Set up the library with some books
    library = Library()
    library.add_book("The Great Gatsby", "F. Scott Fitzgerald", "1234567890", 3)
    library.add_book("To Kill a Mockingbird", "Harper Lee", "1234567891", 2)
    
    # Set up a student
    student = Student("Alice", "S1")
    
    # Student borrows a book
"""
model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=1024, do_sample=False)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: \n{input_text}\n\nGenerated text: \n{output_text}")

```
The expected output as following:
```
Generated text:
    book = library.find_book("1234567890")
    if student.borrow_book(book, library):
    print(f"{student.name} borrowed {book.title}")
    else:
    print(f"{student.name} could not borrow {book.title}")
    
        # Student returns a book
        if student.return_book(book, library):
            print(f"{student.name} returned {book.title}")
        else:
            print(f"{student.name} could not return {book.title}")
        
        # List all books in the library
        print("All books in the library:")
        for book in library.list_books():
            print(book)

if __name__ == "__main__":
main()
```

</div>
</details>

### 👉🏻 Deploying CodeQwen with vLLM
As a family member of Qwen1.5, CodeQwen1.5 are supported by vLLM. The detail tutorial  could be found in [Qwen tutorial](https://qwen.readthedocs.io/en/latest/deployment/vllm.html). 
Here, we give you an simple example of offline batched inference in vLLM.

#### Offline Batched Inference
```python
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")

# Pass the default decoding hyperparameters of Qwen1.5-7B-Chat
# max_tokens is for the maximum length for generation.
sampling_params = SamplingParams(temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=1024)

# Input the model name or path. Can be GPTQ or AWQ models.
llm = LLM(model="Qwen/CodeQwen1.5-7B")

# Prepare your prompts
prompt = "#write a quick sort algorithm.\ndef quick_sort("

# generate outputs
outputs = llm.generate([prompt], sampling_params)

# Print the outputs.
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
```

#### Multi-GPU Distributred Serving
To scale up your serving throughputs, distributed serving helps you by leveraging more GPU devices. 
When using ultra-long sequences for inference, it might cause insufficient GPU memory. Here, we demonstrate how to run CodeQwen1.5-7B with tensor parallelism just by passing in the argument `tensor_parallel_size`.
```python
llm = LLM(model="Qwen/CodeQwen1.5-7B", tensor_parallel_size=4)
```


## Performance

### EvalPlus (HumanEval, MBPP)

We recommend using EvalPlus to evaluate the effectiveness of HumaneEval and MBPP. [Here](https://github.com/QwenLM/CodeQwen1.5/tree/main/evaluation/eval_plus) is our evaluation script.

<table style="text-align:center;">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>HumanEval</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>HumanEval+</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP+</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP</div>
            <div class="cell-aux">3-shot</div>
        </td>
    </tr>
    <tr>
        <td colspan=7><center><b>Base Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>33.5</td>
        <td>25.6</td>
        <td>52.1</td>
        <td>41.6</td>
        <td>38.6</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2</td>
        <td style="text-align: left">7B</td>
        <td>35.4</td>
        <td>29.9</td>
        <td>54.4</td>
        <td>45.6</td>
        <td>51.0</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>47.6</td>
        <td>39.6</td>
        <td>70.2</td>
        <td>56.6</td>
        <td>60.6</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td>
        <td>51.8</td>
        <td>45.7</td>
        <td>72.2</td>
        <td>60.2</td>
        <td>61.8</td>
    </tr>
    <tr>
        <td colspan=7><center><b>Chat Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>76.8</td>
        <td>70.7</td>
        <td>82.5</td>
        <td>69.7</td>
        <td>70.8</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4-Turbo (Nov 2023)</td>
        <td style="text-align: left">-</td>
        <td>85.4</td>
        <td>81.7</td>
        <td>83.5</td>
        <td>70.7</td>
        <td>80.0</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>73.8</td>
        <td>70.1</td>
        <td>73.2</td>
        <td>63.4</td>
        <td>65.4</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td>83.5</td>
        <td>78.7</td>
        <td>77.7</td>
        <td>67.2</td>
        <td>70.6</td>
    </tr>
</table>

### LiveCodeBench

[LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) provides holistic and contamination-free evaluation of coding capabilities of LLMs. Particularly, LiveCodeBench continuously collects new problems over time from contests across three competition platforms -- LeetCode, AtCoder, and CodeForces. 
[Here](https://github.com/QwenLM/CodeQwen1.5/tree/main/evaluation/livecode_bench) is our evaluation script.

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>All Time</div>
                <div>Pass@1</div>
            </div>
        </td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>2023/9/1 ~ 2024/4/1</div>
                <div>Pass@1</div>
            </div>
        </td>
    </tr>
    <tr>
        <td colspan=4><center><b>Base Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>6.5</td>
        <td>7.6</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2</td>
        <td style="text-align: left">7B</td>
        <td>11.3</td>
        <td>12.7</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>19.1</td>
        <td>13.7</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td>
        <td><b>21.8</b></td>
        <td><b>19.3</b></td>
    </tr>
    <tr>
        <td colspan=4><center><b>Chat Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Instruct</td>
        <td style="text-align: left">7B</td>
        <td>10.6</td>
        <td>12.4</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>21.6</td>
        <td>19.2</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td><b>25.0</b></td>
        <td><b>23.2</b></td>
    </tr>
</table>

### MultiPL-E

MultiPL-E is a popular benchmark for evaluating multiple programming languages. 
You can find our reproduce process [here](https://github.com/QwenLM/CodeQwen1.5/tree/main/evaluation/multipl_e).

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>Python</td>
        <td>C++</td>
        <td>Java</td>
        <td>PHP</td>
        <td>TS</td>
        <td>C#</td>
        <td>Bash</td>
        <td>JS</td>
        <td>Avg</td>
    </tr>
    <tr>
        <td colspan=11><b>Base Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>31.7</td>
        <td>29.8</td>
        <td>34.2</td>
        <td>23.6</td>
        <td>36.5</td>
        <td>36.7</td>
        <td>12.0</td>
        <td>29.2</td>
        <td>29.2</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2-Base</td>
        <td style="text-align: left">7B</td>
        <td>35.3</td>
        <td>40.9</td>
        <td>37.3</td>
        <td>29.2</td>
        <td>37.7</td>
        <td>40.5</td>
        <td>9.4</td>
        <td>36.0</td>
        <td>33.3</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>49.4</td>
        <td>50.3</td>
        <td>43.0</td>
        <td>38.5</td>
        <td>49.7</td>
        <td>50.0</td>
        <td>28.5</td>
        <td>48.4</td>
        <td>44.7</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5<b></td>
        <td style="text-align: left">7B</td>
        <td>52.4</td>
        <td>52.2</td>
        <td>42.4</td>
        <td>46.6</td>
        <td>52.2</td>
        <td>55.7</td>
        <td>36.7</td>
        <td>49.7</td>
        <td>48.5</td>
    </tr>
    <tr>
        <td colspan=11><b>Chat Model</b></td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>76.2</td>
        <td>63.4</td>
        <td>69.2</td>
        <td>60.9</td>
        <td>69.1</td>
        <td>70.8</td>
        <td>42.4</td>
        <td>67.1</td>
        <td>64.9</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4</td>
        <td style="text-align: left">-</td>
        <td>84.1</td>
        <td>76.4</td>
        <td>81.6</td>
        <td>77.2</td>
        <td>77.4</td>
        <td>79.1</td>
        <td>58.2</td>
        <td>78.0</td>
        <td>76.5</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>78.6</td>
        <td>63.4</td>
        <td>68.4</td>
        <td>68.9</td>
        <td>67.2</td>
        <td>72.8</td>
        <td>36.7</td>
        <td>72.7</td>
        <td>66.1</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td>83.2</td>
        <td>71.2</td>
        <td>70.1</td>
        <td>73.5</td>
        <td>75.4</td>
        <td>75.9</td>
        <td>41.1</td>
        <td>78.2</td>
        <td>71.1</td>
    </tr>
</table>

### Text-to-SQL
We evaluated CodeQwen1.5-7B-Chat on popular text-to-SQL benchmarks Spider and BIRD. Here you can find the [prompts](https://github.com/QwenLM/CodeQwen1.5/tree/main/evaluation/text_to_sql) we used, sourced from [Chang et al](https://arxiv.org/abs/2305.11853) and [Li et al](https://arxiv.org/abs/2305.03111).

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>Spider</div>
            <div class="cell-aux">
                <div>Execution Accuracy</div>
                <div>Dev Set</div>
            </div>
        </td>
        <td>
            <div>Bird</div>
            <div class="cell-aux">
                <div>Execution Accuracy</div>
                <div>Dev Set</div>
            </div>
        </td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>70.1</td>
        <td>37.2</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4</td>
        <td style="text-align: left">-</td>
        <td>85.3</td>
        <td>50.7</td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Instruct</td>
        <td style="text-align: left">7B</td>
        <td>59.5</td>
        <td>22.4</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>70.1</td>
        <td>39.4</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td><b>77.9</b></td>
        <td><b>42.0</b></td>
    </tr>
</table>



## Citation
If you find our work helpful, feel free to give us a cite.

```bibtex
@article{qwen,
  title={Qwen Technical Report},
  author={Jinze Bai and Shuai Bai and Yunfei Chu and Zeyu Cui and Kai Dang and Xiaodong Deng and Yang Fan and Wenbin Ge and Yu Han and Fei Huang and Binyuan Hui and Luo Ji and Mei Li and Junyang Lin and Runji Lin and Dayiheng Liu and Gao Liu and Chengqiang Lu and Keming Lu and Jianxin Ma and Rui Men and Xingzhang Ren and Xuancheng Ren and Chuanqi Tan and Sinan Tan and Jianhong Tu and Peng Wang and Shijie Wang and Wei Wang and Shengguang Wu and Benfeng Xu and Jin Xu and An Yang and Hao Yang and Jian Yang and Shusheng Yang and Yang Yao and Bowen Yu and Hongyi Yuan and Zheng Yuan and Jianwei Zhang and Xingxuan Zhang and Yichang Zhang and Zhenru Zhang and Chang Zhou and Jingren Zhou and Xiaohuan Zhou and Tianhang Zhu},
  journal={arXiv preprint arXiv:2309.16609},
  year={2023}
}
```

## Contact Us
If you are interested to leave a message to either our research team or product team, join our [Discord](https://discord.gg/z3GAxXZ9Ce) or [WeChat groups](https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png)!

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>
