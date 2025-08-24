"""
查询插件接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config.schema import PluginConfig
from src.data.separate_databases import SeparateDatabaseManager


class QueryPlugin(ABC):
    """查询插件抽象基类"""
    
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
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询"""
        pass
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """获取必需的参数列表"""
        pass