<a name="readme-top"></a>

<p align="center">
    <img src="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen2.5/Qwen2.5-Coder/qwen2.5-coder-logo" width="400"/>
<p>

<p align="center">
    <img src="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen2.5/Qwen2.5-Coder-Family/main_fig_32b_white.jpg" width="400"/>
<p>

<p align="center">
        💜 <a href="https://chat.qwenlm.ai/"><b>Qwen Chat</b></a>&nbsp&nbsp | &nbsp&nbsp🤗 <a href="https://huggingface.co/collections/Qwen/qwen25-coder-66eaa22e6f99801bf65b0c2f">Hugging Face</a>&nbsp&nbsp | &nbsp&nbsp🤖 <a href="https://modelscope.cn/organization/qwen">ModelScope</a>&nbsp&nbsp | &nbsp&nbsp💻 <a href="https://www.kaggle.com/models/qwen-lm/qwen2.5-coder">Kaggle</a>&nbsp&nbsp | &nbsp&nbsp 📑 <a href="https://qwenlm.github.io/blog/qwen2.5-coder-family">Blog</a> &nbsp&nbsp ｜ &nbsp&nbsp📖 <a href="https://qwen.readthedocs.io/">Documentation</a>
<br>
🖥️ <a href="https://huggingface.co/spaces/Qwen/Qwen2.5-Coder-demo">Demo</a>&nbsp&nbsp | 🖼 <a href="https://huggingface.co/spaces/Qwen/Qwen2.5-Coder-Artifacts">Artifacts</a>&nbsp&nbsp | &nbsp&nbsp💬 <a href="https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png">WeChat (微信)</a>&nbsp&nbsp | &nbsp&nbsp🫨 <a href="https://discord.gg/CV4E9rpNSD">Discord</a>&nbsp&nbsp | &nbsp&nbsp 📄<a href="https://arxiv.org/abs/2409.12186">Arxiv</a>&nbsp&nbsp | &nbsp&nbsp🖥️ <a href="https://gallery.pai-ml.com/#/preview/deepLearning/nlp/qwen2-5_coder_7b">PAI-DSW</a>&nbsp&nbsp
</p>


Visit our Hugging Face or ModelScope organization (click links above), search checkpoints with names starting with `Qwen2.5-Coder-`, and you will find all you need! Enjoy!

# Qwen2.5-Coder Series: Powerful, Diverse, Practical.

## Introduction

Today, we are excited to open source the “Powerful”, “Diverse”, and “Practical” **Qwen2.5-Coder** series (formerly known as CodeQwen1.5), dedicated to continuously promoting the development of Open CodeLLMs.

💻 Powerful: Qwen2.5-Coder-32B-Instruct has become the current SOTA open-source code model, matching the coding capabilities of GPT-4o. While demonstrating strong and comprehensive coding abilities, it also possesses good general and mathematical skills;

📚 Diverse: Building on the previously open-sourced two sizes of 1.5B / 7B, this release brings four model sizes, including 0.5B / 3B / 14B / 32B. As of now, Qwen2.5-Coder has covered six mainstream model sizes to meet the needs of different developers;

🛠 Practical: We explore the practicality of Qwen2.5-Coder in two scenarios, including code assistants and Artifacts, with some examples showcasing the potential applications of Qwen2.5-Coder in real-world scenarios;

## Basic information

1. ✨ Supporting long context understanding and generation with the context length of 128K tokens;
2. ✨ Supporting 92 coding languages;
```
['ada', 'agda', 'alloy', 'antlr', 'applescript', 'assembly', 'augeas', 'awk', 'batchfile', 'bluespec', 'c', 'c#', 'c++', 'clojure', 'cmake', 'coffeescript', 'common-lisp', 'css', 'cuda', 'dart', 'dockerfile', 'elixir', 'elm', 'emacs-lisp', 'erlang', 'f#', 'fortran', 'glsl', 'go', 'groovy', 'haskell', 'html', 'idris', 'isabelle', 'java', 'java-server-pages', 'javascript', 'json', 'julia', 'jupyter-notebook', 'kotlin', 'lean', 'literate-agda', 'literate-coffeescript', 'literate-haskell', 'lua', 'makefile', 'maple', 'markdown', 'mathematica', 'matlab', 'objectc++', 'ocaml', 'pascal', 'perl', 'php', 'powershell', 'prolog', 'protocol-buffer', 'python', 'r', 'racket', 'restructuredtext', 'rmarkdown', 'ruby', 'rust', 'sas', 'scala', 'scheme', 'shell', 'smalltalk', 'solidity', 'sparql', 'sql', 'stan', 'standard-ml', 'stata', 'swift', 'systemverilog', 'tcl', 'tcsh', 'tex', 'thrift', 'typescript', 'verilog', 'vhdl', 'visual-basic', 'vue', 'xslt', 'yacc', 'yaml', 'zig']
```
3. ✨ Retain strengths in math and general capabilities from base model

> [!Important]
> We updated both the special tokens and their corresponding token ids, in order to maintain consistency with Qwen2.5. The new special tokens are as the following:

```json
{
  "<|fim_prefix|>": 151659, 
  "<|fim_middle|>": 151660, 
  "<|fim_suffix|>": 151661, 
  "<|fim_pad|>": 151662, 
  "<|repo_name|>": 151663, 
  "<|file_sep|>": 151664, 
  "<|im_start|>": 151644, 
  "<|im_end|>": 151645
}
```

| model name                  | type     | length | Download                                                                                                                                                                        |
|-----------------------------|----------|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Qwen2.5-Coder-0.5B          | base     | 32k    | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B)                                       |
| Qwen2.5-Coder-1.5B          | base     | 32k    | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B)                                       |
| Qwen2.5-Coder-3B            | base     | 32k    | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B)                                           |
| Qwen2.5-Coder-7B            | base     | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B)                                           |
| Qwen2.5-Coder-14B           | base     | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B)                                         |
| Qwen2.5-Coder-32B           | base     | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B)                                         |
| Qwen2.5-Coder-0.5B-instruct | instruct | 32k    | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B-Instruct)                     |
| Qwen2.5-Coder-1.5B-instruct | instruct | 32k     | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B-Instruct)                     |
| Qwen2.5-Coder-3B-instruct   | instruct | 32k     | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B-Instruct)                         |
| Qwen2.5-Coder-7B-instruct   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct)                         |
| Qwen2.5-Coder-14B-instruct  | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B-Instruct)                       |
| Qwen2.5-Coder-32B-instruct  | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B-Instruct)                       |
| Qwen2.5-Coder-0.5B-Instruct-AWQ       | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B-Instruct-AWQ)             |
| Qwen2.5-Coder-0.5B-Instruct-GGUF      | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF)           |
| Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int4 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int4) |
| Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int8 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-0.5B-Instruct-GPTQ-Int8) |
| Qwen2.5-Coder-1.5B-Instruct-AWQ       | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B-Instruct-AWQ)             |
| Qwen2.5-Coder-1.5B-Instruct-GGUF      | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF)           |
| Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int4 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int4) |
| Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int8 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-1.5B-Instruct-GPTQ-Int8) |
| Qwen2.5-Coder-3B-Instruct-AWQ       | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ)                 |
| Qwen2.5-Coder-3B-Instruct-GGUF      | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF)               |
| Qwen2.5-Coder-3B-Instruct-GPTQ-Int4 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B-Instruct-GPTQ-Int4)     |
| Qwen2.5-Coder-3B-Instruct-GPTQ-Int8 | instruct | 32k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-3B-Instruct-GPTQ-Int8)     |
| Qwen2.5-Coder-7B-Instruct-AWQ         | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ)             |
| Qwen2.5-Coder-7B-Instruct-GGUF        | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)           |
| Qwen2.5-Coder-7B-Instruct-GPTQ-Int4   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4) |
| Qwen2.5-Coder-7B-Instruct-GPTQ-Int8   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int8) |
| Qwen2.5-Coder-14B-Instruct-AWQ         | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ)             |
| Qwen2.5-Coder-14B-Instruct-GGUF        | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF)           |
| Qwen2.5-Coder-14B-Instruct-GPTQ-Int4   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int4) |
| Qwen2.5-Coder-14B-Instruct-GPTQ-Int8   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int8) |
| Qwen2.5-Coder-32B-Instruct-AWQ         | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ)             |
| Qwen2.5-Coder-32B-Instruct-GGUF        | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF)           |
| Qwen2.5-Coder-32B-Instruct-GPTQ-Int4   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4) |
| Qwen2.5-Coder-32B-Instruct-GPTQ-Int8   | instruct | 128k   | 🤗 [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8) • 🤖 [ModelScope](https://modelscope.cn/models/Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8) |


Detailed performance and introduction are shown in this <a href="https://qwenlm.github.io/blog/qwen2.5-coder-family"> 📑 blog</a>.

## Requirements
* `python>=3.9`
* `transformers>4.37.0` for Qwen2.5 dense models.

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
> **Qwen2.5-Coder-\[0.5-32\]B-Instruct** are instruction models for chatting;
>
> **Qwen2.5-Coder-\[0.5-32\]B** is a base model typically used for completion, serving as a better starting point for fine-tuning.
>
### 👉🏻 Chat with Qwen2.5-Coder-32B-Instruct
You can just write several lines of code with `transformers` to chat with Qwen2.5-Coder-32B-Instruct. Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform chatting with the help of chat template provided by the tokenizer. Below is an example of how to chat with Qwen2.5-Coder-32B-Instruct:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-Coder-32B-Instruct"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

prompt = "write a quick sort algorithm."
messages = [
    {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
```
The `apply_chat_template()` function is used to convert the messages into a format that the model can understand.
The `add_generation_prompt` argument is used to add a generation prompt, which refers to `<|im_start|>assistant\n` to the input. Notably, we apply ChatML template for chat models following our previous practice.
The `max_new_tokens` argument is used to set the maximum length of the response. The `tokenizer.batch_decode()` function is used to decode the response. In terms of the input, the above messages is an example to show how to format your dialog history and system prompt.
You can use the other size of instruct model in the same way.

### 👉🏻 Code with Qwen2.5-Coder-32B

#### 1. Basic Usage
The model completes the code snippets according to the given prompts, without any additional formatting, which is usually termed as `code completion` in the code generation tasks.

Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform code completion. Below is an example on how to chat with Qwen2.5-Coder-32B:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

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


#### 2. Processing Long Texts

The current `config.json` is set for context length up to 32,768 tokens.
To handle extensive inputs exceeding 32,768 tokens, we utilize [YaRN](https://arxiv.org/abs/2309.00071), a technique for enhancing model length extrapolation, ensuring optimal performance on lengthy texts.

For supported frameworks, you could add the following to `config.json` to enable YaRN:
```json
{
  ...,
  "rope_scaling": {
    "factor": 4.0,
    "original_max_position_embeddings": 32768,
    "type": "yarn"
  }
}
```

#### 3. File-Level Code Completion (Fill in the middle)
The code insertion task, also referred to as the "fill-in-the-middle" challenge, requires the insertion of code segments in a manner that bridges the gaps within a given code context.
For an approach aligned with best practices, we recommend adhering to the formatting guidelines outlined in the paper "Efficient Training of Language Models to Fill in the Middle"[[arxiv](https://arxiv.org/abs/2207.14255)]. This involves the use of three specialized tokens`<fim_prefix>`, `<fim_suffix>`, and `<fim_middle>` to denote the respective segments of the code structure.
The prompt should be structured as follows:
```python
prompt = '<|fim_prefix|>' + prefix_code + '<|fim_suffix|>' + suffix_code + '<|fim_middle|>'
```
Following the approach mentioned, an example would be structured in this manner:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
# load model
device = "cuda" # the device to load the model onto

TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

input_text = """<|fim_prefix|>def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    <|fim_suffix|>
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)<|fim_middle|>"""

model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False)[0]
# The generated_ids include prompt_ids, we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```

#### 4. Repository-Level Code Completion
The repository level code completion task involves feeding the model the content of multiple files from the same repository. This enables the model to understand the interrelationships between different calls within these files, thereby facilitating the completion of code content.
We recommend using the two special tokens `<|repo_name|>` and `<|file_sep|>` to indicate the repository structure.
For example, assuming the repository name is stored in `repo_name`, and it contains files with their respective paths and contents listed as [(`file_path1`, `file_content1`), (`file_path2`, `file_content2`)], the format of the final input prompt would be as follows:
```python
input_text = f'''<|repo_name|>{repo_name}
<|file_sep|>{file_path1} 
{file_content1}
<|file_sep|>{file_path2} 
{file_content2}'''
```

<details><summary>👇🏻 Below is a complete example of a repository level code completion task: <i>:: click to expand ::</i></summary>
<div>

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
MODEL = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

# tokenize the input into tokens
input_text = """<|repo_name|>library-system
<|file_sep|>library.py
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

<|file_sep|>student.py
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

<|file_sep|>main.py
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
```python
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

### 👉🏻 Deploying Qwen2.5-Coder with vLLM
As a family member of Qwen2.5, Qwen2.5-Coder are supported by vLLM. The detail tutorial  could be found in [Qwen tutorial](https://qwen.readthedocs.io/en/latest/deployment/vllm.html).
Here, we give you an simple example of offline batched inference in vLLM.

#### Offline Batched Inference
```python
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")

# Pass the default decoding hyperparameters of Qwen1.5-32B-Chat
# max_tokens is for the maximum length for generation.
sampling_params = SamplingParams(temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=1024)

# Input the model name or path. Can be GPTQ or AWQ models.
llm = LLM(model="Qwen/Qwen2.5-Coder-32B")

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

#### Multi-GPU Distributed Serving
To scale up your serving throughputs, distributed serving helps you by leveraging more GPU devices.
When using ultra-long sequences for inference, it might cause insufficient GPU memory. Here, we demonstrate how to run Qwen2.5-Coder-32B with tensor parallelism just by passing in the argument `tensor_parallel_size`.
```python
llm = LLM(model="Qwen/Qwen2.5-Coder-32B", tensor_parallel_size=8)
```
### 👉🏻 Gradio interface 🤗

We also provide a Gradio <a href='https://github.com/gradio-app/gradio'><img src='https://img.shields.io/github/stars/gradio-app/gradio'></a> interface for a better experience, just run by:

```bash
cd demo/chatbot/
# For Linux and Windows users (and macOS with Intel??)
python app.py 

# For macOS with Apple Silicon users, Intel not supported, this maybe 20x slower than RTX 4090
PYTORCH_ENABLE_MPS_FALLBACK=1 python app.py
```

We also provide a Gradio interface of artifacts mode:
```bash
cd demo/artifacts/
python app.py
```

You can specify the `--server_port`, `--share`, `--server_name` arguments to satisfy your needs!

**Or, try it out effortlessly on HuggingFace: [「chatbot demo」](https://huggingface.co/spaces/Qwen/Qwen2.5-Coder-demo) 🤗 [「artifacts demo」](https://huggingface.co/spaces/Qwen/Qwen2.5-Coder-Artifacts)**

## Performance
For more information, please  refer to the <a href="https://arxiv.org/abs/2409.12186">Qwen2.5-Coder Technical Report</a>.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=QwenLM/Qwen2.5-Coder&type=Date)](https://star-history.com/#QwenLM/Qwen2.5-Coder&Date)

## Citation
If you find our work helpful, feel free to give us a cite.

```bibtex
@article{hui2024qwen2,
  title={Qwen2. 5-Coder Technical Report},
  author={Hui, Binyuan and Yang, Jian and Cui, Zeyu and Yang, Jiaxi and Liu, Dayiheng and Zhang, Lei and Liu, Tianyu and Zhang, Jiajun and Yu, Bowen and Dang, Kai and others},
  journal={arXiv preprint arXiv:2409.12186},
  year={2024}
}
@article{qwen2,
    title={Qwen2 Technical Report},
    author={An Yang and Baosong Yang and Binyuan Hui and Bo Zheng and Bowen Yu and Chang Zhou and Chengpeng Li and Chengyuan Li and Dayiheng Liu and Fei Huang and Guanting Dong and Haoran Wei and Huan Lin and Jialong Tang and Jialin Wang and Jian Yang and Jianhong Tu and Jianwei Zhang and Jianxin Ma and Jin Xu and Jingren Zhou and Jinze Bai and Jinzheng He and Junyang Lin and Kai Dang and Keming Lu and Keqin Chen and Kexin Yang and Mei Li and Mingfeng Xue and Na Ni and Pei Zhang and Peng Wang and Ru Peng and Rui Men and Ruize Gao and Runji Lin and Shijie Wang and Shuai Bai and Sinan Tan and Tianhang Zhu and Tianhao Li and Tianyu Liu and Wenbin Ge and Xiaodong Deng and Xiaohuan Zhou and Xingzhang Ren and Xinyu Zhang and Xipin Wei and Xuancheng Ren and Yang Fan and Yang Yao and Yichang Zhang and Yu Wan and Yunfei Chu and Yuqiong Liu and Zeyu Cui and Zhenru Zhang and Zhihao Fan},
    journal={arXiv preprint arXiv:2407.10671},
    year={2024}
}
```

## Contact Us
If you are interested to leave a message to either our research team or product team, join our [Discord](https://discord.gg/z3GAxXZ9Ce) or [WeChat groups](https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png)!

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>
