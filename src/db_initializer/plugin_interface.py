"""
数据库初始化插件接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.config.schema import PluginConfig
from src.data.separate_databases import SeparateDatabaseManager


class DatabaseInitPlugin(ABC):
    """数据库初始化插件抽象基类"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        self.config = config or PluginConfig()
        self.separate_db_manager = separate_db_manager
        # 从配置中提取源数据路径和数据库路径
        self.source_dir = self.config.settings.get('source_dir')
        self.db_paths = self.config.settings.get('separate_db_paths', {})
    
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
        """初始化数据库
        
        Args:
            db_name: 数据库名称
            clear_existing: 是否清空现有数据
            
        Returns:
            初始化结果字典
        """
        pass
    
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法
        
        Args:
            db_name: 数据库名称
            result: 初始化结果
        """
        pass


class DatabaseInitPluginManager:
    """数据库初始化插件管理器"""
    
    def __init__(self, config_manager: Optional['ConfigManager'] = None):
        self.plugins = {}
        self.config_manager = config_manager
        self.separate_db_manager = None
    
    def set_separate_db_manager(self, separate_db_manager):
        """设置分离数据库管理器"""
        self.separate_db_manager = separate_db_manager
    
    def register_plugin(self, plugin: DatabaseInitPlugin):
        """注册插件"""
        # 为插件设置分离数据库管理器
        if self.separate_db_manager:
            plugin.separate_db_manager = self.separate_db_manager
        self.plugins[plugin.get_name()] = plugin
    
    def get_plugin(self, name: str) -> Optional[DatabaseInitPlugin]:
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
        
        # 遍历启用的插件列表，尝试加载每个插件
        for plugin_name in project_plugins_config.enabled_plugins:
            try:
                # 获取插件配置
                plugin_config = self.config_manager.get_plugin_config(plugin_name)
                
                # 如果插件被禁用，跳过
                if not plugin_config.enabled:
                    continue
                
                # 尝试导入并实例化插件
                # 从配置中获取模块名和类名
                plugin_module_name = plugin_config.module if plugin_config.module else f"src.db_initializer.plugins.{plugin_name}"
                plugin_class_name = plugin_config.class_name if plugin_config.class_name else f"{plugin_name.capitalize()}InitPlugin"
                
                # 动态导入插件模块
                import importlib
                plugin_module = importlib.import_module(plugin_module_name)
                plugin_class = getattr(plugin_module, plugin_class_name)
                
                # 实例化插件并传入配置和分离数据库管理器
                plugin_instance = plugin_class(config=plugin_config, separate_db_manager=self.separate_db_manager)
                self.register_plugin(plugin_instance)
                
            except Exception as e:
                print(f"警告: 加载数据库初始化插件 '{plugin_name}' 时出错: {e}")
    
    def initialize_plugins(self, db_name: str, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """执行所有插件的数据库初始化"""
        results = {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                result = plugin.initialize_database(db_name, clear_existing)
                results[plugin_name] = result
                # 调用回调方法
                plugin.on_database_initialized(db_name, result)
            except Exception as e:
                results[plugin_name] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results