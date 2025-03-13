from .sql_task_base import SqlTaskBase


class BirdDev(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/bird-dev/bird-dev.json"
    DATASET_NAME = None


class BirdDevNoKG(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/bird-dev/bird-dev-nokg.json"
    DATASET_NAME = None
