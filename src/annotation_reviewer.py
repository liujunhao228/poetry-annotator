"""
诗词标注校对工具 GUI 逻辑核心

本模块实现了 GUI 界面设计草案 (docs/gui_design_draft.md) 中描述的核心逻辑，
负责处理用户输入、查询数据库、处理数据并为 GUI 界面提供所需的数据结构。
该模块严格遵循逻辑与界面分离的原则，不涉及任何 GUI 组件的创建或操作。

支持多数据库模式，可以切换不同的诗词数据库（如唐诗、宋词等）进行标注校对。

依赖模块:
- src.data: 提供诗词、作者、标注数据的查询功能。
- poetry-annotator-data-visualizer.data_visualizer.db_manager: 提供情感分类体系的查询功能。
"""

import json
import logging
import sys
import os
from typing import Dict, List, Optional, Tuple, Any

# 获取项目根目录并添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.formatters import format_poem_info_for_display, format_sentence_annotations_for_table, SentenceAnnotation
from project.plugins.social_poem_analysis_plugin import SocialPoemAnalysisPlugin # 导入插件

# 初始化日志记录器
logger = logging.getLogger(__name__)

# --- 核心逻辑类 ---


class AnnotationReviewerLogic:
    """
    诗词标注校对工具的逻辑核心类。

    该类封装了所有与数据查询、处理和为GUI提供数据相关的逻辑。
    """

    def __init__(self, social_poem_analysis_plugin: SocialPoemAnalysisPlugin):
        """
        初始化逻辑核心。

        :param social_poem_analysis_plugin: SocialPoemAnalysisPlugin 实例。
        """
        self.social_poem_analysis_plugin = social_poem_analysis_plugin
        self.db_name = "social_poem_analysis" # 插件模式下，数据库名称固定为插件名
        
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        获取当前数据库的统计信息。
        
        :return: 包含统计信息的字典
        """
        try:
            stats = self.social_poem_analysis_plugin.get_statistics()
            return {
                'database_name': self.db_name,
                'total_poems': stats.get('raw_data', {}).get('tables', {}).get('poems', 0),
                'total_authors': stats.get('raw_data', {}).get('tables', {}).get('authors', 0),
                'model_stats': stats.get('annotation', {}).get('tables', {}).get('annotations', 0) # 暂时用annotations表行数表示
            }
        except Exception as e:
            logger.error(f"获取数据库统计信息时出错: {e}")
            return {
                'database_name': self.db_name,
                'total_poems': 0,
                'total_authors': 0,
                'model_stats': {}
            }

    def get_available_models_for_poem(self, poem_id: int) -> List[str]:
        """
        根据诗词ID，查询数据库中该诗词所有可用的标注模型。

        :param poem_id: 数据库中的诗词唯一ID。
        :return: 一个包含模型标识符的列表，例如 ['gemini-2.5-flash', 'gpt-4o']。
                 如果未找到或出错，返回空列表。
        """
        try:
            models = self.social_poem_analysis_plugin.get_annotation_sources_for_poem(poem_id)
            logger.debug(f"诗词ID {poem_id} 可用模型: {models}")
            logger.info(f"诗词ID {poem_id} 找到 {len(models)} 个可用模型")
            return models
        except Exception as e:
            logger.error(f"查询诗词 {poem_id} 可用模型时出错: {e}")
            return []

    def query_poem_and_annotation(self, poem_id: int, model_identifier: str) -> \
        Tuple[Optional[Dict[str, Any]], Optional[List[SentenceAnnotation]]]:
        """
        核心查询函数：根据诗词ID和模型标识符，查询诗词原文和对应的标注结果。

        :param poem_id: 数据库中的诗词唯一ID。
        :param model_identifier: 执行标注的模型标识符。
        :return: 一个元组 (poem_info, sentence_annotations)
                 - poem_info: 包含诗词基本信息的字典，例如
                   {'id': 10191, 'title': '水调歌头', 'author': '苏轼', 'full_text': '...'}
                   如果未找到，为 None。
                 - sentence_annotations: 包含每个句子标注详情的列表，每个元素是一个 SentenceAnnotation 字典。
                   如果未找到或出错，为 None。
        """
        # 1. 查询诗词原文信息
        poem = self.social_poem_analysis_plugin.get_poem_by_id(poem_id)
        if not poem:
            logger.warning(f"未找到ID为 {poem_id} 的诗词。")
            return None, None

        poem_info = {
            'id': poem.id,
            'title': poem.title,
            'author': poem.author,
            'full_text': poem.full_text,
            'paragraphs': poem.paragraphs
        }

        # 2. 查询对应的标注结果
        try:
            raw_annotations = self.social_poem_analysis_plugin.get_annotations_for_poem(poem_id, model_identifier)
            
            if not raw_annotations:
                logger.warning(f"未找到诗词 {poem_id} 由模型 {model_identifier} 生成的标注。")
                return poem_info, None
            
            # 3. 处理标注结果，转换为 SentenceAnnotation 格式
            sentence_annotations = self._process_sentence_annotations(raw_annotations)
            
            logger.info(f"成功查询诗词 {poem_id} 及其 {len(sentence_annotations)} 条句子标注。")
            return poem_info, sentence_annotations

        except Exception as e:
            logger.error(f"查询诗词 {poem_id} 标注信息时出错: {e}")
            return poem_info, None

    def _process_sentence_annotations(self, raw_annotations: List[Dict[str, Any]]) -> List[SentenceAnnotation]:
        """
        内部辅助函数：处理原始的句子标注数据，转换为 SentenceAnnotation 格式。
        插件返回的标注数据结构与旧的 SentenceAnnotation 略有不同，需要适配。

        :param raw_annotations: 从插件获取的原始标注列表。
        :return: 处理后的 SentenceAnnotation 列表。
        """
        processed_annotations = []
        # 获取插件提供的所有分类信息
        categories_data = self.social_poem_analysis_plugin.get_categories()

        for item in raw_annotations:
            # 提取基本信息
            sentence_id = item.get('sentence_uid') # 插件返回的是 sentence_uid
            sentence_text = item.get('sentence_text')
            
            # 社交情感分类信息
            relationship_action_id = item.get('relationship_action')
            emotional_strategy_id = item.get('emotional_strategy')
            communication_scene_ids = item.get('communication_scene', [])
            risk_level_id = item.get('risk_level')
            rationale = item.get('rationale')

            # 构建主情感信息 (这里我们将关系动作作为主情感，次情感为其他)
            primary_emotion_info = {"id": relationship_action_id, "name": self._get_category_name(categories_data, "relationship_action", relationship_action_id)}
            
            # 构建次情感信息列表
            secondary_emotions_info = []
            if emotional_strategy_id:
                secondary_emotions_info.append({"id": emotional_strategy_id, "name": self._get_category_name(categories_data, "emotional_strategy", emotional_strategy_id)})
            for cs_id in communication_scene_ids:
                secondary_emotions_info.append({"id": cs_id, "name": self._get_category_name(categories_data, "communication_scene", cs_id)})
            if risk_level_id:
                secondary_emotions_info.append({"id": risk_level_id, "name": self._get_category_name(categories_data, "risk_level", risk_level_id)})

            processed_annotations.append({
                'sentence_id': sentence_id,
                'sentence_text': sentence_text,
                'primary_emotion': primary_emotion_info,
                'secondary_emotions': secondary_emotions_info,
                'rationale': rationale # 添加 rationale 字段
            })
        
        return processed_annotations

    def _get_category_name(self, categories_data: Dict[str, Any], category_type: str, category_id: str) -> str:
        """辅助函数：根据ID获取分类的中文名称"""
        if not category_id:
            return "N/A"
        category_group = categories_data.get(category_type)
        if category_group:
            for cat in category_group.get('categories', []):
                if cat.get('id') == category_id:
                    return cat.get('name_zh', cat.get('name_en', category_id))
        return category_id # 如果找不到，返回ID本身

    # --- 为GUI组件提供的便捷方法 ---

    def format_poem_info_for_display(self, poem_info: Dict[str, Any]) -> Dict[str, str]:
        """
        将诗词信息字典格式化为适合在GUI标签上显示的键值对。

        :param poem_info: 由 query_poem_and_annotation 返回的 poem_info 字典。
        :return: 一个字典，键为显示标签，值为对应的文本内容。
        """
        return format_poem_info_for_display(poem_info)

    def format_sentence_annotations_for_table(self, sentence_annotations: List[SentenceAnnotation]) -> \
        List[Dict[str, str]]:
        """
        将句子标注列表格式化为适合在GUI表格(Treeview)中显示的数据。

        :param sentence_annotations: 由 query_poem_and_annotation 返回的 sentence_annotations 列表。
        :return: 一个字典列表，每个字典代表表格中的一行。
        """
        # 这里的 SentenceAnnotation 结构已经包含了 rationale，需要调整 formatters.py
        # 或者在这里进行适配，暂时先在这里适配
        table_data = []
        for ann in sentence_annotations:
            primary_display = ann['primary_emotion']['name'] if ann['primary_emotion'] else 'N/A'
            secondary_names = [e['name'] for e in ann['secondary_emotions']]
            secondary_display = ', '.join(secondary_names) if secondary_names else '无'

            table_data.append({
                "句子ID": ann['sentence_id'],
                "句子文本": ann['sentence_text'],
                "主情感": primary_display,
                "次情感": secondary_display,
                "理由": ann.get('rationale', '无')
            })
        return table_data

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。
        现在将返回社交情感分类。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
                      此参数在社交情感分类中可能不直接适用，但保留接口一致性。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        categories_data = self.social_poem_analysis_plugin.get_categories()
        full_list = []
        for category_type, data in categories_data.items():
            for cat in data.get('categories', []):
                full_list.append({
                    'id': cat['id'],
                    'name': f"{cat['id']} {cat.get('name_zh', cat.get('name_en', ''))}"
                })
        return full_list
        
    def get_all_emotion_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有情感分类信息。
        现在将返回社交情感分类。
        
        :return: 包含所有情感分类信息的字典
        """
        return self.social_poem_analysis_plugin.get_categories()
