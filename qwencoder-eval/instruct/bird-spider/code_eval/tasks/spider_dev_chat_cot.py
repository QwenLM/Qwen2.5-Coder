from .sql_task_chat_cot_base import SqlTaskChatCoTBase


class SpiderDevChat(SqlTaskChatCoTBase):
    DATASET_PATH = "sql_suites/data/spider-dev/spider-dev.json"
    DATASET_NAME = None
