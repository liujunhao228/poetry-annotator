"""
数据管理模块异常定义
"""


class DataError(Exception):
    """数据相关错误的基类"""
    pass


class DatabaseError(DataError):
    """数据库相关错误"""
    pass


class DataValidationError(DataError):
    """数据验证错误"""
    pass


class DataNotFoundError(DataError):
    """数据未找到错误"""
    pass