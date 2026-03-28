"""
诗词仓库接口与实现 - 管理诗词数据访问

Poetry repository for managing poetry data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Set
from datetime import datetime

from .base import Repository

# 兼容两种导入方式：作为包导入和作为独立模块导入
try:
    from src.models.poetry import PoetryModel
except ImportError:
    from models.poetry import PoetryModel


class PoetryRepository(Repository[PoetryModel], ABC):
    """诗词仓库抽象基类"""

    @abstractmethod
    def get_to_annotate(
        self,
        model_identifier: str,
        limit: Optional[int] = None,
        id_range: Optional[Tuple[int, int]] = None,
        exclude_annotated: bool = True
    ) -> List[PoetryModel]:
        """获取待标注的诗词"""
        pass

    @abstractmethod
    def get_completed_ids(
        self,
        poem_ids: List[int],
        model_identifier: str
    ) -> Set[int]:
        """获取已成功标注的 ID 集合"""
        pass

    @abstractmethod
    def get_by_ids(self, poem_ids: List[int]) -> List[PoetryModel]:
        """根据 ID 列表批量获取诗词"""
        pass

    @abstractmethod
    def search(
        self,
        author: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[PoetryModel], int]:
        """搜索诗词"""
        pass


class PoetryRepositoryImpl(PoetryRepository):
    """诗词仓库实现"""

    def __init__(self, connection_factory):
        self._connection_factory = connection_factory

    def _get_connection(self):
        return self._connection_factory()

    def get_by_id(self, id: int) -> Optional[PoetryModel]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, author, paragraphs, full_text, author_desc, created_at, updated_at
            FROM poems
            WHERE id = ?
        """, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[PoetryModel]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT id, title, author, paragraphs, full_text, author_desc, created_at, updated_at FROM poems"
        params = []
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)
        cursor.execute(query, params)
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def add(self, entity: PoetryModel) -> PoetryModel:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO poems
            (id, title, author, paragraphs, full_text, author_desc, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.id,
            entity.title,
            entity.author,
            json.dumps(entity.paragraphs, ensure_ascii=False),
            entity.full_text,
            entity.author_desc,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        ))
        conn.commit()
        return entity

    def add_batch(self, entities: List[PoetryModel]) -> List[PoetryModel]:
        conn = self._get_connection()
        cursor = conn.cursor()
        data = []
        for entity in entities:
            data.append((
                entity.id,
                entity.title,
                entity.author,
                json.dumps(entity.paragraphs, ensure_ascii=False),
                entity.full_text,
                entity.author_desc,
                entity.created_at.isoformat(),
                entity.updated_at.isoformat()
            ))
        cursor.executemany("""
            INSERT OR REPLACE INTO poems
            (id, title, author, paragraphs, full_text, author_desc, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        return entities

    def update(self, entity: PoetryModel) -> PoetryModel:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE poems
            SET title = ?, author = ?, paragraphs = ?, full_text = ?,
                author_desc = ?, updated_at = ?
            WHERE id = ?
        """, (
            entity.title,
            entity.author,
            json.dumps(entity.paragraphs, ensure_ascii=False),
            entity.full_text,
            entity.author_desc,
            entity.updated_at.isoformat(),
            entity.id
        ))
        conn.commit()
        return entity

    def delete(self, id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM poems WHERE id = ?", (id,))
        conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM poems")
        return cursor.fetchone()[0]

    def get_to_annotate(
        self,
        model_identifier: str,
        limit: Optional[int] = None,
        id_range: Optional[Tuple[int, int]] = None,
        exclude_annotated: bool = True
    ) -> List[PoetryModel]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text,
                   au.description as author_desc, p.created_at, p.updated_at
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
        """
        params = []
        conditions = []
        
        if exclude_annotated:
            conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM annotations a
                    WHERE a.poem_id = p.id
                    AND a.model_identifier = ?
                    AND a.status = 'completed'
                )
            """)
            params.append(model_identifier)
        
        if id_range:
            start_id, end_id = id_range
            if start_id:
                conditions.append("p.id >= ?")
                params.append(start_id)
            if end_id:
                conditions.append("p.id <= ?")
                params.append(end_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY p.id"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def get_completed_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        if not poem_ids:
            return set()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT poem_id
            FROM annotations
            WHERE poem_id IN ({placeholders})
            AND model_identifier = ?
            AND status = 'completed'
        """
        params = poem_ids + [model_identifier]
        cursor.execute(query, params)
        return {row[0] for row in cursor.fetchall()}

    def get_by_ids(self, poem_ids: List[int]) -> List[PoetryModel]:
        if not poem_ids:
            return []
        
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT id, title, author, paragraphs, full_text, author_desc,
                   created_at, updated_at
            FROM poems
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, poem_ids)
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def search(
        self,
        author: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[PoetryModel], int]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if author:
            conditions.append("p.author LIKE ?")
            params.append(f"%{author}%")
        if title:
            conditions.append("p.title LIKE ?")
            params.append(f"%{title}%")
        
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        
        count_query = f"SELECT COUNT(*) FROM poems p{where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text,
                   au.description as author_desc, p.created_at, p.updated_at
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            {where_clause}
            ORDER BY p.id
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        cursor.execute(query, params)
        
        models = [self._row_to_model(row) for row in cursor.fetchall()]
        return models, total

    def _row_to_model(self, row) -> PoetryModel:
        paragraphs = row['paragraphs']
        if isinstance(paragraphs, str):
            try:
                paragraphs = json.loads(paragraphs)
            except (json.JSONDecodeError, ValueError):
                paragraphs = [paragraphs] if paragraphs else []
        
        return PoetryModel(
            id=row['id'],
            title=row['title'],
            author=row['author'],
            paragraphs=paragraphs,
            full_text=row['full_text'],
            author_desc=row['author_desc'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now(),
        )


import sqlite3
import json
