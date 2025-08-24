"""
数据库初始化插件接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.config.schema import PluginConfig
from src.data.separate_databases import SeparateDatabaseManager


class DatabaseInitPlugin(ABC):
    """数据库初始化插件抽象基类"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        self.config = config or PluginConfig()
        self.separate_db_manager = separate_db_manager
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库"""
        pass