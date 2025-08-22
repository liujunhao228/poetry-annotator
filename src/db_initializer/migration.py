"""
数据库迁移模块
负责将数据从旧的合并数据库迁移到新的分离数据库结构
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..config import config_manager
from ..data.adapter import get_database_adapter
from ..data.separate_databases import get_separate_db_manager

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """数据库迁移器，负责将数据从旧结构迁移到新结构"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_configs = self._get_database_configs()

    def _get_database_configs(self) -> Dict[str, str]:
        """获取所有数据库配置"""
        db_config = config_manager.get_effective_database_config()

        # 处理新的多数据库配置
        if 'db_paths' in db_config:
            db_paths = db_config['db_paths']
            # 确保使用绝对路径
            resolved_paths = {}
            for name, path in db_paths.items():
                if not Path(path).is_absolute():
                    resolved_paths[name] = str(Path(path).resolve())
                else:
                    resolved_paths[name] = path
            return resolved_paths
        # 回退到旧的单数据库配置
        elif 'db_path' in db_config:
            path = db_config['db_path']
            if not Path(path).is_absolute():
                path = str(Path(path).resolve())
            return {"default": path}
        else:
            raise ValueError("配置文件中未找到数据库路径配置。")

    def migrate_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """迁移所有数据库的数据到分离结构"""
        results = {}

        for db_name, main_db_path in self.db_configs.items():
            try:
                self.logger.info(f"开始迁移数据库 {db_name} ({main_db_path}) 的数据到分离结构")
                result = self.migrate_database(db_name, main_db_path)
                results[db_name] = result
                self.logger.info(f"数据库 {db_name} 数据迁移完成")
            except Exception as e:
                self.logger.error(f"迁移数据库 {db_name} 数据失败: {e}")
                results[db_name] = {"error": str(e)}

        return results

    def migrate_database(self, db_name: str, main_db_path: str) -> Dict[str, Any]:
        """迁移单个数据库的数据到分离结构"""
        # 检查主数据库是否存在
        if not Path(main_db_path).exists():
            return {
                "status": "skipped",
                "message": f"主数据库文件不存在: {main_db_path}"
            }

        # 获取分离数据库管理器
        separate_db_manager = get_separate_db_manager(main_db_name=db_name)

        try:
            # 迁移原始数据
            raw_data_result = self._migrate_raw_data(main_db_path, separate_db_manager)
            
            # 迁移标注数据
            annotation_result = self._migrate_annotation_data(main_db_path, separate_db_manager)
            
            # 迁移情感分类数据
            emotion_result = self._migrate_emotion_data(main_db_path, separate_db_manager)

            return {
                "status": "success",
                "message": f"数据库 {db_name} 数据迁移完成",
                "details": {
                    "raw_data": raw_data_result,
                    "annotation": annotation_result,
                    "emotion": emotion_result
                }
            }
        except Exception as e:
            self.logger.error(f"迁移数据库 {db_name} 数据时出错: {e}")
            raise

    def _migrate_raw_data(self, main_db_path: str, separate_db_manager) -> Dict[str, Any]:
        """迁移原始数据（诗词和作者）到分离的原始数据数据库"""
        try:
            # 连接主数据库和分离的原始数据数据库
            main_adapter = get_database_adapter('sqlite', main_db_path)
            raw_data_adapter = separate_db_manager.raw_data_db

            # 确保数据库连接是打开的
            raw_data_conn = raw_data_adapter.connect()
            
            # 开始事务
            raw_data_conn.execute("BEGIN")

            # 迁移作者数据
            author_count = 0
            try:
                # 从主数据库查询所有作者
                authors = main_adapter.execute_query("SELECT name, description, short_description, created_at FROM authors")
                if authors:
                    # 清空现有数据
                    raw_data_conn.execute("DELETE FROM authors")
                    # 批量插入到分离的原始数据数据库
                    insert_data = [(author[0], author[1], author[2], author[3]) for author in authors]
                    raw_data_conn.executemany('''
                        INSERT INTO authors (name, description, short_description, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', insert_data)
                    author_count = len(insert_data)
                    self.logger.info(f"迁移了 {author_count} 位作者到分离的原始数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移作者数据时出错: {e}")

            # 迁移诗词数据
            poem_count = 0
            try:
                # 从主数据库查询所有诗词
                poems = main_adapter.execute_query("""
                    SELECT id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at 
                    FROM poems
                """)
                if poems:
                    # 清空现有数据
                    raw_data_conn.execute("DELETE FROM poems")
                    # 批量插入到分离的原始数据数据库
                    insert_data = [(poem[0], poem[1], poem[2], poem[3], poem[4], poem[5], poem[6], poem[7], poem[8]) for poem in poems]
                    raw_data_conn.executemany('''
                        INSERT INTO poems (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    poem_count = len(insert_data)
                    self.logger.info(f"迁移了 {poem_count} 首诗词到分离的原始数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移诗词数据时出错: {e}")

            # 提交事务
            raw_data_conn.commit()

            return {
                "status": "success",
                "authors_migrated": author_count,
                "poems_migrated": poem_count
            }
        except Exception as e:
            # 回滚事务
            try:
                raw_data_adapter.connect().rollback()
            except:
                pass
            self.logger.error(f"迁移原始数据时出错: {e}")
            raise

    def _migrate_annotation_data(self, main_db_path: str, separate_db_manager) -> Dict[str, Any]:
        """迁移标注数据到分离的标注数据数据库"""
        try:
            # 连接主数据库和分离的标注数据数据库
            main_adapter = get_database_adapter('sqlite', main_db_path)
            annotation_adapter = separate_db_manager.annotation_db

            # 确保数据库连接是打开的
            annotation_conn = annotation_adapter.connect()
            
            # 开始事务
            annotation_conn.execute("BEGIN")

            # 迁移标注数据
            annotation_count = 0
            try:
                # 从主数据库查询所有标注
                annotations = main_adapter.execute_query("""
                    SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at 
                    FROM annotations
                """)
                if annotations:
                    # 清空现有数据
                    annotation_conn.execute("DELETE FROM annotations")
                    # 批量插入到分离的标注数据数据库
                    insert_data = [(anno[0], anno[1], anno[2], anno[3], anno[4], anno[5], anno[6], anno[7]) for anno in annotations]
                    annotation_conn.executemany('''
                        INSERT INTO annotations (id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    annotation_count = len(insert_data)
                    self.logger.info(f"迁移了 {annotation_count} 条标注到分离的标注数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移标注数据时出错: {e}")

            # 迁移句子标注数据
            sentence_annotation_count = 0
            try:
                # 从主数据库查询所有句子标注
                sentence_annotations = main_adapter.execute_query("""
                    SELECT id, annotation_id, poem_id, sentence_uid, sentence_text 
                    FROM sentence_annotations
                """)
                if sentence_annotations:
                    # 清空现有数据
                    annotation_conn.execute("DELETE FROM sentence_annotations")
                    # 批量插入到分离的标注数据数据库
                    insert_data = [(sa[0], sa[1], sa[2], sa[3], sa[4]) for sa in sentence_annotations]
                    annotation_conn.executemany('''
                        INSERT INTO sentence_annotations (id, annotation_id, poem_id, sentence_uid, sentence_text)
                        VALUES (?, ?, ?, ?, ?)
                    ''', insert_data)
                    sentence_annotation_count = len(insert_data)
                    self.logger.info(f"迁移了 {sentence_annotation_count} 条句子标注到分离的标注数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移句子标注数据时出错: {e}")

            # 迁移句子情感链接数据
            sentence_emotion_link_count = 0
            try:
                # 从主数据库查询所有句子情感链接
                sentence_emotion_links = main_adapter.execute_query("""
                    SELECT sentence_annotation_id, emotion_id, is_primary 
                    FROM sentence_emotion_links
                """)
                if sentence_emotion_links:
                    # 清空现有数据
                    annotation_conn.execute("DELETE FROM sentence_emotion_links")
                    # 批量插入到分离的标注数据数据库
                    insert_data = [(sel[0], sel[1], sel[2]) for sel in sentence_emotion_links]
                    annotation_conn.executemany('''
                        INSERT INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary)
                        VALUES (?, ?, ?)
                    ''', insert_data)
                    sentence_emotion_link_count = len(insert_data)
                    self.logger.info(f"迁移了 {sentence_emotion_link_count} 条句子情感链接到分离的标注数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移句子情感链接数据时出错: {e}")

            # 提交事务
            annotation_conn.commit()

            return {
                "status": "success",
                "annotations_migrated": annotation_count,
                "sentence_annotations_migrated": sentence_annotation_count,
                "sentence_emotion_links_migrated": sentence_emotion_link_count
            }
        except Exception as e:
            # 回滚事务
            try:
                annotation_adapter.connect().rollback()
            except:
                pass
            self.logger.error(f"迁移标注数据时出错: {e}")
            raise

    def _migrate_emotion_data(self, main_db_path: str, separate_db_manager) -> Dict[str, Any]:
        """迁移情感分类数据到分离的情感数据数据库"""
        try:
            # 连接主数据库和分离的情感数据数据库
            main_adapter = get_database_adapter('sqlite', main_db_path)
            emotion_adapter = separate_db_manager.emotion_db

            # 确保数据库连接是打开的
            emotion_conn = emotion_adapter.connect()
            
            # 开始事务
            emotion_conn.execute("BEGIN")

            # 迁移情感分类数据
            emotion_count = 0
            try:
                # 从主数据库查询所有情感分类
                emotions = main_adapter.execute_query("""
                    SELECT id, name_zh, name_en, parent_id, level 
                    FROM emotion_categories
                """)
                if emotions:
                    # 清空现有数据
                    emotion_conn.execute("DELETE FROM emotion_categories")
                    # 批量插入到分离的情感数据数据库
                    insert_data = [(emo[0], emo[1], emo[2], emo[3], emo[4]) for emo in emotions]
                    emotion_conn.executemany('''
                        INSERT INTO emotion_categories (id, name_zh, name_en, parent_id, level)
                        VALUES (?, ?, ?, ?, ?)
                    ''', insert_data)
                    emotion_count = len(insert_data)
                    self.logger.info(f"迁移了 {emotion_count} 个情感分类到分离的情感数据数据库")
            except Exception as e:
                self.logger.warning(f"迁移情感分类数据时出错: {e}")

            # 提交事务
            emotion_conn.commit()

            return {
                "status": "success",
                "emotions_migrated": emotion_count
            }
        except Exception as e:
            # 回滚事务
            try:
                emotion_adapter.connect().rollback()
            except:
                pass
            self.logger.error(f"迁移情感分类数据时出错: {e}")
            raise


# 全局数据库迁移器实例
db_migrator = None


def get_db_migrator() -> DatabaseMigrator:
    """获取数据库迁移器实例"""
    global db_migrator
    if db_migrator is None:
        db_migrator = DatabaseMigrator()
    return db_migrator