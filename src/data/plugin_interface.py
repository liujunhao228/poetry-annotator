"""
插件化数据库查询接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config.schema import PluginConfig
from src.data.separate_databases import SeparateDatabaseManager
from src.plugin_system.base import ComponentType


class QueryPlugin(ABC):
    """查询插件抽象基类"""
    
    def __init__(self, plugin_config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        self.plugin_config = plugin_config or PluginConfig()
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
        """执行查询
        
        Args:
            params: 查询参数
            
        Returns:
            查询结果DataFrame
        """
        pass
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """获取必需的参数列表"""
        pass


class QueryPluginManager:
    """查询插件管理器"""
    
    def __init__(self, config_manager: Optional['ConfigManager'] = None):
        self.plugins = {}
        self.config_manager = config_manager
        # 初始化分离数据库管理器
        self.separate_db_manager = None
    
    def set_separate_db_manager(self, separate_db_manager):
        """设置分离数据库管理器"""
        self.separate_db_manager = separate_db_manager
    
    def register_plugin(self, plugin: QueryPlugin):
        """注册插件"""
        # 为插件设置分离数据库管理器
        if self.separate_db_manager:
            plugin.separate_db_manager = self.separate_db_manager
        self.plugins[plugin.get_name()] = plugin
    
    def get_plugin(self, name: str) -> Optional[QueryPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件及其描述"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def load_plugins_from_config(self):
        """根据配置动态加载插件"""
        if not self.config_manager:
            return
        
        project_plugins_config = self.config_manager.get_project_plugins_config()
        
        # 遍历所有插件配置，尝试加载启用的插件
        for plugin_name, plugin_config in project_plugins_config.plugins.items():
            try:
                # 如果插件被禁用，跳过
                if not plugin_config.enabled:
                    continue
                
                # 检查插件类型，确保只加载查询插件
                if plugin_config.settings.get('type') != ComponentType.DATA_QUERY.value:
                    continue
                
                # 尝试导入并实例化插件
                # 从配置中获取模块名和类名
                plugin_module_name = plugin_config.module if plugin_config.module else f"src.data.plugins.{plugin_name}"
                plugin_class_name = plugin_config.class_name if plugin_config.class_name else f"{plugin_name.capitalize()}Plugin"
                
                # 动态导入插件模块
                import importlib
                plugin_module = importlib.import_module(plugin_module_name)
                plugin_class = getattr(plugin_module, plugin_class_name)
                
                # 实例化插件并传入配置和分离数据库管理器
                plugin_instance = plugin_class(plugin_config=plugin_config, separate_db_manager=self.separate_db_manager)
                self.register_plugin(plugin_instance)
                
            except Exception as e:
                print(f"警告: 加载插件 '{plugin_name}' 时出错: {e}")
