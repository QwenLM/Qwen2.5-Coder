def generate_prompt_group1(batch, name, input=None):
    def generate_instruction(data):
        source_code = data['source_code']
        public_tests_input = data['public_tests_input']
        public_tests_output = data['public_tests_output']
        instruction = f'''
Write a solution to the following coding problem:
You are assigned the task of optimizing the given code snippet to enhance its execution efficiency and reduce memory usage. Ensuring the accuracy of the code remains unaffected. Validate your solution against the provided test cases to ensure its accuracy. Note that:
1. Your solution should strictly consist of the corrected code only. 
2. You must wrap your code using ```.

Below is the source code snippet that needs optimization:
{source_code}

Optimize the code and ensure it passes the following test case:
Input: {public_tests_input}
Output: {public_tests_output}
            '''
        return instruction

    batch_prompts = []
    batch_size = len(batch['idx'])
    for idx in range(batch_size):

        if input == "zero":
            prompt = ""
        elif input == "three":
            with open(f'../few_shot_prompt/open/polish/prompt_polish_{name}.txt', 'r') as f:
                prompt = f.read()

        new_dict = {}
        for key, values in batch.items():
            new_dict[key] = values[idx]
        instruction = generate_instruction(new_dict)
        
        if name == 'wizardcoder' or name == 'deepseek':
            prompt += f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
"""
        elif name == 'magicoder':
            prompt += f"""You are an exceptionally intelligent coding assistant that consistently delivers accurate and reliable responses to user instructions.

@@ Instruction
{instruction}

@@ Response
"""            
        elif name == "codefuse":
            HUMAN_ROLE_START_TAG = "<|role_start|>human<|role_end|>"
            BOT_ROLE_START_TAG = "<|role_start|>bot<|role_end|>"
            prompt += f"{HUMAN_ROLE_START_TAG}{instruction}{BOT_ROLE_START_TAG}"

        elif name == "octocoder" or name == 'codellama':
            prompt += f"""Question: {instruction} \n\nAnswer:"""
        
        elif name == "phind":
            prompt += f"""
### System Prompt
You are an intelligent programming assistant.

### User Message
{instruction}

### Assistant
"""
        elif name == "codellama-inst":
            prompt += f"<s>[INST] {instruction.strip()} [/INST]"
        elif name == "codeqwen":
            QWEN_PROMPT_START = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
            QWEN_PROMPT_END = "<|im_end|>\n<|im_start|>assistant\n"
            prompt += f"{QWEN_PROMPT_START}{instruction.strip()}{QWEN_PROMPT_END}"
            if idx == 0:
                print(prompt)
        else:
            pass

        batch_prompts.append(prompt)
        # print("Prompt:", prompt)
    
    return batch_prompts



def generate_prompt_cot(batch, name, input=None):
    def generate_instruction(data):
        source_code = data['source_code']
        public_tests_input = data['public_tests_input']
        public_tests_output = data['public_tests_output']
        instruction = f'''
### Instruction:
Optimize the given code snippet for better execution efficiency and reduced memory usage by employing a step-by-step reasoning process. Follow these steps:

1. **Performance and Memory Analysis**: Start by thoroughly analyzing the source code to identify any performance bottlenecks and areas with excessive memory usage. Consider both the complexity of algorithms and the data structures used.

2. **Identify Optimization Opportunities**: Highlight specific lines of code or constructs that are inefficient. Explain why they are problematic and how they contribute to lower performance or higher memory usage.

3. **Optimization Strategies**: Develop a detailed plan for optimizing the code. This should include algorithmic improvements, data structure optimizations, and any coding practices that can enhance efficiency. Explain how each change is expected to improve performance or reduce memory usage.

4. **Implementation**: Apply your optimization strategies to modify the source code. Ensure that these changes maintain the code's accuracy and functionality.

5. **Validation**: Validate the optimized code using the provided test case. Detail how the optimizations impact the execution efficiency and memory usage in the context of the test case.

### Question:
Below is the code snippet that needs optimization:
{source_code}

Use this input to test your optimized code and confirm it produces the expected output.
- Input: {public_tests_input}
- Output: {public_tests_output}

### Answer:

1. **Performance and Memory Analysis**: [Your analysis of the code's performance and memory usage] (Limit your response to 150 words)

2. **Identify Optimization Opportunities**: [Specific inefficiencies and their impacts] (Limit your response to 150 words)

3. **Optimization Strategies**: [Your detailed plan for optimizing the code] (Limit your response to 150 words)

4. **Implementation**: [Your optimized code snippet]

5. **Validation**: [Explanation of how the optimizations improved efficiency or reduced memory usage]
'''
        return instruction

    batch_prompts = []
    batch_size = len(batch['idx'])
    for idx in range(batch_size):
        new_dict = {}
        for key, values in batch.items():
            new_dict[key] = values[idx]
        instruction = generate_instruction(new_dict)
        
        prompt = f"<s>[INST] {instruction.strip()} [/INST]"

        batch_prompts.append(prompt)
        # print("Prompt:", prompt)
    
    return batch_prompts