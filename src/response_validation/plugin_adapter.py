"""
响应验证器插件适配器

本模块提供响应验证功能，作为插件系统的适配器。
"""

import logging
from typing import Dict, Any, List, Optional
from src.component_system import Component, ComponentType, get_component_system
from src.response_validation.interface import ResponseValidationPlugin

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ResponseValidatorPluginAdapter(Component, ResponseValidationPlugin):
    """
    响应验证器插件适配器类，继承自Component和ResponseValidationPlugin。
    """

    def __init__(self, project_root=None, config=None):
        """
        初始化响应验证器插件适配器。

        :param project_root: 项目根目录路径
        :param config: 插件配置
        """
        Component.__init__(self, ComponentType.RESPONSE_VALIDATOR)  # 设置组件类型为响应验证器
        ResponseValidationPlugin.__init__(self, config)
        # 确保 project_root 是 Path 对象
        from pathlib import Path
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self._response_validation_plugin: Optional[ResponseValidationPlugin] = None
        self._initialize_response_validation_plugin()

    def _initialize_response_validation_plugin(self):
        """
        初始化响应验证插件。
        """
        try:
            # 通过组件系统获取响应验证插件
            component_system = get_component_system(self.project_root)
            self._response_validation_plugin = component_system.get_component(ComponentType.RESPONSE_VALIDATOR)
            logger.info("响应验证插件初始化成功")
        except Exception as e:
            logger.error(f"响应验证插件初始化失败: {e}")
            self._response_validation_plugin = None

    def get_name(self) -> str:
        """获取插件名称"""
        if self._response_validation_plugin and hasattr(self._response_validation_plugin, 'get_name'):
            return self._response_validation_plugin.get_name()
        return "ResponseValidatorPluginAdapter"

    def get_description(self) -> str:
        """获取插件描述"""
        if self._response_validation_plugin and hasattr(self._response_validation_plugin, 'get_description'):
            return self._response_validation_plugin.get_description()
        return "响应验证器插件适配器"

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
        # 直接委托给插件处理
        if not self._response_validation_plugin:
            # 使用默认实现
            # 这里需要实现一个默认的验证逻辑
            raise ValueError("未找到响应验证插件")

        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._response_validation_plugin, 'validate_response'):
            return self._response_validation_plugin.validate_response(result_list)

        # 如果插件没有实现validate_response但实现了validate，则使用它
        if hasattr(self._response_validation_plugin, 'validate'):
            return self._response_validation_plugin.validate(result_list)

        # 否则抛出异常
        raise ValueError("响应验证插件未实现验证方法")

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
        # 直接委托给插件处理
        if not self._response_validation_plugin:
            # 使用默认实现
            # 这里需要实现一个默认的验证逻辑
            raise ValueError("未找到响应验证插件")

        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._response_validation_plugin, 'validate'):
            return self._response_validation_plugin.validate(result_list)

        # 如果插件没有实现validate但实现了validate_response，则使用它
        if hasattr(self._response_validation_plugin, 'validate_response'):
            return self._response_validation_plugin.validate_response(result_list)

        # 否则抛出异常
        raise ValueError("响应验证插件未实现验证方法")