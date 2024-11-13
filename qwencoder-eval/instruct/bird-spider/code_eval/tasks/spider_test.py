from .sql_task_base import SqlTaskBase


class SpiderTest(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/spider-test/spider-test.json"
    DATASET_NAME = None
