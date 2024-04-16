def generate_prompt_group1(batch, name, input=None):
    def generate_instruction(data):
        similar_source_code = data['similar_source_code']
        public_similar_tests_input = data['public_similar_tests_input']
        public_similar_tests_output = data['public_similar_tests_output']
        public_target_tests_input = data['public_target_tests_input']
        public_target_tests_output = data['public_target_tests_output']
        instruction = f'''
Write a solution to the following coding problem:
You are assigned the task of modifying the given code snippet to implement a new function that is related to the original function implemented by the code. Ensure your modified code adheres to the programming language's syntax and logic requirements. Validate your solution against the provided test cases to ensure its accuracy. Note that:
1. Your solution should strictly consist of the corrected code only. 
2. You must wrap your code using ```.

Below is the code snippet that implements a specific function:
{similar_source_code}

It currently performs the operation:
Input: {public_similar_tests_input}
Output: {public_similar_tests_output}

You are required to modify this code to implement a new function that is related to the original one, as detailed below:
Input: {public_target_tests_input}
Output: {public_target_tests_output}

Ensure your modified code passes the provided test case.
            '''
        return instruction
    
    batch_prompts = []
    batch_size = len(batch['idx'])
    for idx in range(batch_size):

        if input == "zero":
            prompt = ""
        elif input == "three":
            with open(f'../few_shot_prompt/open/switch/prompt_switch_{name}.txt', 'r') as f:
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
        similar_source_code = data['similar_source_code']
        public_similar_tests_input = data['public_similar_tests_input']
        public_similar_tests_output = data['public_similar_tests_output']
        public_target_tests_input = data['public_target_tests_input']
        public_target_tests_output = data['public_target_tests_output']
        instruction = f'''
### Instruction:
Modify the following code snippet to implement a new specified function, using a step-by-step reasoning process. The process involves analyzing the current code's functionality, identifying necessary changes for the new requirements, and implementing these changes effectively. Follow these steps:

1. **Current Functionality Analysis**: Begin by thoroughly understanding and analyzing the functionality and logic of the current code. Identify the key operations and how they contribute to producing the given output.

2. **Identify New Requirements**: Compare the current functionality with the new function requirements. Highlight the differences in input and output specifications and any additional functionalities that need to be incorporated.

3. **Determine Required Changes**: Based on the analysis, specify the changes needed to adapt the existing code to the new requirements. This includes altering existing logic, adding new logic or functions, and removing unnecessary parts.

4. **Modification Strategy**: Develop a detailed plan for making these changes. This should outline any new algorithms, data structures, or coding constructs required to implement the new functionality while maintaining code efficiency and readability.

5. **Implementation**: Modify the source code according to your strategy. Ensure that the new code accurately implements the desired function and adheres to good coding practices.

6. **Validation**: Validate your modified code using the provided test case. Explain how the new input leads to the expected output, demonstrating the effectiveness of your modifications.

### Question:
Below is the code snippet that needs modification:
{similar_source_code}

It currently performs this operation:
- Input: {public_similar_tests_input}
- Output: {public_similar_tests_output}

Modify the code to achieve the following new functionality:
- Input: {public_target_tests_input}
- Output: {public_target_tests_output}

### Answer:

1. **Current Functionality Analysis**: [Your analysis of the source code's current functionality] (Limit your response to 150 words)

2. **Identify New Requirements**: [The differences between current and new requirements] (Limit your response to 150 words)

3. **Determine Required Changes**: [Specific changes needed for the new functionality] (Limit your response to 150 words)

4. **Modification Strategy**: [Your plan for implementing these changes] (Limit your response to 150 words)

5. **Implementation**: [The modified code snippet]

6. **Validation**: [Explanation of how the modifications meet the new requirements]
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