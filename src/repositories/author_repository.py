"""
作者仓库接口与实现 - 管理作者数据访问

Author repository for managing author data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .base import Repository

# 兼容两种导入方式：作为包导入和作为独立模块导入
try:
    from src.models.poetry import AuthorModel
except ImportError:
    from models.poetry import AuthorModel


class AuthorRepository(Repository[AuthorModel], ABC):
    """
    作者仓库抽象基类

    定义作者数据访问的业务接口
    """

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[AuthorModel]:
        """根据作者名称获取作者信息"""
        pass

    @abstractmethod
    def search(self, keyword: str, limit: int = 10) -> List[AuthorModel]:
        """搜索作者"""
        pass


class AuthorRepositoryImpl(AuthorRepository):
    """
    作者仓库实现

    基于 SQL 数据库的实现
    """

    def __init__(self, connection_factory):
        """
        初始化作者仓库

        Args:
            connection_factory: 数据库连接工厂函数
        """
        self._connection_factory = connection_factory

    def _get_connection(self):
        """获取数据库连接"""
        return self._connection_factory()

    def get_by_id(self, id: str) -> Optional[AuthorModel]:
        """根据名称（主键）获取作者"""
        return self.get_by_name(id)

    def get_by_name(self, name: str) -> Optional[AuthorModel]:
        """根据作者名称获取作者信息"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, description, short_description, created_at
            FROM authors
            WHERE name = ?
        """, (name,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[AuthorModel]:
        """获取所有作者（支持分页）"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT name, description, short_description, created_at
            FROM authors
            ORDER BY name
        """
        params = []
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)
        cursor.execute(query, params)
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def add(self, entity: AuthorModel) -> AuthorModel:
        """添加单个作者"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO authors
            (name, description, short_description, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            entity.name,
            entity.description,
            entity.short_description,
            entity.created_at.isoformat()
        ))
        conn.commit()
        return entity

    def add_batch(self, entities: List[AuthorModel]) -> List[AuthorModel]:
        """批量添加作者"""
        conn = self._get_connection()
        cursor = conn.cursor()
        data = []
        for entity in entities:
            data.append((
                entity.name,
                entity.description,
                entity.short_description,
                entity.created_at.isoformat()
            ))
        cursor.executemany("""
            INSERT OR REPLACE INTO authors
            (name, description, short_description, created_at)
            VALUES (?, ?, ?, ?)
        """, data)
        conn.commit()
        return entities

    def update(self, entity: AuthorModel) -> AuthorModel:
        """更新单个作者"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE authors
            SET description = ?, short_description = ?
            WHERE name = ?
        """, (
            entity.description,
            entity.short_description,
            entity.name
        ))
        conn.commit()
        return entity

    def delete(self, name: str) -> bool:
        """删除单个作者"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM authors WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """获取作者总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM authors")
        return cursor.fetchone()[0]

    def search(self, keyword: str, limit: int = 10) -> List[AuthorModel]:
        """搜索作者"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, description, short_description, created_at
            FROM authors
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
            LIMIT ?
        """, (f"%{keyword}%", f"%{keyword}%", limit))
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def _row_to_model(self, row) -> AuthorModel:
        """将数据库行转换为 AuthorModel 实例"""
        from datetime import datetime

        return AuthorModel(
            name=row['name'],
            description=row['description'],
            short_description=row['short_description'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
        )


# 延迟导入 sqlite3 以避免模块加载问题
import sqlite3
