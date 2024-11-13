from .sql_task_chat_cot_base import SqlTaskChatCoTBase


class BirdDevChat(SqlTaskChatCoTBase):
    DATASET_PATH = "sql_suites/data/bird-dev/bird-dev.json"
    DATASET_NAME = None

