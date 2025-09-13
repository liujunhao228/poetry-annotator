"""
响应验证核心处理器
"""

import logging
from typing import Dict, Any, List, Optional
from src.plugin_system.manager import get_plugin_manager
from src.plugin_system.plugin_types import PluginType
from src.response_validation.interface import ResponseValidationPlugin

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ResponseValidationCore:
    """
    响应验证核心处理器类，负责处理响应验证的核心逻辑。
    """

    def __init__(self, project_root=None):
        """
        初始化响应验证核心处理器。

        :param project_root: 项目根目录路径
        """
        self.project_root = project_root
        self.plugin_manager = get_plugin_manager()

        # 获取所有已注册的响应验证插件
        self.response_validation_plugins = self.plugin_manager.get_plugins_by_type(PluginType.RESPONSE_VALIDATION)
        self.response_validation_plugins = [
            plugin for plugin in self.response_validation_plugins
            if isinstance(plugin, ResponseValidationPlugin)
        ]

        logger.info(f"找到 {len(self.response_validation_plugins)} 个响应验证插件")

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
        # 如果有插件，使用第一个插件处理
        if self.response_validation_plugins:
            try:
                return self.response_validation_plugins[0].validate_response(result_list)
            except Exception as e:
                logger.error(f"插件处理响应验证时出错: {e}")

        # 默认实现（如果插件不存在或失败）
        if not result_list:
            raise ValueError("解析成功，但JSON数组为空")

        if not isinstance(result_list, list):
            raise TypeError(f"期望得到列表，但实际类型是 {type(result_list)}")

        validated_result = []

        for i, item in enumerate(result_list):
            if not isinstance(item, dict):
                raise ValueError(f"列表第 {i+1} 项不是字典格式: {item}")

            # 创建验证后的项副本
            validated_item = item.copy()

            # 自动去除ID首尾空格
            if 'id' in validated_item and isinstance(validated_item['id'], str):
                validated_item['id'] = validated_item['id'].strip()

            # 验证必需字段
            required_fields = ['id', 'primary', 'secondary']
            for field in required_fields:
                if field not in validated_item:
                    raise ValueError(f"列表第 {i+1} 项缺少必要字段: '{field}' in {validated_item}")

            # 验证字段类型
            if not isinstance(validated_item['id'], str) or not validated_item['id']:
                raise TypeError(f"列表第 {i+1} 项的 'id' 字段必须是非空字符串: {validated_item['id']}")

            if not isinstance(validated_item['primary'], str) or not validated_item['primary']:
                raise TypeError(f"列表第 {i+1} 项的 'primary' 字段必须是非空字符串: {validated_item['primary']}")

            if not isinstance(validated_item['secondary'], list):
                raise TypeError(f"列表第 {i+1} 项的 'secondary' 字段必须是列表: {type(validated_item['secondary'])}")

            # 验证secondary列表中的每个元素都是字符串
            validated_secondary = []
            for j, secondary_id in enumerate(validated_item['secondary']):
                if not isinstance(secondary_id, str):
                    raise TypeError(f"列表第 {i+1} 项 'secondary' 字段中的第 {j+1} 个元素必须是字符串: {secondary_id}")
                validated_secondary.append(secondary_id)

            # 更新验证后的secondary字段
            validated_item['secondary'] = validated_secondary

            # 添加到验证结果中
            validated_result.append(validated_item)

        # 验证通过，返回验证后的列表
        return validated_result

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