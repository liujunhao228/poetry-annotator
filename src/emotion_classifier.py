"""
情感分类器模块

本模块提供情感分类体系的查询和格式化功能，现已重构为插件化架构。
"""

import logging
from typing import Dict, Any, List, Optional
from src.component_system import Component, ComponentType, get_component_system
from src.data.label_parser_plugin_interface import LabelParserPlugin

# 初始化日志记录器
logger = logging.getLogger(__name__)

# --- 核心数据结构定义 ---

# 用于存储情感分类的内部表示
# key: emotion_id (e.g., "01.05")
# value: {"name_zh": "愉悦", "name_en": "Joy", "parent_id": "01", "level": 2}
EmotionCategoryMap = Dict[str, Dict[str, Any]]


class EmotionClassifier(Component):
    """
    情感分类器类，已重构为通过插件系统获取情感分类信息。
    """

    def __init__(self, project_root=None):
        """
        初始化情感分类器。

        :param project_root: 项目根目录路径
        """
        super().__init__(ComponentType.LABEL_PARSER)  # 设置组件类型为标签解析器
        self.project_root = project_root
        self._emotion_plugin: Optional[LabelParserPlugin] = None
        self._initialize_emotion_plugin()

    def _initialize_emotion_plugin(self):
        """
        初始化情感分类插件。
        """
        try:
            # 通过组件系统获取情感分类插件
            component_system = get_component_system(self.project_root)
            self._emotion_plugin = component_system.get_component(ComponentType.LABEL_PARSER)
            logger.info("情感分类插件初始化成功")
        except Exception as e:
            logger.error(f"情感分类插件初始化失败: {e}")
            self._emotion_plugin = None

    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return {'id': emotion_id or '', 'name': f"{emotion_id or ''} 未知情感"}
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_emotion_display_info'):
            return self._emotion_plugin.get_emotion_display_info(emotion_id)
        
        # 否则使用默认实现
        categories = self._emotion_plugin.get_categories()
        
        # 在插件提供的分类中查找指定ID的情感
        for primary_id, primary_data in categories.items():
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
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return []
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_full_emotion_list_for_selection'):
            return self._emotion_plugin.get_full_emotion_list_for_selection(level)
        
        # 否则使用默认实现
        emotion_list = []
        categories = self._emotion_plugin.get_categories()
        
        # 根据层级获取分类列表
        if level == 1:
            # 获取一级分类
            for primary_id, primary_data in categories.items():
                name_zh = primary_data.get('name_zh', '')
                emotion_list.append({'id': primary_id, 'name': f"{primary_id} {name_zh}"})
        elif level == 2:
            # 获取二级分类
            for primary_data in categories.values():
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
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return {}
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_all_emotion_categories'):
            return self._emotion_plugin.get_all_emotion_categories()
            
        return self._emotion_plugin.get_categories()

    def get_categories_text(self) -> str:
        """
        获取格式化的情感分类文本，用于提示词。

        :return: 格式化的情感分类文本
        """
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return "## 情感分类体系：\n\n未加载情感分类信息。\n"
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_categories_text'):
            return self._emotion_plugin.get_categories_text()
            
        text = "## 情感分类体系：\n\n"
        categories = self._emotion_plugin.get_categories()
        
        for category_id, category_data in categories.items():
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
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return []
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_all_categories'):
            return self._emotion_plugin.get_all_categories()
            
        categories = []
        category_data = self._emotion_plugin.get_categories()
        
        for primary_data in category_data.values():
            categories.append(primary_data.get('name_zh', ''))
            for secondary in primary_data.get('categories', []):
                categories.append(secondary.get('name_zh', ''))
                
        return categories

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """
        获取所有情感分类ID和名称的映射。

        :return: 情感分类ID和名称的映射字典
        """
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return {}
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_all_categories_with_ids'):
            return self._emotion_plugin.get_all_categories_with_ids()
            
        categories = {}
        category_data = self._emotion_plugin.get_categories()
        
        for primary_id, primary_data in category_data.items():
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
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return False
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'validate_emotion'):
            return self._emotion_plugin.validate_emotion(emotion)
            
        all_categories = self.get_all_categories()
        return emotion in all_categories

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """
        根据二级类别ID获取一级类别ID。

        :param secondary_id: 二级类别ID
        :return: 对应的一级类别ID，如果未找到则返回None
        """
        # 直接委托给插件处理
        if not self._emotion_plugin:
            return None
            
        # 检查插件是否实现了此方法，如果实现了则直接调用
        if hasattr(self._emotion_plugin, 'get_primary_category'):
            return self._emotion_plugin.get_primary_category(secondary_id)
            
        categories = self._emotion_plugin.get_categories()
        
        for primary_id, primary_data in categories.items():
            for secondary in primary_data.get('categories', []):
                if secondary.get('id', '') == secondary_id:
                    return primary_id
        return None