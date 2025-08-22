"""
数据管理模块入口文件
"""
from .manager import DataManager, get_data_manager
from .adapter import get_database_adapter
from .initializer import get_db_initializer, initialize_all_databases_from_source_folders
from .models import Poem, Author, Annotation
from .exceptions import DataError, DatabaseError
from .visualizer.queries import VisualizationQueries

__all__ = [
    "DataManager",
    "get_data_manager",
    "get_database_adapter",
    "get_db_initializer",
    "initialize_all_databases_from_source_folders",
    "Poem",
    "Author",
    "Annotation",
    "DataError",
    "DatabaseError",
    "VisualizationQueries"
]