"""
插件化数据库查询管理器
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.plugin_interface import QueryPluginManager, QueryPlugin
from src.config import config_manager
from src.data.separate_databases import get_separate_db_manager


class PluginBasedQueryManager:
    """插件化数据库查询管理器"""
    
    def __init__(self, db_path: str, config_manager = None):
        self.db_path = db_path
        self.config_manager = config_manager or globals().get('config_manager')
        self.plugin_manager = QueryPluginManager(self.config_manager)
        
        # 初始化分离数据库管理器
        # 这里我们假设使用默认的主数据库名称，实际应用中可能需要根据配置确定
        self.separate_db_manager = get_separate_db_manager("default")
        # 为插件管理器设置分离数据库管理器
        self.plugin_manager.set_separate_db_manager(self.separate_db_manager)
        
        # 根据配置加载插件
        if self.config_manager:
            self.plugin_manager.load_plugins_from_config()
    
    def register_plugin(self, plugin: QueryPlugin):
        """注册自定义插件"""
        # 为插件设置分离数据库管理器
        plugin.separate_db_manager = self.separate_db_manager
        self.plugin_manager.register_plugin(plugin)
    
    def execute_query(self, plugin_name: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"未找到插件: {plugin_name}")
        
        return plugin.execute_query(params)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return self.plugin_manager.list_plugins()