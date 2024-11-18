from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import TextIteratorStreamer
from threading import Thread

device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B-Instruct")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B-Instruct", device_map="auto").eval()

# Instead of using model.chat(), we directly use model.generate()
# But you need to use tokenizer.apply_chat_template() to format your inputs as shown below
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
model_inputs = tokenizer([text], return_tensors="pt").to(device)

streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

generation_kwargs = dict(inputs=model_inputs.input_ids, streamer=streamer, max_new_tokens=2048)
thread = Thread(target=model.generate, kwargs=generation_kwargs)

thread.start()
generated_text = ""
for new_text in streamer:
    generated_text += new_text
    print(new_text, end="")
print(generated_text)
