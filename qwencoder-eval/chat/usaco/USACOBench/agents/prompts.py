basic_generation_prompt = "Please reply with a Python 3 solution to the below problem. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire solution. Feel free to either return just the one code block with your solution or the one code block with explanatory text before and/or after -- however, you will only be evaluated on the correctness of your code. No outside libraries are allowed.\n\n[BEGIN PROBLEM]\n{}\n[END PROBLEM]"

basic_generation_prompt2 = """Please reply with a Python 3 solution to the below problem. Make sure
to wrap your code in '```python' and '```' Markdown delimiters, and
include exactly one block of code with the entire solution.
Reason through the problem and conceptualize a solution first,
then write pseudocode, and finally output the Python
with your solution steps in comments.
No outside libraries are allowed.

[BEGIN PROBLEM]
{}
[END PROBLEM]
"""

retrieval_generation_prompt = "First, read the following passage, which may or may not be helpful or relevant to problem-solving.\n\n[BEGIN PASSAGE]\n{}\n[END PASSAGE]\n\n\nNow, consider the following problem:\n\n[BEGIN PROBLEM]\n{}\n[END PROBLEM]\n\n\nPlease reply with a Python 3 solution to the above problem. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire solution. Feel free to either return just the one code block with your solution or the one code block with explanatory text before and/or after -- however, you will only be evaluated on the correctness of your code. No outside libraries are allowed."

sample_output_prompt = "Consider the following problem.\n\n[BEGIN PROBLEM]\n{}\n[END PROBLEM]\n\nWhat is the expected output for the given input? Think step-by-step before giving your final answer, and use the following format:\n[your reasoning / explanation here]\n[BEGIN OUTPUT]\n[your final answer as formatted output]\n[END OUTPUT]"

# retrieval_generation_multiple_prompt = "Please reply with a Python 3 solution to the below problem. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire solution. Feel free to either return just the one code block with your solution or the one code block with explanatory text before and/or after -- however, you will only be evaluated on the correctness of your code.\n\n[BEGIN PROBLEM]\n{}\n[END PROBLEM]\n\nAlso, feel free to refer to the following passages, which may or may not be helpful or relevant to the problem.\n\n[BEGIN PASSAGES]\n{}\n[END PASSAGES]\n\n"

# new prompts for subtasks project
'''
Format: problem['description']
'''
solve_prompt = """Please reply with a Python 3 solution to the below problem. Make sure to wrap your code in '```python' and '```' Markdown
delimiters, and include exactly one block of code with the entire solution
(in the final code step).
Reason through the problem and:
1. Restate the problem in plain English
2. Conceptualize a solution first in plain English
3. Write a pseudocode solution
4. Output the final Python solution with your solution steps in comments.
No outside libraries are allowed.

[BEGIN PROBLEM]
{}
[END PROBLEM]
"""
def solve_prompt_fn(problem):
    '''
    problem must have solution_english available
    '''
    return solve_prompt.format(problem['description'])


'''
Format: problem['description'], problem['solution_english']
'''
assisted_solve_prompt = """Please reply with a Python 3 solution to the below problem. Make sure to wrap your code in '```python' and '```' Markdown
delimiters, and include exactly one block of code with the entire solution
(in the final code step).
Reason through the problem and:
1. Restate the problem in plain English
2. Closely following the explanation, restate and explain the solution in plain English
3. Write a pseudocode solution
4. Output the final Python solution with your solution steps in comments.
No outside libraries are allowed.

[BEGIN PROBLEM]
{}

[BEGIN EXPLANATION]
{}
[END EXPLANATION]
[END PROBLEM]
"""
def assisted_solve_prompt_fn(problem):
    '''
    problem must have solution_english available
    '''
    return assisted_solve_prompt.format(problem['description'], problem['solution_english'])

debug_solve_prompt = """Here is a programming question, along with a bugged python solution to the above problem.
[BEGIN PROBLEM]
{}
[END PROBLEM]

[BEGIN BUGGED CODE]
{}
[END BUGGED CODE]

Your job is to find the bug, and fix the code. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire fixed code: your output will immediately be auto-evaluated by an execution environment. No outside libraries are allowed. Feel free to input comments in the code to show where you think the bug is, and how you would fix it.
"""
def debug_solve_prompt_fn(problem, error_type=0):
    return debug_solve_prompt.format(problem['description'], problem['bugged_set'][error_type]['bugged_code'])

debug_solve_alt_prompt = """Here is a programming question, along with a bugged python solution to the above problem.
[BEGIN PROBLEM]
{}
[END PROBLEM]

[BEGIN BUGGED CODE]
{}
[END BUGGED CODE]

The bugged solution is almost optimal, but has one bug. Your job is to find the bug, and fix the code. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire fixed code: your output will immediately be auto-evaluated by an execution environment. No outside libraries are allowed. Feel free to input comments in the code to show where you think the bug is, and how you would fix it.
"""

def debug_solve_alt_prompt_fn(problem, error_type=0):
    return debug_solve_alt_prompt.format(problem['description'], problem['bugged_set'][error_type]['bugged_code'])

debug_solve_hint_prompt = """Here is a programming question, along with a bugged python solution to the above problem. You are also given a hint on where the bugged solution is bugged.
[BEGIN PROBLEM]
{}
[END PROBLEM]

[BEGIN BUGGED CODE]
{}
[END BUGGED CODE]

[BEGIN HINT]
{}
[END HINT]

Your job is to find the bug, and fix the code, utilizing the hint given. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire fixed code: your output will immediately be auto-evaluated by an execution environment. No outside libraries are allowed. Feel free to input comments in the code to show where you think the bug is, and how you would fix it.
"""

def debug_solve_hint_prompt_fn(problem, error_type=0):
    return debug_solve_hint_prompt.format(problem['description'], problem['bugged_set'][error_type]['bugged_code'], problem['bugged_set'][error_type]['bugged_hint'])

debug_solve_alt_prompt2 = """Consider the following competitive programming problem and bugged (incorrect) student solution code in Python 3.

[BEGIN PROBLEM]
{}
[END PROBLEM]

[BEGIN BUGGED STUDENT SOLUTION CODE]
{}
[END BUGGED STUDENT SOLUTION CODE]

Your job is to help the student by debugging their solution. Please reply with a Python 3 solution to the above problem that modifies the student code to fix it nad solve the problem. Make sure to wrap your code in '```python' and '```' Markdown
delimiters, and include exactly one block of code with the entire solution (in the final code step).

Specifically, reason through the problem and:
1. Restate the problem in plain English
2. Reason through and explain the student's solution in plain English (including identifying and fixing the bug in the given span)
3. Write a pseudocode solution (including the fixed bug)
4. Output the final Python solution with your solution steps in comments. No outside libraries are allowed.
"""

def debug_solve_alt_prompt2_fn(problem, error_type=0): 
    return debug_solve_alt_prompt2.format(problem['description'], problem['bugged_set'][error_type]['bugged_code'])