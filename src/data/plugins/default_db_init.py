"""
默认数据库初始化插件实现
"""
from typing import Dict, Any
from src.data.plugin_interfaces.db_init import DatabaseInitPlugin
from src.db_initializer.initializer import DatabaseInitializer


class DefaultDatabaseInitPlugin(DatabaseInitPlugin):
    """默认数据库初始化插件实现"""
    
    def get_name(self) -> str:
        return "default_db_init"
    
    def get_description(self) -> str:
        return "默认数据库初始化插件实现"
    
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        initializer = DatabaseInitializer()
        return initializer.initialize_database(db_name, clear_existing)