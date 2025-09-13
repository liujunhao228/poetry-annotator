"""
插件系统基础模块
定义插件基类和核心接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)

# 定义严格的组件类型枚举
class ComponentType(Enum):
    """组件类型枚举，确保类型安全"""
    ANNOTATOR = "annotator"
    DATA_MANAGER = "data_manager"
    QUERY_BUILDER = "query_builder"
    PROMPT_BUILDER = "prompt_builder"
    DB_INITIALIZER = "db_initializer"
    LABEL_PARSER = "label_parser"
    CUSTOM_QUERY = "custom_query"
    PREPROCESSING = "preprocessing"
    # 数据相关插件类型
    DATA_STORAGE = "data_storage"
    DATA_QUERY = "data_query"
    DATA_PROCESSING = "data_processing"
    ANNOTATION_MANAGEMENT = "annotation_management"
    DATA_MODEL_DEFINITION = "data_model_definition"
    RESPONSE_VALIDATOR = "response_validator"
    
    @classmethod
    def from_string(cls, value: str) -> 'ComponentType':
        """从字符串创建组件类型"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"未知的组件类型: {value}")

# 定义组件接口
class Component(ABC):
    """组件基类"""
    def __init__(self, component_type: ComponentType):
        self.component_type = component_type
    
    def get_type(self) -> ComponentType:
        """获取组件类型"""
        return self.component_type

class BasePlugin(ABC):
    """基础插件接口"""
    
    def __init__(self, plugin_config: PluginConfig):
        self.plugin_config = plugin_config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    def initialize(self) -> bool:
        """初始化插件"""
        self.logger.debug(f"Initializing plugin: {self.get_name()}")
        return True
    
    def cleanup(self) -> bool:
        """清理插件资源"""
        self.logger.debug(f"Cleaning up plugin: {self.get_name()}")
        return True
    
    def get_config(self) -> PluginConfig:
        """获取插件配置"""
        return self.plugin_config
