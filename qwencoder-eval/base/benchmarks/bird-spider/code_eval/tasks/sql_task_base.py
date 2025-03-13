from code_eval.base import Task
from datasets import load_dataset

SPECIAL_SEPERATOR = "\t----- SQL-EVAL -----\t"


class SqlTaskBase(Task):

    def __init__(self):
        super().__init__(
            stop_words=[
                # "\n\n",
                ";",
                "</s>",
                "<pad>",
                "<|endoftext|>",
                "Question:",
                "Answer:",
            ],
            requires_execution=False,
        )

    def get_dataset(self):
        return self.dataset["train"]

    def get_prompt(self, doc):
        return doc["instruction"] + "\nSELECT "

    def get_reference(self, doc):
        return doc["output"]

    @staticmethod
    def _stop_at_stop_token(decoded_string, stop_tokens):
        min_stop_index = len(decoded_string)
        for stop_token in stop_tokens:
            stop_index = decoded_string.find(stop_token)
            if stop_index != -1 and stop_index < min_stop_index:
                min_stop_index = stop_index

        return decoded_string[:min_stop_index]

    def postprocess_generation(self, generation, idx):

        
        ex = self.dataset["train"][idx]

        prompt = self.get_prompt(ex)

        generation = generation.replace("\n", " ")
        generation = generation.replace(";", "")
        generation = generation.replace("</s>", "")
        generation = self._stop_at_stop_token(generation, self.stop_words)  # Newly added

        db_id = ex["db_id"]
        generation = f"SELECT {generation}{SPECIAL_SEPERATOR}{db_id}"
        return generation

    def process_results(self, generations, references):
        pass
