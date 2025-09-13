"""
情感分类器模块

本模块提供情感分类体系的查询和格式化功能，现已重构为插件化架构。
为了保持向后兼容性，该类作为适配器使用新的情感分类模块。
"""

import logging
from typing import Dict, Any, List, Optional
from src.plugin_system.base import Component, ComponentType
from src.emotion_classification.plugin_adapter import EmotionClassifierPluginAdapter

# 初始化日志记录器
logger = logging.getLogger(__name__)

# --- 核心数据结构定义 ---

# 用于存储情感分类的内部表示
# key: emotion_id (e.g., "01.05")
# value: {"name_zh": "愉悦", "name_en": "Joy", "parent_id": "01", "level": 2}
EmotionCategoryMap = Dict[str, Dict[str, Any]]


class EmotionClassifier(Component):
    """
    情感分类器类，作为适配器使用新的情感分类模块。
    """

    def __init__(self, project_root=None):
        """
        初始化情感分类器。

        :param project_root: 项目根目录路径
        """
        super().__init__(ComponentType.LABEL_PARSER)  # 设置组件类型为标签解析器
        self.project_root = project_root
        # 使用新的插件适配器
        self._adapter = EmotionClassifierPluginAdapter(project_root)

    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        return self._adapter.get_emotion_display_info(emotion_id)

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        return self._adapter.get_full_emotion_list_for_selection(level)

    def get_all_emotion_categories(self) -> Dict[str, Any]:
        """
        获取所有情感分类信息。

        :return: 包含所有情感分类信息的字典
        """
        return self._adapter.get_all_emotion_categories()

    def get_categories_text(self) -> str:
        """
        获取格式化的情感分类文本，用于提示词。

        :return: 格式化的情感分类文本
        """
        return self._adapter.get_categories_text()

    def get_all_categories(self) -> List[str]:
        """
        获取所有情感分类名称。

        :return: 所有情感分类名称列表
        """
        return self._adapter.get_all_categories()

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """
        获取所有情感分类ID和名称的映射。

        :return: 情感分类ID和名称的映射字典
        """
        return self._adapter.get_all_categories_with_ids()

    def validate_emotion(self, emotion: str) -> bool:
        """
        验证情感标签是否在分类体系中。

        :param emotion: 情感标签名称
        :return: 是否有效
        """
        return self._adapter.validate_emotion(emotion)

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """
        根据二级类别ID获取一级类别ID。

        :param secondary_id: 二级类别ID
        :return: 对应的一级类别ID，如果未找到则返回None
        """
        return self._adapter.get_primary_category(secondary_id)
