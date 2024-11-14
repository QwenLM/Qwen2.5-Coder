from .sql_task_chat_base import SqlTaskChatBase


class SpiderDevChat(SqlTaskChatBase):
    DATASET_PATH = "sql_suites/data/spider-dev/spider-dev.json"
    DATASET_NAME = None
