"""
数据清洗相关异常类。
"""

class CleaningError(Exception):
    """数据清洗异常基类。"""
    pass

class DataCleaningError(CleaningError):
    """数据清洗过程异常类。"""
    pass