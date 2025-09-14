"""
诗词标注数据导出器

该模块提供功能，用于查询指定诗词的所有模型标注数据，
将其处理为包含中文情感名称的表格形式。
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any
import sys
import os
import json

# 获取项目根目录并添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加 data-visualizer 目录到 Python 路径
data_visualizer_path = os.path.join(project_root, 'poetry-annotator-data-visualizer')
if data_visualizer_path not in sys.path:
    sys.path.insert(0, data_visualizer_path)

from src.data import get_data_manager
from data_visualizer.db_manager import DBManager

# 初始化日志记录器
logger = logging.getLogger(__name__)


class AnnotationDataExporter:
    """
    诗词标注数据导出器类，负责查询和格式化标注数据。
    """
    
    def __init__(self, output_dir: str, source_dir: str):
        """
        初始化导出器。

        :param output_dir: 项目的输出目录，用于派生项目名称和数据库路径。
        :param source_dir: 数据源目录。
        """
        self.output_dir = output_dir
        self.source_dir = source_dir
        self.data_manager = get_data_manager(output_dir=self.output_dir, source_dir=self.source_dir)
        
        # 获取情感数据库路径
        emotion_db_path = self.data_manager.separate_db_paths.get('emotion')
        if not emotion_db_path:
            raise ValueError("无法获取情感数据库路径。")
        
        # 使用 data_visualizer 的 DBManager 来查询情感分类体系
        self.emotion_db_manager = DBManager(emotion_db_path)
        self._emotion_categories: Optional[Dict[str, Dict[str, Any]]] = None
        self._load_emotion_categories()
        
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
    
    def _get_emotion_name(self, emotion_id: str) -> str:
        """
        根据情感ID获取中文名称。

        :param emotion_id: 情感的唯一ID。
        :return: 情感的中文名称，如果未找到则返回ID本身。
        """
        if not emotion_id or not self._emotion_categories:
            return emotion_id or ''
        
        emotion_info = self._emotion_categories.get(emotion_id)
        if not emotion_info:
            return emotion_id
        
        return emotion_info['name_zh']
    
    def get_annotations_for_poem(self, poem_id: int, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取指定诗词ID的所有模型的标注数据，并处理为表格形式。

        :param poem_id: 诗词的唯一ID。
        :param columns: 可选，指定要包含在返回DataFrame中的列名列表。
                        如果为None，则包含所有列。
        :return: 包含所有模型标注数据的DataFrame，情感ID已转换为中文名称。
        """
        try:
            # 1. 查询诗词原文信息
            poem_info = self.data_manager.get_poem_by_id(poem_id)
            if not poem_info:
                logger.warning(f"未找到ID为 {poem_id} 的诗词。")
                return pd.DataFrame()
import sqlite3 # Add this import

class AnnotationDataExporter:
    """
    诗词标注数据导出器类，负责查询和格式化标注数据。
    """
    
    def __init__(self, output_dir: str, source_dir: str):
        """
        初始化导出器。

        :param output_dir: 项目的输出目录，用于派生项目名称和数据库路径。
        :param source_dir: 数据源目录。
        """
        self.output_dir = output_dir
        self.source_dir = source_dir
        self.data_manager = get_data_manager(output_dir=self.output_dir, source_dir=self.source_dir)
        
        # 获取情感数据库路径
        emotion_db_path = self.data_manager.separate_db_paths.get('emotion')
        if not emotion_db_path:
            raise ValueError("无法获取情感数据库路径。")
        
        # 使用 data_visualizer 的 DBManager 来查询情感分类体系
        self.emotion_db_manager = DBManager(emotion_db_path)
        self._emotion_categories: Optional[Dict[str, Dict[str, Any]]] = None
        self._load_emotion_categories()
        
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
    
    def _get_emotion_name(self, emotion_id: str) -> str:
        """
        根据情感ID获取中文名称。

        :param emotion_id: 情感的唯一ID。
        :return: 情感的中文名称，如果未找到则返回ID本身。
        """
        if not emotion_id or not self._emotion_categories:
            return emotion_id or ''
        
        emotion_info = self._emotion_categories.get(emotion_id)
        if not emotion_info:
            return emotion_id
        
        return emotion_info['name_zh']
    
    def get_annotations_for_poem(self, poem_id: int, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取指定诗词ID的所有模型的标注数据，并处理为表格形式。

        :param poem_id: 诗词的唯一ID。
        :param columns: 可选，指定要包含在返回DataFrame中的列名列表。
                        如果为None，则包含所有列。
        :return: 包含所有模型标注数据的DataFrame，情感ID已转换为中文名称。
        """
        try:
            # 1. 查询诗词原文信息
            poem_info = self.data_manager.get_poem_by_id(poem_id)
            if not poem_info:
                logger.warning(f"未找到ID为 {poem_id} 的诗词。")
                return pd.DataFrame()
            
            # 获取标注数据库路径
            annotation_db_path = self.data_manager.separate_db_paths.get('annotation')
            if not annotation_db_path:
                raise ValueError("无法获取标注数据库路径。")
            
            # 获取数据库连接
            conn = sqlite3.connect(annotation_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 2. 查询该诗词的所有completed标注记录
            query = """
                SELECT id, poem_id, model_identifier, annotation_result, created_at
                FROM annotations
                WHERE poem_id = ? AND status = 'completed'
            """
            cursor.execute(query, (poem_id,))
            rows = cursor.fetchall()
            
            if not rows:
                logger.info(f"诗词 {poem_id} 没有找到任何completed的标注记录。")
                return pd.DataFrame()
            
            # 3. 处理每条标注记录
            all_sentence_data = []
            
            for row in rows:
                annotation_id = row[0]
                model_identifier = row[2]
                annotation_result_str = row[3]
                created_at = row[4]
                
                if not annotation_result_str:
                    logger.warning(f"标注记录 {annotation_id} 的结果为空。")
                    continue
                
                try:
                    raw_annotations = json.loads(annotation_result_str)
                except json.JSONDecodeError as e:
                    logger.error(f"解析标注记录 {annotation_id} 的JSON时出错: {e}")
                    continue
                
                # 4. 展开每个句子的标注信息
                for item in raw_annotations:
                    sentence_id = item.get('sentence_id')
                    sentence_text = item.get('sentence_text')
                    primary_emotion_id = item.get('primary_emotion')
                    secondary_emotion_ids = item.get('secondary_emotions', [])
                    
                    # 转换情感ID为中文名称
                    primary_emotion_name = self._get_emotion_name(primary_emotion_id)
                    secondary_emotion_names = [self._get_emotion_name(e_id) for e_id in secondary_emotion_ids]
                    
                    # 构建一行数据
                    sentence_data = {
                        'poem_id': poem_id,
                        'model_identifier': model_identifier,
                        'sentence_id': sentence_id,
                        'sentence_text': sentence_text,
                        'primary_emotion_id': primary_emotion_id,
                        'primary_emotion_name': primary_emotion_name,
                        'secondary_emotion_ids': ';'.join(secondary_emotion_ids),
                        'secondary_emotion_names': ';'.join(secondary_emotion_names),
                        'annotation_created_at': created_at
                    }
                    all_sentence_data.append(sentence_data)
            
            # 5. 转换为DataFrame并返回
            if not all_sentence_data:
                logger.info(f"诗词 {poem_id} 的标注数据处理后为空。")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_sentence_data)
            
            # 6. 根据columns参数筛选列
            if columns is not None:
                # 确保请求的列都存在于DataFrame中
                available_columns = [col for col in columns if col in df.columns]
                missing_columns = set(columns) - set(available_columns)
                if missing_columns:
                    logger.warning(f"请求的列 {list(missing_columns)} 在数据中不存在，将被忽略。")
                df = df[available_columns] if available_columns else pd.DataFrame()
            
            logger.info(f"成功导出诗词 {poem_id} 的标注数据，共 {len(df)} 条句子记录，来自 {len(rows)} 个模型。")
            return df
            
        except Exception as e:
            logger.error(f"导出诗词 {poem_id} 的标注数据时出错: {e}")
            return pd.DataFrame()


# --- 便捷函数 ---

def export_annotations_to_csv(poem_id: int, output_file: str, output_dir: str, source_dir: str) -> bool:
    """
    便捷函数：导出指定诗词的所有模型标注数据到CSV文件。

    :param poem_id: 诗词的唯一ID。
    :param output_file: 输出CSV文件的路径。
    :param output_dir: 项目的输出目录，用于派生项目名称和数据库路径。
    :param source_dir: 数据源目录。
    :return: 导出是否成功。
    """
    try:
        exporter = AnnotationDataExporter(output_dir=output_dir, source_dir=source_dir)
        df = exporter.get_annotations_for_poem(poem_id)
        
        if df.empty:
            logger.warning(f"没有数据可导出到 {output_file}。")
            return False
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"成功导出诗词 {poem_id} 的标注数据到 {output_file}。")
        return True
    except Exception as e:
        logger.error(f"导出诗词 {poem_id} 的标注数据到CSV时出错: {e}")
        return False


def export_annotations_to_excel(poem_id: int, output_file: str, output_dir: str, source_dir: str) -> bool:
    """
    便捷函数：导出指定诗词的所有模型标注数据到Excel文件。

    :param poem_id: 诗词的唯一ID。
    :param output_file: 输出Excel文件的路径。
    :param output_dir: 项目的输出目录，用于派生项目名称和数据库路径。
    :param source_dir: 数据源目录。
    :return: 导出是否成功。
    """
    try:
        exporter = AnnotationDataExporter(output_dir=output_dir, source_dir=source_dir)
        df = exporter.get_annotations_for_poem(poem_id)
        
        if df.empty:
            logger.warning(f"没有数据可导出到 {output_file}。")
            return False
        
        df.to_excel(output_file, index=False)
        logger.info(f"成功导出诗词 {poem_id} 的标注数据到 {output_file}。")
        return True
    except Exception as e:
        logger.error(f"导出诗词 {poem_id} 的标注数据到Excel时出错: {e}")
        return False
