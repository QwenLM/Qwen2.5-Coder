# Use Qwen2.5-Coder-32B By transformers
One of the simple but fundamental ways to try Qwen2.5-Coder-32B is to use the `transformers` library. In this document, we show how to use Qwen2.5-Coder-32B in three common scenarios of code generation, respectively.


## Basic Usage
The model completes the code snipplets according to the given prompts, without any additional formatting, which is usually termed as `code completion` in the code generation tasks.
 
Essentially, we build the tokenizer and the model with `from_pretrained` method, and we use generate method to perform code completion. Below is an example on how to chat with Qwen2.5-Coder-32B:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

# tokenize the input into tokens
input_text = "#write a quick sort algorithm"
model_inputs = tokenizer([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
eos_token_ids = [151664, 151662, 151659, 151660, 151661, 151662, 151663, 151664, 151645, 151643]
generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False, eos_token_id=eos_token_ids)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = tokenizer.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```
The `max_new_tokens` argument is used to set the maximum length of the response.
The `input_text` could be any text that you would like model to continue with.

## Code Insertion (Fill in the middle)
The code insertion task, also referred to as the "fill-in-the-middle" challenge, requires the insertion of code segments in a manner that bridges the gaps within a given code context. 
For an approach aligned with best practices, we recommend adhering to the formatting guidelines outlined in the paper "Efficient Training of Language Models to Fill in the Middle"[[arxiv](https://arxiv.org/abs/2207.14255)]. This involves the use of three specialized tokens`<|fim_prefix|>`, `<|fim_suffix|>`, and `<|fim_middle|>` to denote the respective segments of the code structure. 
The prompt should be structured as follows:
```python
prompt = '<|fim_prefix|>' + prefix_code + '<|fim_suffix|>' + suffix_code + '<|fim_middle|>'
```
Following the approach mentioned, an example would be structured in this manner:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
# load model
device = "cuda" # the device to load the model onto

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

input_text = """<|fim_prefix|>def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    <|fim_suffix|>
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)<|fim_middle|>"""

model_inputs = tokenizer([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
eos_token_ids = [151664, 151662, 151659, 151660, 151661, 151662, 151663, 151664, 151645, 151643]
generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False, eos_token_id=eos_token_ids)[0]
# The generated_ids include prompt_ids, we only need to decode the tokens after prompt_ids.
output_text = tokenizer.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
```

## Repository Level Code Completion
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
Below is a complete example of a repository level code completion task:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

# tokenize the input into tokens
input_text = """<repo_name>library-system
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
model_inputs = tokenizer([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
eos_token_ids = [151664, 151662, 151659, 151660, 151661, 151662, 151663, 151664, 151645, 151643]
generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=1024, do_sample=False, eos_token_id=eos_token_ids)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = tokenizer.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: \n{input_text}\n\nGenerated text: \n{output_text.split('<|file_sep|>')[0]}")

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

## Repository Level Code Infilling
Repo level code infilling is essentially about concatenating the repo level format with the FIM format, as shown below,
```python
input_text = f'''<|repo_name|>{repo_name}
<|file_sep|>{file_path1} 
{file_content1}
<|file_sep|>{file_path2} 
{file_content2}
<|file_sep|>{file_path2} 
<|fim_prefix|>{prefix_code}<|fim_suffix|>{suffix_code}<|fim_middle|>'''
```
Below is an example of a repository level code infilling task:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

# tokenize the input into tokens
# set fim format into the corresponding file you need to infilling
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
<|fim_prefix|>from library import Library
from student import Student

def main():
    # Set up the library with some books
    library = Library()
    library.add_book("The Great Gatsby", "F. Scott Fitzgerald", "1234567890", 3)
    library.add_book("To Kill a Mockingbird", "Harper Lee", "1234567891", 2)
    
    # Set up a student
    student = Student("Alice", "S1")
    
    # Student borrows a book<|fim_suffix|>
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
    main()<|fim_middle|>
"""
model_inputs = tokenizer([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
eos_token_ids = [151664, 151662, 151659, 151660, 151661, 151662, 151663, 151664, 151645, 151643]
generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=1024, do_sample=False, eos_token_id=eos_token_ids)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = tokenizer.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: \n{input_text}\n\nGenerated text: \n{output_text.split('<|file_sep|>')[0]}")

# the expected output as following:
"""
Generated text:
    book = library.find_book("1234567890")
"""
```

# Use Qwen2.5-Coder-32B By vllm
As a family member of Qwen2.5, Qwen2.5-Coder-32B are supported by vLLM. The detail tutorial  could be found in [Qwen tutorial](https://qwen.readthedocs.io/en/latest/deployment/vllm.html). 
Here, we only give you an simple example of offline batched inference in vLLM.

## Offline Batched Inference

```python
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")

# Pass the default decoding hyperparameters of Qwen1.5-32B-Chat
# max_tokens is for the maximum length for generation.
eos_token_ids = [151664, 151662, 151659, 151660, 151661, 151662, 151663, 151664, 151645, 151643]
sampling_params = SamplingParams(temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=1024, stop_token_ids=eos_token_ids)

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

## Multi-GPU Distributred Serving
To scale up your serving throughputs, distributed serving helps you by leveraging more GPU devices. 
When using ultra-long sequences for inference, it might cause insufficient GPU memory. Here, we demonstrate how to run Qwen2.5-Coder-32B with tensor parallelism just by passing in the argument `tensor_parallel_size`
```python
llm = LLM(model="Qwen/Qwen2.5-Coder-32B", tensor_parallel_size=8)
```

## Streaming Mode

With the help of `TextStreamer`, you can modify generation with Qwen2.5-Coder to streaming mode. Below we show you an example of how to use it:


```python
# Repeat the code above before model.generate()
# Starting here, we add streamer for text generation.
from transformers import TextStreamer
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

# This will print the output in the streaming mode.
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens=2048,
    streamer=streamer,
)
```

Besides using `TextStreamer`, we can also use `TextIteratorStreamer` which stores print-ready text in a queue, to be used by a downstream application as an iterator:

```python
# Repeat the code above before model.generate()
# Starting here, we add streamer for text generation.
from transformers import TextIteratorStreamer
streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

from threading import Thread
generation_kwargs = dict(inputs=model_inputs.input_ids, streamer=streamer, max_new_tokens=2048)
thread = Thread(target=model.generate, kwargs=generation_kwargs)

thread.start()
generated_text = ""
for new_text in streamer:
    generated_text += new_text
    print(new_text, end="")
```
