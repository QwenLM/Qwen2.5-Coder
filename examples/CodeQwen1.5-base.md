# Use CodeQwen1.5-base By transformers
One of the simple but fundamental ways to try CodeQwen1.5-base is to use the `transformers` library. In this document, we show how to use CodeQwen1.5-base in three common scenarios of code generation, respectively.


## Basic Usage
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

## Code Insertion (Fill in the middle)
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

## Repository Level Code Completion
