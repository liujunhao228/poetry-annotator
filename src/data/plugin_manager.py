"""
插件管理器
"""
from typing import Optional, Type, Dict, Any, List
from src.data.model_plugin_interface import ModelDefinitionPluginManager
from src.data.model_serialization_plugin_interface import ModelSerializationPluginManager


class PluginManager:
    """统一插件管理器"""
    
    _instance: Optional['PluginManager'] = None
    
    def __init__(self):
        self.model_definition_manager = ModelDefinitionPluginManager()
        self.model_serialization_manager = ModelSerializationPluginManager()
        self._plugin_managers = {}  # 存储不同插件类型的管理器
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'PluginManager':
        """获取插件管理器单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize_plugins(self):
        """初始化并注册所有插件"""
        if self._initialized:
            return
        
        self._initialized = True
    
    def register_model_definition_plugin(self, plugin):
        """注册模型定义插件"""
        self.model_definition_manager.register_plugin(plugin)
    
    def register_model_serialization_plugin(self, plugin):
        """注册模型序列化插件"""
        self.model_serialization_manager.register_plugin(plugin)
    
    def register_plugin_manager(self, plugin_type: str, manager):
        """注册特定类型的插件管理器"""
        self._plugin_managers[plugin_type] = manager
    
    def get_plugin_manager(self, plugin_type: str):
        """获取特定类型的插件管理器"""
        return self._plugin_managers.get(plugin_type)
    
    def get_model_class(self, plugin_name: str, model_name: str) -> Optional[Type]:
        """获取模型类"""
        return self.model_definition_manager.get_model_class(plugin_name, model_name)
    
    def create_model_instance(self, plugin_name: str, model_name: str, data: Dict[str, Any]):
        """创建模型实例"""
        return self.model_definition_manager.create_model_instance(plugin_name, model_name, data)
    
    def serialize_model(self, plugin_name: str, model_instance) -> Optional[Dict[str, Any]]:
        """序列化模型实例"""
        return self.model_serialization_manager.serialize_model(plugin_name, model_instance)
    
    def deserialize_model(self, plugin_name: str, model_class: Type, data: Dict[str, Any]):
        """反序列化模型实例"""
        return self.model_serialization_manager.deserialize_model(plugin_name, model_class, data)
    
    def get_model_fields(self, plugin_name: str, model_name: str) -> Optional[List[str]]:
        """获取模型字段列表"""
        return self.model_definition_manager.get_model_fields(plugin_name, model_name)
    
    def get_model_class_by_type(self, plugin_type: str, plugin_name: str, model_name: str) -> Optional[Type]:
        """通过插件类型获取模型类"""
        manager = self._plugin_managers.get(plugin_type)
        if manager and hasattr(manager, 'get_model_class'):
            return manager.get_model_class(plugin_name, model_name)
        return None
    
    def create_model_instance_by_type(self, plugin_type: str, plugin_name: str, model_name: str, data: Dict[str, Any]):
        """通过插件类型创建模型实例"""
        manager = self._plugin_managers.get(plugin_type)
        if manager and hasattr(manager, 'create_model_instance'):
            return manager.create_model_instance(plugin_name, model_name, data)
        return None
    
    def serialize_model_by_type(self, plugin_type: str, plugin_name: str, model_instance) -> Optional[Dict[str, Any]]:
        """通过插件类型序列化模型实例"""
        manager = self._plugin_managers.get(plugin_type)
        if manager and hasattr(manager, 'serialize_model'):
            return manager.serialize_model(plugin_name, model_instance)
        return None