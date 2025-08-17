"""
情感分类器模块

本模块负责处理情感分类体系的加载、查询和格式化。
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os

# 获取项目根目录并添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加 data-visualizer 目录到 Python 路径
data_visualizer_path = os.path.join(project_root, 'poetry-annotator-data-visualizer')
if data_visualizer_path not in sys.path:
    sys.path.insert(0, data_visualizer_path)

from data_visualizer.db_manager import DBManager

# 初始化日志记录器
logger = logging.getLogger(__name__)

# --- 核心数据结构定义 ---

# 用于存储情感分类的内部表示
# key: emotion_id (e.g., "01.05")
# value: {"name_zh": "愉悦", "name_en": "Joy", "parent_id": "01", "level": 2}
EmotionCategoryMap = Dict[str, Dict[str, Any]]


class EmotionClassifier:
    """
    情感分类器类，负责管理情感分类体系。
    """

    def __init__(self, db_manager: DBManager):
        """
        初始化情感分类器。

        :param db_manager: 数据库管理器实例，用于查询情感分类数据。
        """
        self.db_manager = db_manager
        self._emotion_categories: Optional[EmotionCategoryMap] = None
        self._load_emotion_categories()

    def _load_emotion_categories(self):
        """
        从数据库加载情感分类体系到内存，构建便于查询的映射结构。
        """
        try:
            df = self.db_manager.get_all_emotion_categories()
            self._emotion_categories = {}
            for _, row in df.iterrows():
                self._emotion_categories[row['id']] = {
                    'name_zh': row['name_zh'],
                    'name_en': row['name_en'],
                    'parent_id': row['parent_id'],
                    'level': row['level']
                }
            logger.info(f"成功加载 {len(self._emotion_categories)} 个情感分类。")
        except Exception as e:
            logger.error(f"加载情感分类体系失败: {e}")
            self._emotion_categories = {}

    def get_emotion_display_info(self, emotion_id: str) -> Dict[str, str]:
        """
        根据情感ID获取用于界面显示的信息。

        :param emotion_id: 情感的唯一ID，例如 "01.05"。
        :return: 包含 'id' 和 'name' 的字典，例如 {'id': '01.05', 'name': '01.05 愉悦'}。
                 如果ID无效，则 'name' 为 '未知情感'。
        """
        if not emotion_id or not self._emotion_categories:
            return {'id': emotion_id or '', 'name': f"{emotion_id or ''} 未知情感"}

        emotion_info = self._emotion_categories.get(emotion_id)
        if not emotion_info:
            return {'id': emotion_id, 'name': f"{emotion_id} 未知情感"}

        # 格式化显示名称，例如 "01.05 愉悦"
        display_name = f"{emotion_id} {emotion_info['name_zh']}"
        return {'id': emotion_id, 'name': display_name}

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        if not self._emotion_categories:
            return []

        emotion_list = []
        for e_id, e_info in self._emotion_categories.items():
            if e_info['level'] == level:
                display_name = f"{e_id} {e_info['name_zh']}"
                emotion_list.append({'id': e_id, 'name': display_name})

        # 按ID排序，保证列表顺序一致
        emotion_list.sort(key=lambda x: x['id'])
        return emotion_list

    def get_all_emotion_categories(self) -> EmotionCategoryMap:
        """
        获取所有情感分类信息。

        :return: 包含所有情感分类信息的字典
        """
        return self._emotion_categories.copy() if self._emotion_categories else {}