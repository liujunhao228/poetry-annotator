"""
默认响应解析插件
"""

import logging
from typing import List, Dict, Any
from src.response_parsing.interface import ResponseParsingPlugin
from src.config.schema import PluginConfig
from src.response_parsing.llm_response_parser import LLMResponseParser

# 配置日志
logger = logging.getLogger(__name__)


class DefaultResponseParsingPlugin(ResponseParsingPlugin):
    """默认响应解析插件"""

    def __init__(self, plugin_config: PluginConfig = None):
        """
        初始化解析器，并可选择性地指定一个验证器插件名称。
        如果未提供验证器插件名称，则使用默认的全局验证器。
        """
        self.plugin_config = plugin_config or PluginConfig()
        # 使用LLMResponseParser作为后端解析器
        self.backend_parser = LLMResponseParser(self.plugin_config)

    def get_name(self) -> str:
        """获取插件名称"""
        return "default_response_parsing"

    def get_description(self) -> str:
        """获取插件描述"""
        return "默认响应解析插件，提供基础的响应解析功能"

    def parse_response(self, text: str) -> List[Dict[str, Any]]:
        """
        从字符串中稳健地解析出经过内容验证的JSON数组。

        Args:
            text: LLM返回的原始文本。

        Returns:
            一个经过完全验证的、包含标注信息的字典列表。

        Raises:
            ValueError: 如果所有策略都无法解析出有效的、且内容符合业务规范的JSON数组。
        """
        return self.backend_parser.parse_and_validate(text)

    def parse_and_validate(self, text: str) -> List[Dict[str, Any]]:
        """
        解析并验证响应文本（实现ResponseParsingAndValidationPlugin接口）

        Args:
            text: LLM返回的原始文本

        Returns:
            一个经过解析和验证的、包含标注信息的字典列表

        Raises:
            ValueError, TypeError: 如果解析或验证失败
        """
        return self.parse_response(text)