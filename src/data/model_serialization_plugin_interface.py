"""
模型序列化插件接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelSerializationPlugin(ABC):
    """模型序列化插件抽象基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def serialize_model(self, model_instance: Any) -> Dict[str, Any]:
        """将模型实例序列化为字典
        
        Args:
            model_instance: 模型实例
            
        Returns:
            序列化后的字典
        """
        pass
    
    @abstractmethod
    def deserialize_model(self, model_class: type, data: Dict[str, Any]) -> Any:
        """从字典反序列化为模型实例
        
        Args:
            model_class: 模型类
            data: 数据字典
            
        Returns:
            模型实例
        """
        pass
    
    @abstractmethod
    def get_model_fields(self, model_class: type) -> List[str]:
        """获取模型字段列表
        
        Args:
            model_class: 模型类
            
        Returns:
            字段名称列表
        """
        pass


class ModelSerializationPluginManager:
    """模型序列化插件管理器"""
    
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, plugin: ModelSerializationPlugin):
        """注册插件"""
        self.plugins[plugin.get_name()] = plugin
    
    def get_plugin(self, name: str) -> Optional[ModelSerializationPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件及其描述"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def serialize_model(self, plugin_name: str, model_instance: Any) -> Optional[Dict[str, Any]]:
        """序列化模型实例"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.serialize_model(model_instance)
        return None
    
    def deserialize_model(self, plugin_name: str, model_class: type, data: Dict[str, Any]) -> Any:
        """反序列化模型实例"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.deserialize_model(model_class, data)
        return None
    
    def get_model_fields(self, plugin_name: str, model_class: type) -> Optional[List[str]]:
        """获取模型字段列表"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.get_model_fields(model_class)
        return None