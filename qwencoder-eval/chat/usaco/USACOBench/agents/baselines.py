from abc import ABC, abstractmethod
import datasets
import numpy as np
from typing import List, Dict, Any, Union, Callable

from .prompts import basic_generation_prompt, retrieval_generation_prompt
from USACOBench.utils import get_code_from_solution
from USACOBench.retrievers import Retriever
from USACOBench.models import chatgpts_raw

Problem = Dict[Any, Any]
Solution = Dict[str, Union[str, None]]
SolutionSet = List[Solution]

# max len for a retrieved passage
MAX_RETRIEVAL_LEN = 2000

class Agent(ABC):
    def __init__(self, 
                 model=None,
                 prompt: str = basic_generation_prompt):
        '''
        model: model with model.generate() method
        prompt: model prompt as a formatted string
        '''
        if model is None:
            print('Using GPT-4 for generation')
            from USACOBench.models import GPT4
            model = GPT4()
        self.model = model
        self.prompt = prompt

    @abstractmethod
    def solve(self,
              problems: Union[datasets.Dataset, List[Problem]],
              attempts: int = 10) -> List[SolutionSet]:
        '''
        Return solution sets, each set containing the attempts at that question
            (some attempts may have None as the code if its parse failed)
        '''
        pass

    def _process_generations(self, 
                             generations: List[str],
                             problems: Union[datasets.Dataset, List[Problem]],
                             attempts: int) -> List[SolutionSet]:
        '''
        Collates solutions by problem, extracts code, and adds problem metadata
        '''
        generations = np.array(generations).reshape((len(problems), attempts))
        solution_sets = []
        for problem, generations_i in zip(problems, generations):
            solution_sets.append([])
            for generation in generations_i:
                solution_sets[-1].append({
                    'problem_id': problem['problem_id'],
                    'language': 'Python3', # TODO support other languages
                    'solution_code': get_code_from_solution(generation),
                    'solution': generation,
                })
        return solution_sets

class BasicAgent(Agent):
    '''
    Basic agent with no memory.
    '''
    
    def __init__(self, 
                 model=None,
                 prompt: str = basic_generation_prompt):
        '''
        model: model with model.generate() method
        prompt: model prompt as a formatted string
        '''
        super().__init__(model, prompt)

    def solve(self,
              problems: Union[datasets.Dataset, List[Problem]],
              attempts: int = 10,
              prompt_fns: List[Callable[..., str]] = None) -> List[SolutionSet]:
        '''
        Return solution sets, each set containing the attempts at that question
            (some attempts may have None as the code if its parse failed)
        prompt_fns: optionally, per-problem custom prompt functions taking in a problem and outputting a string.
            By default, creates a function that formats self.prompt using the problem description.
        '''
        assert isinstance(problems, datasets.Dataset) or isinstance(problems, list), 'input must be a *list* of problems'
        assert all('description' in problem for problem in problems)
        assert all('problem_id' in problem for problem in problems)
        if prompt_fns is not None:
            prompts = [prompt_fn(problem) for prompt_fn, problem in zip(prompt_fns, problems)]
        else:
            # by default, use a fixed prompt template taking in the description for all problems
            prompts = [self.prompt.format(problem['description']) for problem in problems]
        generations = self.model.generate([prompt for prompt in prompts for i in range(attempts)])
        return self._process_generations(generations, problems, attempts)

class RetrievalAgent(Agent):
    '''
    Basic agent with retrieval and no memory.
    '''
    
    def __init__(self,
                 retriever: Retriever,
                 model,
                 prompt: str = retrieval_generation_prompt):
        '''
        retriever: retriever, owns docs, encoder if using dense retrieval, and any prompts,
            supports a retriever.retrieve method
        '''
        self.retriever = retriever
        super().__init__(model, prompt)

    def solve(self,
              problems: Union[datasets.Dataset, List[Problem]],
              attempts: int = 10) -> List[SolutionSet]:
        '''
        Return solution sets, each set containing the attempts at that question
            (some attempts may have None as the code if its parse failed)
        '''
        assert isinstance(problems, datasets.Dataset) or isinstance(problems, list), 'input must be a *list* of problems'
        assert all('description' in problem for problem in problems)
        assert all('problem_id' in problem for problem in problems)
        generations = self.model.generate([self.prompt.format(
            self.retriever.retrieve(problem['description'])[0][:MAX_RETRIEVAL_LEN],
            problem['description']
        ) for problem in problems for i in range(attempts)])
        return self._process_generations(generations, problems, attempts)
