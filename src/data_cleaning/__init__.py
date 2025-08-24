"""
数据清洗模块入口文件。
"""

from .manager import DataCleaningManager
from .exceptions import CleaningError, CleaningRuleError, DataCleaningError
from .preprocessing_plugin_adapter import PreprocessingPlugin, PreprocessingPluginAdapter

__all__ = [
    "DataCleaningManager",
    "PreprocessingPlugin",
    "PreprocessingPluginAdapter",
    "CleaningError",
    "CleaningRuleError",
    "DataCleaningError"
]