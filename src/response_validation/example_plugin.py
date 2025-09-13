"""
响应验证示例插件
"""

import logging
from typing import List, Dict, Any
from src.response_validation.interface import ResponseValidationPlugin
from src.config.schema import PluginConfig
from src.response_validation.core import ResponseValidationCore

# 配置日志
logger = logging.getLogger(__name__)


class ExampleResponseValidationPlugin(ResponseValidationPlugin):
    """示例响应验证插件"""

    def __init__(self, plugin_config: PluginConfig = None):
        """
        初始化示例响应验证插件
        """
        self.plugin_config = plugin_config or PluginConfig()
        self.core = ResponseValidationCore()

    def get_name(self) -> str:
        """获取插件名称"""
        return "ExampleResponseValidationPlugin"

    def get_description(self) -> str:
        """获取插件描述"""
        return "示例响应验证插件，提供基础的响应验证功能"

    def validate_response(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证响应结果
        
        Args:
            result_list: 解析后的标注列表
            
        Returns:
            一个经过验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果验证失败
        """
        # 使用核心验证逻辑
        return self.core.validate_response(result_list)

    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证标注列表的内容（实现ResponseValidatorPlugin接口）
        
        Args:
            result_list: 解析后的标注列表
            
        Returns:
            一个经过验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果验证失败
        """
        return self.validate_response(result_list)