"""
插件化查询管理器
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.plugin_interfaces.query import QueryPlugin
from src.data.plugin_query_manager import PluginBasedQueryManager


class PluginBasedQueryManager(QueryPlugin):
    """插件化查询管理器"""
    
    def __init__(self, db_path: str, config_manager=None):
        self.db_path = db_path
        self.config_manager = config_manager
        self.query_manager = PluginBasedQueryManager(db_path, config_manager)
    
    def get_name(self) -> str:
        return "plugin_based_query_manager"
    
    def get_description(self) -> str:
        return "插件化查询管理器"
    
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        # 这里需要指定具体的插件名称来执行查询
        # 作为示例，我们假设有一个默认的查询插件
        return self.query_manager.execute_query("default_query", params)
    
    def get_required_params(self) -> List[str]:
        # 默认实现不需要特定参数
        return []
    
    def register_plugin(self, plugin: QueryPlugin):
        """注册自定义插件"""
        self.query_manager.register_plugin(plugin)
    
    def execute_plugin_query(self, plugin_name: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行指定插件的查询"""
        return self.query_manager.execute_query(plugin_name, params)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return self.query_manager.list_plugins()