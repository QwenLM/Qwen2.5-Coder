from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

checkpoint = "/cpfs01/shared/public/chuzhe.hby/CodeQwen-public/CodeQwen-7B"
TOKENIZER = AutoTokenizer.from_pretrained(checkpoint)
MODEL = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto").eval()

# tokenize the input into tokens
input_text = "#write a quick sort algorithm"
model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=False)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")
