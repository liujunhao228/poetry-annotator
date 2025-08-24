"""
数据模型定义插件接口
"""

from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List, Optional
from src.data.model_plugin_interface import ModelDefinitionPlugin
from src.data.model_serialization_plugin_interface import ModelSerializationPlugin


class DataModelDefinitionPlugin(ModelDefinitionPlugin, ModelSerializationPlugin, ABC):
    """数据模型定义插件抽象基类"""
    
    @abstractmethod
    def get_model_definitions(self) -> Dict[str, Any]:
        """获取数据模型定义
        
        Returns:
            Dict[str, Any]: 模型名称到模型定义的映射
        """
        pass
    
    @abstractmethod
    def get_model_serializers(self) -> Dict[str, Any]:
        """获取数据模型序列化器
        
        Returns:
            Dict[str, Any]: 模型名称到序列化器的映射
        """
        pass