import copy
from typing import Any, List


class BaseGen(object):
    def __init__(self, inputs: List[Any], entry_point: str, contract: str):
        """Initializing a input mutator.

        Args:
            inputs (List[Any]): The set of initial inputs (i.e., seeds)
            entry_point (str): The function name to invoke with the input
            contract (str): The contract to verify input validity
        """
        self.contract = contract
        self.entry_point = entry_point
        self.seed_pool: List[Any] = copy.deepcopy(inputs)
        self.new_inputs = []
        self.seed_hash = set([hash(str(x)) for x in self.seed_pool])

    def generate(self, num: int) -> List[Any]:
        raise NotImplementedError
