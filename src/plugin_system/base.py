"""
插件系统基础模块
定义插件基类和核心接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


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