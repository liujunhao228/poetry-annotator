"""
响应解析器插件适配器

本模块提供响应解析功能，作为插件系统的适配器。
"""

import logging
from typing import Dict, Any, List, Optional
from src.component_system import Component, ComponentType, get_component_system
from src.response_parsing.interface import ResponseParsingPlugin

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ResponseParserPluginAdapter(Component, ResponseParsingPlugin):
    """
    响应解析器插件适配器类，继承自Component和ResponseParsingPlugin。
    """

    def __init__(self, project_root=None, config=None):
        """
        初始化响应解析器插件适配器。

        :param project_root: 项目根目录路径
        :param config: 插件配置
        """
        Component.__init__(self, ComponentType.RESPONSE_PARSING)  # 设置组件类型为响应解析器
        ResponseParsingPlugin.__init__(self, config)
        self.project_root = project_root
        self._response_parsing_plugin: Optional[ResponseParsingPlugin] = None
        self._initialize_response_parsing_plugin()

    def _initialize_response_parsing_plugin(self):
        """
        初始化响应解析插件。
        """
        try:
            # 通过组件系统获取响应解析插件
            component_system = get_component_system(self.project_root)
            self._response_parsing_plugin = component_system.get_component(ComponentType.RESPONSE_PARSING)
            logger.info("响应解析插件初始化成功")
        except Exception as e:
            logger.error(f"响应解析插件初始化失败: {e}")
            self._response_parsing_plugin = None

    def get_name(self) -> str:
        """获取插件名称"""
        if self._response_parsing_plugin and hasattr(self._response_parsing_plugin, 'get_name'):
            return self._response_parsing_plugin.get_name()
        return "ResponseParserPluginAdapter"

    def get_description(self) -> str:
        """获取插件描述"""
        if self._response_parsing_plugin and hasattr(self._response_parsing_plugin, 'get_description'):
            return self._response_parsing_plugin.get_description()
        return "响应解析器插件适配器"

    def parse_response(self, text: str) -> List[Dict[str, Any]]:
        """
        解析响应文本

        Args:
            text: LLM返回的原始文本

        Returns:
            一个经过解析的、包含标注信息的字典列表

        Raises:
            ValueError, TypeError: 如果解析失败
        """
        # 直接委托给插件处理
        if not self._response_parsing_plugin:
            # 使用默认实现
            # 这里需要实现一个默认的解析逻辑
            raise ValueError("未找到响应解析插件")

        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._response_parsing_plugin, 'parse_response'):
            return self._response_parsing_plugin.parse_response(text)

        # 如果插件没有实现parse_response但实现了parse_and_validate，则使用它
        if hasattr(self._response_parsing_plugin, 'parse_and_validate'):
            return self._response_parsing_plugin.parse_and_validate(text)

        # 否则抛出异常
        raise ValueError("响应解析插件未实现解析方法")

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
        # 直接委托给插件处理
        if not self._response_parsing_plugin:
            # 使用默认实现
            # 这里需要实现一个默认的解析和验证逻辑
            raise ValueError("未找到响应解析插件")

        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._response_parsing_plugin, 'parse_and_validate'):
            return self._response_parsing_plugin.parse_and_validate(text)

        # 如果插件没有实现parse_and_validate但实现了parse_response，则使用它
        if hasattr(self._response_parsing_plugin, 'parse_response'):
            return self._response_parsing_plugin.parse_response(text)

        # 否则抛出异常
        raise ValueError("响应解析插件未实现解析和验证方法")