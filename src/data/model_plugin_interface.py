"""
模型定义插件接口
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List, Optional
from dataclasses import is_dataclass, fields


class ModelDefinitionPlugin(ABC):
    """模型定义插件抽象基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_model_classes(self) -> Dict[str, Type]:
        """获取模型类字典
        
        Returns:
            Dict[str, Type]: 模型名称到模型类的映射
        """
        pass
    
    @abstractmethod
    def create_model_instance(self, model_name: str, data: Dict[str, Any]) -> Any:
        """创建模型实例
        
        Args:
            model_name: 模型名称
            data: 用于创建实例的数据
            
        Returns:
            模型实例
        """
        pass
    
    @abstractmethod
    def get_model_fields(self, model_name: str) -> List[str]:
        """获取模型字段列表
        
        Args:
            model_name: 模型名称
            
        Returns:
            字段名称列表
        """
        pass


class ModelDefinitionPluginManager:
    """模型定义插件管理器"""
    
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, plugin: ModelDefinitionPlugin):
        """注册插件"""
        self.plugins[plugin.get_name()] = plugin
    
    def get_plugin(self, name: str) -> Optional[ModelDefinitionPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件及其描述"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def get_model_class(self, plugin_name: str, model_name: str) -> Optional[Type]:
        """获取模型类"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            model_classes = plugin.get_model_classes()
            return model_classes.get(model_name)
        return None
    
    def create_model_instance(self, plugin_name: str, model_name: str, data: Dict[str, Any]) -> Any:
        """创建模型实例"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.create_model_instance(model_name, data)
        return None
    
    def get_model_fields(self, plugin_name: str, model_name: str) -> Optional[List[str]]:
        """获取模型字段列表"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.get_model_fields(model_name)
        return None