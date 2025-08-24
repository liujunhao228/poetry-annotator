"""
查询插件适配器
将现有的QueryPlugin适配为新的Plugin系统
"""

from typing import Optional
from src.component_system import Plugin, ComponentType, PluginConfig
from src.data.plugin_interface import QueryPlugin
from src.config.schema import PluginConfig as ConfigSchemaPluginConfig


class QueryPluginAdapter(Plugin):
    """查询插件适配器"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(ComponentType.QUERY_PLUGIN, plugin_config)
        self.query_plugin = None
        self._name = None
        self._description = None
        
        # 根据配置动态加载
        self._load_query_plugin()
    
    @classmethod
    def create(cls, plugin_config: PluginConfig, **kwargs):
        """创建插件实例的工厂方法"""
        # 过滤掉不应该传递给构造函数的参数
        from src.component_system import ComponentSystem
        init_kwargs = ComponentSystem._filter_plugin_init_kwargs(plugin_config.settings, kwargs)
        # 移除type参数，因为它只用于组件系统
        init_kwargs.pop('type', None)
        
        # 创建适配器实例
        adapter = cls(plugin_config)
        
        # 如果有额外的参数需要传递给底层插件，可以在适配器中处理
        return adapter
    
    def _load_query_plugin(self):
        """根据配置动态加载查询插件"""
        if not self.plugin_config.module or not self.plugin_config.class_name:
            raise ValueError("查询插件配置缺少module或class_name")
        
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
        
        self.query_plugin = plugin_class(**init_kwargs)
        self._name = self.query_plugin.get_name()
        self._description = self.query_plugin.get_description()
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self._name
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self._description
    
    def execute_query(self, params=None):
        """执行查询"""
        if not self.query_plugin:
            raise RuntimeError("查询插件未正确初始化")
        return self.query_plugin.execute_query(params)
    
    def get_required_params(self):
        """获取必需的参数列表"""
        if not self.query_plugin:
            raise RuntimeError("查询插件未正确初始化")
        return self.query_plugin.get_required_params()