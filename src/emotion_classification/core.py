"""
情感分类核心处理器
"""

import logging
from typing import Dict, Any, List, Optional
from src.plugin_system.manager import get_plugin_manager
from src.plugin_system.plugin_types import PluginType
from src.emotion_classification.interface import EmotionClassificationPlugin

# 初始化日志记录器
logger = logging.getLogger(__name__)


class EmotionClassificationCore:
    """
    情感分类核心处理器类，负责处理情感分类的核心逻辑。
    """

    def __init__(self, project_root=None):
        """
        初始化情感分类核心处理器。

        :param project_root: 项目根目录路径
        """
        self.project_root = project_root
        self.plugin_manager = get_plugin_manager()
        
        # 获取所有已注册的情感分类插件
        self.emotion_plugins = self.plugin_manager.get_plugins_by_type(PluginType.EMOTION_CLASSIFICATION)
        self.emotion_plugins = [
            plugin for plugin in self.emotion_plugins 
            if isinstance(plugin, EmotionClassificationPlugin)
        ]
        
        logger.info(f"找到 {len(self.emotion_plugins)} 个情感分类插件")

    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_emotion_display_info(emotion_id)
            except Exception as e:
                logger.error(f"插件处理情感显示信息时出错: {e}")
        
        # 默认实现
        return {'id': emotion_id or '', 'name': f"{emotion_id or ''} 未知情感"}

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_full_emotion_list_for_selection(level)
            except Exception as e:
                logger.error(f"插件获取情感列表时出错: {e}")
        
        # 默认返回空列表
        return []

    def get_all_emotion_categories(self) -> Dict[str, Any]:
        """
        获取所有情感分类信息。

        :return: 包含所有情感分类信息的字典
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_all_emotion_categories()
            except Exception as e:
                logger.error(f"插件获取所有情感分类时出错: {e}")
        
        # 默认返回空字典
        return {}

    def get_categories_text(self) -> str:
        """
        获取格式化的情感分类文本，用于提示词。

        :return: 格式化的情感分类文本
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_categories_text()
            except Exception as e:
                logger.error(f"插件获取分类文本时出错: {e}")
        
        # 默认返回
        return "## 情感分类体系：\n\n未加载情感分类信息。\n"

    def get_all_categories(self) -> List[str]:
        """
        获取所有情感分类名称。

        :return: 所有情感分类名称列表
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_all_categories()
            except Exception as e:
                logger.error(f"插件获取所有分类时出错: {e}")
        
        # 默认返回空列表
        return []

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """
        获取所有情感分类ID和名称的映射。

        :return: 情感分类ID和名称的映射字典
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_all_categories_with_ids()
            except Exception as e:
                logger.error(f"插件获取分类ID映射时出错: {e}")
        
        # 默认返回空字典
        return {}

    def validate_emotion(self, emotion: str) -> bool:
        """
        验证情感标签是否在分类体系中。

        :param emotion: 情感标签名称
        :return: 是否有效
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].validate_emotion(emotion)
            except Exception as e:
                logger.error(f"插件验证情感时出错: {e}")
        
        # 默认返回False
        return False

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """
        根据二级类别ID获取一级类别ID。

        :param secondary_id: 二级类别ID
        :return: 对应的一级类别ID，如果未找到则返回None
        """
        # 如果有插件，使用第一个插件处理
        if self.emotion_plugins:
            try:
                return self.emotion_plugins[0].get_primary_category(secondary_id)
            except Exception as e:
                logger.error(f"插件获取一级分类时出错: {e}")
        
        # 默认返回None
        return None
