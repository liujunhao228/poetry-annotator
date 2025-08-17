"""
诗词标注校对工具 GUI 逻辑核心

本模块实现了 GUI 界面设计草案 (docs/gui_design_draft.md) 中描述的核心逻辑，
负责处理用户输入、查询数据库、处理数据并为 GUI 界面提供所需的数据结构。
该模块严格遵循逻辑与界面分离的原则，不涉及任何 GUI 组件的创建或操作。

支持多数据库模式，可以切换不同的诗词数据库（如唐诗、宋词等）进行标注校对。

依赖模块:
- src.data_manager: 提供诗词、作者、标注数据的查询功能。
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

# 添加 data-visualizer 目录到 Python 路径
data_visualizer_path = os.path.join(project_root, 'poetry-annotator-data-visualizer')
if data_visualizer_path not in sys.path:
    sys.path.insert(0, data_visualizer_path)

from src.data_manager import get_data_manager
from src.config_manager import config_manager
from src.emotion_classifier import EmotionClassifier
from src.formatters import format_poem_info_for_display, format_sentence_annotations_for_table, SentenceAnnotation
from data_visualizer.db_manager import DBManager

# 初始化日志记录器
logger = logging.getLogger(__name__)

# --- 核心逻辑类 ---


class AnnotationReviewerLogic:
    """
    诗词标注校对工具的逻辑核心类。

    该类封装了所有与数据查询、处理和为GUI提供数据相关的逻辑。
    """

    def __init__(self, db_name: str = "default"):
        """
        初始化逻辑核心。

        :param db_name: 要连接的数据库名称，默认为 "default"。
        """
        self.db_name = db_name
        self.data_manager = get_data_manager(db_name)
        # 使用 data_visualizer 的 DBManager 来查询情感分类体系
        # 注意：这里假设两个 DBManager 实例指向同一个数据库文件
        # 或者情感分类体系在 data_visualizer 的数据库中是独立且同步的
        # 在实际应用中，可能需要更复杂的同步机制或共享同一个DB实例
        self.emotion_db_manager = DBManager(self.data_manager.db_path)
        self.emotion_classifier = EmotionClassifier(self.emotion_db_manager)
        
    @classmethod
    def get_available_databases(cls) -> Dict[str, str]:
        """
        获取所有可用的数据库配置。
        
        :return: 一个字典，key为数据库名称，value为数据库路径
        """
        db_config = config_manager.get_database_config()
        
        # 处理新的多数据库配置
        if 'db_paths' in db_config:
            return db_config['db_paths']
        
        # 回退到旧的单数据库配置
        if 'db_path' in db_config:
            return {"default": db_config['db_path']}
        
        # 如果都没有配置，则返回空字典
        return {}
        
    @classmethod
    def create_for_database(cls, db_name: str = "default"):
        """
        为指定数据库创建 AnnotationReviewerLogic 实例。
        
        :param db_name: 数据库名称
        :return: AnnotationReviewerLogic 实例
        """
        return cls(db_name)
        
    def get_current_database_name(self) -> str:
        """
        获取当前使用的数据库名称。
        
        :return: 数据库名称
        """
        return self.db_name
        
    def switch_database(self, db_name: str):
        """
        切换到指定的数据库。
        
        :param db_name: 要切换到的数据库名称
        """
        # 重新初始化数据管理器
        self.db_name = db_name
        self.data_manager = get_data_manager(db_name)
        # 重新初始化情感数据库管理器
        self.emotion_db_manager = DBManager(self.data_manager.db_path)
        # 重新加载情感分类
        self.emotion_classifier = EmotionClassifier(self.emotion_db_manager)
        
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        获取当前数据库的统计信息。
        
        :return: 包含统计信息的字典
        """
        try:
            stats = self.data_manager.get_statistics()
            return {
                'database_name': self.db_name,
                'total_poems': stats.get('total_poems', 0),
                'total_authors': stats.get('total_authors', 0),
                'model_stats': stats.get('stats_by_model', {})
            }
        except Exception as e:
            logger.error(f"获取数据库统计信息时出错: {e}")
            return {
                'database_name': self.db_name,
                'total_poems': 0,
                'total_authors': 0,
                'model_stats': {}
            }

    def _load_emotion_categories(self):
        """
        从数据库加载情感分类体系到内存，构建便于查询的映射结构。
        """
        try:
            df = self.emotion_db_manager.get_all_emotion_categories()
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

    def get_available_models_for_poem(self, poem_id: int) -> List[str]:
        """
        根据诗词ID，查询数据库中该诗词所有可用的标注模型。

        :param poem_id: 数据库中的诗词唯一ID。
        :return: 一个包含模型标识符的列表，例如 ['gemini-2.5-flash', 'gpt-4o']。
                 如果未找到或出错，返回空列表。
        """
        try:
            # 查询特定 poem_id 的所有标注记录
            query = """
                SELECT DISTINCT model_identifier
                FROM annotations
                WHERE poem_id = ? AND status = 'completed'
            """
            rows = self.data_manager.db_adapter.execute_query(query, (poem_id,))
            models = [row[0] for row in rows]
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
        poem_info = self.data_manager.get_poem_by_id(poem_id)
        if not poem_info:
            logger.warning(f"未找到ID为 {poem_id} 的诗词。")
            return None, None

        # 2. 查询对应的标注结果
        try:
            query = """
                SELECT annotation_result
                FROM annotations
                WHERE poem_id = ? AND model_identifier = ? AND status = 'completed'
            """
            rows = self.data_manager.db_adapter.execute_query(query, (poem_id, model_identifier))
            
            if not rows:
                logger.warning(f"未找到诗词 {poem_id} 由模型 {model_identifier} 生成的 completed 标注。")
                return poem_info, None
            
            annotation_result_str = rows[0][0]
            if not annotation_result_str:
                logger.warning(f"诗词 {poem_id} 由模型 {model_identifier} 生成的标注结果为空。")
                return poem_info, None

            # 3. 解析并处理标注结果
            raw_annotations = json.loads(annotation_result_str)
            sentence_annotations = self._process_sentence_annotations(raw_annotations)
            
            logger.info(f"成功查询诗词 {poem_id} 及其 {len(sentence_annotations)} 条句子标注。")
            return poem_info, sentence_annotations

        except json.JSONDecodeError as e:
            logger.error(f"解析诗词 {poem_id} 标注结果JSON时出错: {e}")
            return poem_info, None
        except Exception as e:
            logger.error(f"查询诗词 {poem_id} 标注信息时出错: {e}")
            return poem_info, None

    def _process_sentence_annotations(self, raw_annotations: List[Dict[str, Any]]) -> List[SentenceAnnotation]:
        """
        内部辅助函数：处理原始的句子标注数据，丰富情感信息。

        :param raw_annotations: 从 annotation_result JSON 解析出的原始列表。
        :return: 处理后的 SentenceAnnotation 列表。
        """
        processed_annotations = []
        for item in raw_annotations:
            # 提取基本信息
            sentence_id = item.get('sentence_id')
            sentence_text = item.get('sentence_text')
            primary_emotion_id = item.get('primary_emotion')
            secondary_emotion_ids = item.get('secondary_emotions', [])

            # 构建主情感信息
            primary_emotion_info = self.emotion_classifier.get_emotion_display_info(primary_emotion_id)

            # 构建次情感信息列表
            secondary_emotions_info = [
                self.emotion_classifier.get_emotion_display_info(e_id) for e_id in secondary_emotion_ids
            ]

            processed_annotations.append({
                'sentence_id': sentence_id,
                'sentence_text': sentence_text,
                'primary_emotion': primary_emotion_info,
                'secondary_emotions': secondary_emotions_info
            })
        
        return processed_annotations

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
        return format_sentence_annotations_for_table(sentence_annotations)

    def get_full_emotion_list_for_selection(self, level: int = 2) -> List[Dict[str, str]]:
        """
        获取完整的情感分类列表，供GUI下拉选择框使用。

        :param level: 指定要获取的情感分类层级 (1: 一级分类, 2: 二级分类)。默认为2。
        :return: 一个字典列表，每个字典包含 'id' 和 'name' 键。
        """
        return self.emotion_classifier.get_full_emotion_list_for_selection(level)
        
    def get_all_emotion_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有情感分类信息。
        
        :return: 包含所有情感分类信息的字典
        """
        return self.emotion_classifier.get_all_emotion_categories()
        
    def switch_database(self, db_name: str):
        """
        切换到指定的数据库。
        
        :param db_name: 要切换到的数据库名称
        """
        # 重新初始化数据管理器
        self.db_name = db_name
        self.data_manager = get_data_manager(db_name)
        # 重新初始化情感数据库管理器
        self.emotion_db_manager = DBManager(self.data_manager.db_path)
        # 重新加载情感分类
        self.emotion_classifier = EmotionClassifier(self.emotion_db_manager)