"""
数据库初始化模块入口文件
"""

from .initializer import DatabaseInitializer, get_db_initializer
from .cli import main as cli_main
from .plugin_interface import DatabaseInitPlugin, DatabaseInitPluginManager
from .functions import initialize_all_databases_from_source_folders
from .separate_databases import SeparateDatabaseManager, get_separate_db_manager

__all__ = [
    "DatabaseInitializer",
    "get_db_initializer",
    "cli_main",
    "DatabaseInitPlugin",
    "DatabaseInitPluginManager",
    "initialize_all_databases_from_source_folders",
    "SeparateDatabaseManager",
    "get_separate_db_manager"
]
