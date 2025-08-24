"""
数据清洗相关异常类。
"""


class CleaningError(Exception):
    """数据清洗异常基类。"""
    pass


class CleaningRuleError(CleaningError):
    """数据清洗规则异常类，用于表示规则加载或应用失败的情况。"""
    pass


class DataCleaningError(CleaningError):
    """数据清洗过程异常类。"""
    pass