"""
情感分类插件管理器
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from src.emotion_classification.core import EmotionClassificationCore


class EmotionClassificationManager:
    """
    情感分类插件管理器
    """
    
    def __init__(self, project_root: str = "."):
        """
        初始化情感分类管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root
        self.core = EmotionClassificationCore(project_root)
        
    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        return self.core.get_emotion_display_info(emotion_id)

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        return self.core.get_full_emotion_list_for_selection(level)

    def get_all_emotion_categories(self) -> Dict[str, Any]:
        """
        获取所有情感分类信息。

        :return: 包含所有情感分类信息的字典
        """
        return self.core.get_all_emotion_categories()

    def get_categories_text(self) -> str:
        """
        获取格式化的情感分类文本，用于提示词。

        :return: 格式化的情感分类文本
        """
        return self.core.get_categories_text()

    def get_all_categories(self) -> List[str]:
        """
        获取所有情感分类名称。

        :return: 所有情感分类名称列表
        """
        return self.core.get_all_categories()

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """
        获取所有情感分类ID和名称的映射。

        :return: 情感分类ID和名称的映射字典
        """
        return self.core.get_all_categories_with_ids()

    def validate_emotion(self, emotion: str) -> bool:
        """
        验证情感标签是否在分类体系中。

        :param emotion: 情感标签名称
        :return: 是否有效
        """
        return self.core.validate_emotion(emotion)

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """
        根据二级类别ID获取一级类别ID。

        :param secondary_id: 二级类别ID
        :return: 对应的一级类别ID，如果未找到则返回None
        """
        return self.core.get_primary_category(secondary_id)

# 全局情感分类管理器实例
_emotion_classification_manager_instance: Optional[EmotionClassificationManager] = None

def get_emotion_classification_manager(project_root: str = ".") -> EmotionClassificationManager:
    """
    获取全局情感分类管理器实例（单例模式）
    """
    global _emotion_classification_manager_instance
    if _emotion_classification_manager_instance is None:
        _emotion_classification_manager_instance = EmotionClassificationManager(project_root)
    return _emotion_classification_manager_instance
