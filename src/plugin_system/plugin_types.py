"""
插件类型枚举
定义系统支持的插件类型
"""

from enum import Enum


class PluginType(Enum):
    """插件类型枚举"""
    QUERY = "query"
    PREPROCESSING = "preprocessing"
    PROMPT_BUILDER = "prompt_builder"
    LABEL_PARSER = "label_parser"
    DATABASE_INIT = "database_init"
    CUSTOM = "custom"
    DATA_STORAGE = "data_storage"
    DATA_QUERY = "data_query"
    DATA_PROCESSING = "data_processing"
    ANNOTATION_MANAGEMENT = "annotation_management"
    DB_INITIALIZER = "db_initializer"
    
    @classmethod
    def from_string(cls, value: str) -> 'PluginType':
        """从字符串创建插件类型"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"未知的插件类型: {value}")