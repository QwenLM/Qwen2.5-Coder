# Use CodeQwen1.5-base By transformers
The most significant but also the simplest usage of CodeQwen1.5-base is using the `transformers` library. In this document, we show how to use CodeQwen1.5-base in three common scenarios of code generation, respectively.


## Basic Usage
The model continues writing the content directly based on the input prompts, without any additional formatting or concatenation, which is called code completion in code generation tasks.

Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform code generation. Below is an example of how to chat with CodeQwen1.5-base:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")
MODEL = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto").eval()

# tokenize the input into tokens
input_text = "#write a quick sort algorithm\ndef "
prompt_ids = TOKENIZER.encode(input_text)
prompt_ids = torch.tensor([prompt_ids], dtype=torch.long).cuda()
prompt_ids = TOKENIZER([input_prompt_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(prompt_ids, max_new_tokens=512, do_sample=False)[0]
# The generated_ids include prompt_ids, we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(prompt_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```

这里还没写，尽快补上
## Code Insertion (Fill in the middle)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
# load model
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/CodeQwen1.5-7B")
MODEL = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto").eval()

input_prompt_text = """<fim_prefix>def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    <fim_suffix>
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)<fim_middle>"""

prompt_ids = TOKENIZER.encode(input_prompt_text)
prompt_ids = torch.tensor([prompt_ids], dtype=torch.long)
generated_ids = MODEL.generate(prompt_ids, max_new_tokens=512, do_sample=False)[0]
output_text = TOKENIZER.decode(generated_ids[len(prompt_ids[0]):], skip_special_tokens=True)

print(output_text)
```
