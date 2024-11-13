from .sql_task_chat_base import SqlTaskChatBase


class BirdDevChat(SqlTaskChatBase):
    DATASET_PATH = "sql_suites/data/bird-dev/bird-dev.json"
    DATASET_NAME = None
