from .sql_task_base import SqlTaskBase


class SpiderDev(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/spider-dev/spider-dev.json"
    DATASET_NAME = None


class SpiderDevSyn(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/spider-syn-dev/spider-syn-dev.json"
    DATASET_NAME = None


class SpiderDevDk(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/spider-dk-dev/spider-dk-dev.json"
    DATASET_NAME = None


class SpiderDevRealistic(SqlTaskBase):
    DATASET_PATH = "sql_suites/data/spider-realistic-dev/spider-realistic-dev.json"
    DATASET_NAME = None
