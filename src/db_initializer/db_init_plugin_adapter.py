"""
数据库初始化插件适配器
将现有的DatabaseInitPlugin适配为新的Plugin系统
"""

import logging
from typing import Optional, Dict, Any
from src.component_system import Plugin, ComponentType
from src.config.schema import PluginConfig
from src.db_initializer.plugin_interface import DatabaseInitPlugin

# 配置日志
logger = logging.getLogger(__name__)


class DBInitPluginAdapter(Plugin):
    """数据库初始化插件适配器"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(ComponentType.DB_INITIALIZER, plugin_config)
        self.db_init_plugin = None
        self._name = None
        self._description = None
        
        # 根据配置动态加载
        self._load_db_init_plugin()
    
    def _load_db_init_plugin(self):
        """根据配置动态加载数据库初始化插件"""
        if not self.plugin_config.module or not self.plugin_config.class_name:
            raise ValueError("数据库初始化插件配置缺少module或class_name")
        
        # 从配置中获取模块名和类名
        plugin_module_name = self.plugin_config.module
        plugin_class_name = self.plugin_config.class_name
        
        # 动态导入插件模块
        import importlib
        try:
            plugin_module = importlib.import_module(plugin_module_name)
        except ImportError as e:
            # 如果导入失败，尝试其他可能的导入路径
            logger.warning(f"无法导入模块 {plugin_module_name}: {e}")
            raise
        
        plugin_class = getattr(plugin_module, plugin_class_name)
        
        # 实例化插件，过滤掉不应该传递给构造函数的参数
        from src.component_system import ComponentSystem
        init_kwargs = ComponentSystem._filter_plugin_init_kwargs(self.plugin_config.settings, {})
        
        # 移除type参数，因为它只用于组件系统
        init_kwargs.pop('type', None)
        
        self.db_init_plugin = plugin_class(**init_kwargs)
        self._name = self.db_init_plugin.get_name()
        self._description = self.db_init_plugin.get_description()
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self._name
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self._description
    
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库"""
        if not self.db_init_plugin:
            raise RuntimeError("数据库初始化插件未正确初始化")
        return self.db_init_plugin.initialize_database(db_name, clear_existing)
    
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法"""
        if not self.db_init_plugin:
            raise RuntimeError("数据库初始化插件未正确初始化")
        return self.db_init_plugin.on_database_initialized(db_name, result)