import aiosqlite
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator, Set
from .config import config_manager
from src.data.separate_databases import SeparateDatabaseManager, get_separate_db_manager # 明确导入SeparateDatabaseManager
from datetime import datetime, timezone, timedelta


class AsyncDataManager:
    """异步数据管理器，负责数据库操作和数据预处理"""

    def __init__(self, separate_db_manager: SeparateDatabaseManager):
        self.separate_db_manager = separate_db_manager
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"异步数据管理器初始化 - 使用SeparateDatabaseManager")

    # 移除 __aenter__ 和 __aexit__，因为连接管理由 SeparateDBManager 负责
    # async def __aenter__(self):
    #     return self

    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     pass

    async def execute_query(self, db_connector: Any, query: str, params: tuple = (), db_type: str = 'raw_data') -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            # db_connector is an instance of SeparateDatabaseManager
            # Its execute_query is synchronous, so run it in a thread pool
            rows = await asyncio.to_thread(db_connector.execute_query, query, params, db_type)
            return [dict(row) for row in rows]
        except Exception as e:
            db_path_for_log = self.separate_db_manager.db_configs.get(db_type, 'unknown_db')
            self.logger.error(f"查询执行失败 (DB: {db_path_for_log}): {e}")
            raise

    async def execute_update(self, db_connector: Any, query: str, params: tuple = (), db_type: str = 'raw_data') -> int:
        """执行更新操作并返回影响的行数"""
        try:
            # db_connector is an instance of SeparateDatabaseManager
            # Its execute_update is synchronous, so run it in a thread pool
            rowcount = await asyncio.to_thread(db_connector.execute_update, query, params, True, db_type) # commit=True by default
            return rowcount
        except Exception as e:
            db_path_for_log = self.separate_db_manager.db_configs.get(db_type, 'unknown_db')
            self.logger.error(f"更新执行失败 (DB: {db_path_for_log}): {e}")
            raise

    async def get_poem_by_id(self, poem_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取单首诗词信息"""
        rows = await self.execute_query(self.separate_db_manager.raw_data_db, """
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id = ?
        """, (poem_id,))

        if rows:
            row = rows[0]
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            return poem

        return None

    async def get_poems_by_ids(self, poem_ids: List[int]) -> List[Dict[str, Any]]:
        """根据ID列表获取诗词信息"""
        if not poem_ids:
            return []

        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """

        rows = await self.execute_query(self.separate_db_manager.raw_data_db, query, tuple(poem_ids))

        poems = []
        for row in rows:
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            poems.append(poem)

        return poems

    async def get_poems_by_ids_filtered(self, poem_ids: List[int], model_identifier: str) -> List[Dict[str, Any]]:
        """根据ID列表获取诗词信息，并过滤掉已经标注过的诗词"""
        if not poem_ids:
            return []

        # 1. 从 raw_data_db 获取所有诗词
        placeholders = ','.join('?' * len(poem_ids))
        poems_query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """
        all_poems_rows = await self.execute_query(self.separate_db_manager.raw_data_db, poems_query, tuple(poem_ids))
        
        # 2. 从 annotation_db 获取已完成标注的诗词ID
        completed_annotations_query = f"""
            SELECT poem_id
            FROM annotations
            WHERE poem_id IN ({placeholders}) AND model_identifier = ? AND status = 'completed'
        """
        completed_params = poem_ids + [model_identifier]
        completed_rows = await self.execute_query(self.separate_db_manager.annotation_db, completed_annotations_query, tuple(completed_params), db_type='annotation')
        
        completed_poem_ids = {row['poem_id'] for row in completed_rows}

        # 3. 过滤诗词
        filtered_poems = []
        for row in all_poems_rows:
            if row['id'] not in completed_poem_ids:
                poem = dict(row)
                if poem.get('paragraphs'):
                    poem['paragraphs'] = json.loads(poem['paragraphs'])
                filtered_poems.append(poem)

        return filtered_poems

    async def get_poems_to_annotate(self, model_identifier: str,
                                    limit: Optional[int] = None,
                                    start_id: Optional[int] = None,
                                    end_id: Optional[int] = None,
                                    force_rerun: bool = False) -> List[Dict[str, Any]]:
        """获取指定模型待标注的诗词"""
        
        # 1. 构建查询所有诗词的基础部分
        poems_query_params = []
        poems_query = """
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE 1=1
        """
        if start_id is not None:
            poems_query += " AND p.id >= ?"
            poems_query_params.append(start_id)
        if end_id is not None:
            poems_query += " AND p.id <= ?"
            poems_query_params.append(end_id)
        
        poems_query += " ORDER BY p.id"
        
        if limit:
            poems_query += " LIMIT ?"
            poems_query_params.append(limit)

        all_poems_rows = await self.execute_query(self.separate_db_manager.raw_data_db, poems_query, tuple(poems_query_params))
        
        # 2. 如果不是强制重跑，则从 annotation_db 获取已完成标注的诗词ID
        completed_poem_ids: Set[int] = set()
        if not force_rerun:
            # 获取当前批次所有诗词的ID，用于高效查询annotations表
            current_poem_ids = [row['id'] for row in all_poems_rows]
            if current_poem_ids:
                placeholders = ','.join('?' * len(current_poem_ids))
                completed_annotations_query = f"""
                    SELECT poem_id
                    FROM annotations
                    WHERE poem_id IN ({placeholders}) AND model_identifier = ? AND status = 'completed'
                """
                completed_params = current_poem_ids + [model_identifier]
                completed_rows = await self.execute_query(self.separate_db_manager.annotation_db, completed_annotations_query, tuple(completed_params))
                completed_poem_ids = {row['poem_id'] for row in completed_rows}

        # 3. 过滤诗词
        filtered_poems = []
        for row in all_poems_rows:
            if row['id'] not in completed_poem_ids:
                poem = dict(row)
                if poem.get('paragraphs'):
                    poem['paragraphs'] = json.loads(poem['paragraphs'])
                filtered_poems.append(poem)

        return filtered_poems

    async def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                              annotation_result: Optional[str] = None,
                              error_message: Optional[str] = None) -> bool:
        """保存标注结果到annotations表 (UPSERT)，时间戳带时区"""
        self.logger.debug(f"保存标注结果 - 诗词ID: {poem_id}, 模型: {model_identifier}, 状态: {status}")

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        try:
            rowcount = await self.execute_update(self.separate_db_manager.annotation_db, '''
                INSERT INTO annotations (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                    status = excluded.status,
                    annotation_result = excluded.annotation_result,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
            ''', (poem_id, model_identifier, status, annotation_result, error_message, now, now), db_type='annotation')

            success = rowcount > 0
            if success:
                self.logger.debug(f"标注结果保存成功 - 诗词ID: {poem_id}, 模型: {model_identifier}")
            return success
        except Exception as e:
            self.logger.error(f"保存标注结果失败 - 诗词ID: {poem_id}, 模型: {model_identifier}, 错误: {e}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        self.logger.debug("开始获取数据库统计信息...")

        # 总诗词数量
        rows = await self.execute_query(self.separate_db_manager.raw_data_db, "SELECT COUNT(*) as count FROM poems")
        total_poems = rows[0]['count'] if rows else 0

        # 总作者数
        rows = await self.execute_query(self.separate_db_manager.raw_data_db, "SELECT COUNT(*) as count FROM authors")
        total_authors = rows[0]['count'] if rows else 0

        # 按模型和状态统计标注数量
        rows = await self.execute_query(self.separate_db_manager.annotation_db, """
            SELECT model_identifier, status, COUNT(*) as count
            FROM annotations
            GROUP BY model_identifier, status
        """, db_type='annotation')

        # 格式化模型统计
        stats_by_model = {}
        for row in rows:
            model = row['model_identifier']
            status = row['status']
            count = row['count']

            if model not in stats_by_model:
                stats_by_model[model] = {'completed': 0, 'failed': 0, 'total_annotated': 0}
            stats_by_model[model][status] = count
            stats_by_model[model]['total_annotated'] += count

        self.logger.debug(f"统计信息获取完成 - 诗词: {total_poems}, 作者: {total_authors}, 模型数: {len(stats_by_model)}")

        return {
            'total_poems': total_poems,
            'total_authors': total_authors,
            'stats_by_model': stats_by_model
        }
