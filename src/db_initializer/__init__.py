"""
数据库初始化模块入口文件
"""

from .initializer import DatabaseInitializer, get_db_initializer
from .cli import main as cli_main
from .plugin_interface import DatabaseInitPlugin, DatabaseInitPluginManager
from .functions import initialize_all_databases_from_source_folders
from .db_config_manager import get_separate_database_paths, ensure_database_directory_exists
from .separate_databases import SeparateDatabaseManager, get_separate_db_manager

__all__ = [
    "DatabaseInitializer",
    "get_db_initializer",
    "cli_main",
    "DatabaseInitPlugin",
    "DatabaseInitPluginManager",
    "initialize_all_databases_from_source_folders",
    "get_separate_database_paths",
    "ensure_database_directory_exists",
    "SeparateDatabaseManager",
    "get_separate_db_manager"
]