"""
示例情感分类插件
"""

import logging
from typing import Dict, Any, List, Optional
from src.emotion_classification.interface import EmotionClassificationPlugin

# 配置日志
logger = logging.getLogger(__name__)

# 示例情感分类数据
EXAMPLE_EMOTION_CATEGORIES = {
    "01": {
        "name_zh": "积极情感",
        "name_en": "Positive Emotion",
        "categories": [
            {"id": "01.01", "name_zh": "喜悦", "name_en": "Joy"},
            {"id": "01.02", "name_zh": "热爱", "name_en": "Love"},
            {"id": "01.03", "name_zh": "崇敬", "name_en": "Reverence"},
            {"id": "01.04", "name_zh": "赞赏", "name_en": "Appreciation"},
            {"id": "01.05", "name_zh": "愉悦", "name_en": "Pleasure"}
        ]
    },
    "02": {
        "name_zh": "消极情感",
        "name_en": "Negative Emotion",
        "categories": [
            {"id": "02.01", "name_zh": "悲伤", "name_en": "Sadness"},
            {"id": "02.02", "name_zh": "愤怒", "name_en": "Anger"},
            {"id": "02.03", "name_zh": "恐惧", "name_en": "Fear"},
            {"id": "02.04", "name_zh": "厌恶", "name_en": "Disgust"},
            {"id": "02.05", "name_zh": "焦虑", "name_en": "Anxiety"}
        ]
    }
}


class ExampleEmotionClassificationPlugin(EmotionClassificationPlugin):
    """示例情感分类插件"""

    def __init__(self, plugin_config: Optional[Dict[str, Any]] = None):
        super().__init__(plugin_config)
        logger.info("ExampleEmotionClassificationPlugin initialized with config: %s", plugin_config)

    def get_name(self) -> str:
        """获取插件名称"""
        return "ExampleEmotionClassificationPlugin"

    def get_description(self) -> str:
        """获取插件描述"""
        return "示例情感分类插件，提供基础的情感分类功能"

    def get_categories(self) -> Dict[str, Any]:
        """
        获取插件提供的额外分类信息

        Returns:
            插件提供的分类信息字典
        """
        return EXAMPLE_EMOTION_CATEGORIES

    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        # 在插件提供的分类中查找指定ID的情感
        for primary_id, primary_data in EXAMPLE_EMOTION_CATEGORIES.items():
            # 检查一级分类
            if primary_id == emotion_id:
                name_zh = primary_data.get('name_zh', '')
                return {'id': emotion_id, 'name': f"{emotion_id} {name_zh}"}
            
            # 检查二级分类
            for secondary in primary_data.get('categories', []):
                if secondary.get('id') == emotion_id:
                    name_zh = secondary.get('name_zh', '')
                    return {'id': emotion_id, 'name': f"{emotion_id} {name_zh}"}
        
        # 如果未找到，返回未知情感
        return {'id': emotion_id, 'name': f"{emotion_id} 未知情感"}

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        emotion_list = []
        
        # 根据层级获取分类列表
        if level == 1:
            # 获取一级分类
            for primary_id, primary_data in EXAMPLE_EMOTION_CATEGORIES.items():
                name_zh = primary_data.get('name_zh', '')
                emotion_list.append({'id': primary_id, 'name': f"{primary_id} {name_zh}"})
        elif level == 2:
            # 获取二级分类
            for primary_data in EXAMPLE_EMOTION_CATEGORIES.values():
                for secondary in primary_data.get('categories', []):
                    secondary_id = secondary.get('id', '')
                    name_zh = secondary.get('name_zh', '')
                    emotion_list.append({'id': secondary_id, 'name': f"{secondary_id} {name_zh}"})
        
        # 按ID排序，保证列表顺序一致
        emotion_list.sort(key=lambda x: x['id'])
        return emotion_list

    def get_all_emotion_categories(self) -> Dict[str, Any]:
        """
        获取所有情感分类信息。

        :return: 包含所有情感分类信息的字典
        """
        return EXAMPLE_EMOTION_CATEGORIES

    def get_categories_text(self) -> str:
        """
        获取格式化的情感分类文本，用于提示词。

        :return: 格式化的情感分类文本
        """
        text = "## 情感分类体系：\n\n"
        
        for category_id, category_data in EXAMPLE_EMOTION_CATEGORIES.items():
            text += f"**{category_id}. {category_data.get('name_zh', '')}** ({category_data.get('name_en', '')})\n"
            for secondary in category_data.get('categories', []):
                text += f"- **{secondary.get('id', '')} {secondary.get('name_zh', '')}** ({secondary.get('name_en', '')})\n"
            text += "\n"
        
        return text

    def get_all_categories(self) -> List[str]:
        """
        获取所有情感分类名称。

        :return: 所有情感分类名称列表
        """
        categories = []
        
        for primary_data in EXAMPLE_EMOTION_CATEGORIES.values():
            categories.append(primary_data.get('name_zh', ''))
            for secondary in primary_data.get('categories', []):
                categories.append(secondary.get('name_zh', ''))
                
        return categories

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """
        获取所有情感分类ID和名称的映射。

        :return: 情感分类ID和名称的映射字典
        """
        categories = {}
        
        for primary_id, primary_data in EXAMPLE_EMOTION_CATEGORIES.items():
            categories[primary_id] = primary_data.get('name_zh', '')
            for secondary in primary_data.get('categories', []):
                categories[secondary.get('id', '')] = secondary.get('name_zh', '')
                
        return categories

    def validate_emotion(self, emotion: str) -> bool:
        """
        验证情感标签是否在分类体系中。

        :param emotion: 情感标签名称
        :return: 是否有效
        """
        all_categories = self.get_all_categories()
        return emotion in all_categories

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """
        根据二级类别ID获取一级类别ID。

        :param secondary_id: 二级类别ID
        :return: 对应的一级类别ID，如果未找到则返回None
        """
        for primary_id, primary_data in EXAMPLE_EMOTION_CATEGORIES.items():
            for secondary in primary_data.get('categories', []):
                if secondary.get('id', '') == secondary_id:
                    return primary_id
        return None
