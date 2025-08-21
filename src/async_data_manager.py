import aiosqlite
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator
from .config_manager import config_manager
from .db_adapter import get_database_adapter, normalize_poem_data
from datetime import datetime, timezone, timedelta


class AsyncDataManager:
    """异步数据管理器，负责数据库操作和数据预处理"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"异步数据管理器初始化 - 数据库: {self.db_path}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.conn = await aiosqlite.connect(self.db_path)
        # 设置行工厂以便于访问列
        self.conn.row_factory = aiosqlite.Row
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'conn') and self.conn:
            await self.conn.close()

    async def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            cursor = await self.conn.execute(query, params)
            rows = await cursor.fetchall()
            # 将Row对象转换为字典
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            raise

    async def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        try:
            cursor = await self.conn.execute(query, params)
            await self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            await self.conn.rollback()
            self.logger.error(f"更新执行失败: {e}")
            raise

    async def get_poem_by_id(self, poem_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取单首诗词信息"""
        rows = await self.execute_query("""
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

        rows = await self.execute_query(query, tuple(poem_ids))

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

        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            LEFT JOIN annotations an ON p.id = an.poem_id AND an.model_identifier = ?
            WHERE p.id IN ({placeholders})
            AND (an.status IS NULL OR an.status != 'completed')
        """

        # 第一个参数是model_identifier，后面是poem_ids
        params = [model_identifier] + poem_ids
        rows = await self.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            poems.append(poem)

        return poems

    async def get_poems_to_annotate(self, model_identifier: str,
                                    limit: Optional[int] = None,
                                    start_id: Optional[int] = None,
                                    end_id: Optional[int] = None,
                                    force_rerun: bool = False) -> List[Dict[str, Any]]:
        """获取指定模型待标注的诗词"""
        params = []

        query = """
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
        """

        # 如果不是强制重跑，则排除已完成的
        if not force_rerun:
            query += """
                LEFT JOIN annotations an ON p.id = an.poem_id AND an.model_identifier = ?
                WHERE (an.status IS NULL OR an.status != 'completed')
            """
            params.append(model_identifier)
        else:
            query += " WHERE 1=1"

        if start_id is not None:
            query += " AND p.id >= ?"
            params.append(start_id)
        if end_id is not None:
            query += " AND p.id <= ?"
            params.append(end_id)

        query += " ORDER BY p.id"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = await self.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            poems.append(poem)

        return poems

    async def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                              annotation_result: Optional[str] = None,
                              error_message: Optional[str] = None) -> bool:
        """保存标注结果到annotations表 (UPSERT)，时间戳带时区"""
        self.logger.debug(f"保存标注结果 - 诗词ID: {poem_id}, 模型: {model_identifier}, 状态: {status}")

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        try:
            rowcount = await self.execute_update('''
                INSERT INTO annotations (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                    status = excluded.status,
                    annotation_result = excluded.annotation_result,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
            ''', (poem_id, model_identifier, status, annotation_result, error_message, now, now))

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
        rows = await self.execute_query("SELECT COUNT(*) as count FROM poems")
        total_poems = rows[0]['count'] if rows else 0

        # 总作者数
        rows = await self.execute_query("SELECT COUNT(*) as count FROM authors")
        total_authors = rows[0]['count'] if rows else 0

        # 按模型和状态统计标注数量
        rows = await self.execute_query("""
            SELECT model_identifier, status, COUNT(*) as count
            FROM annotations
            GROUP BY model_identifier, status
        """)

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