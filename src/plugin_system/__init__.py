"""
插件系统入口文件
"""

from .base import BasePlugin
from .plugin_types import PluginType
from .interfaces import QueryPlugin, PreprocessingPlugin, PromptBuilderPlugin, LabelParserPlugin, DatabaseInitPlugin
from .manager import PluginManager, get_plugin_manager
from .loader import PluginLoader

__all__ = [
    "BasePlugin",
    "PluginType",
    "QueryPlugin",
    "PreprocessingPlugin",
    "PromptBuilderPlugin",
    "LabelParserPlugin",
    "DatabaseInitPlugin",
    "PluginManager",
    "get_plugin_manager",
    "PluginLoader"
]