"""
标注结果仓库接口与实现 - 管理标注数据访问

Annotation repository for managing annotation data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

from .base import Repository

# 兼容两种导入方式：作为包导入和作为独立模块导入
try:
    from src.models.annotation import AnnotationModel, AnnotationStatistics
except ImportError:
    from models.annotation import AnnotationModel, AnnotationStatistics


class AnnotationRepository(Repository[AnnotationModel], ABC):
    """
    标注结果仓库抽象基类
    
    定义标注数据访问的业务接口
    """

    @abstractmethod
    def get_by_poem_id(self, poem_id: int) -> List[AnnotationModel]:
        """根据诗词 ID 获取所有标注"""
        pass

    @abstractmethod
    def get_by_model(self, model_identifier: str, limit: int = 100, offset: int = 0) -> List[AnnotationModel]:
        """根据模型标识符获取标注"""
        pass

    @abstractmethod
    def get_statistics(self) -> AnnotationStatistics:
        """获取标注统计信息"""
        pass

    @abstractmethod
    def get_by_poem_and_model(self, poem_id: int, model_identifier: str) -> Optional[AnnotationModel]:
        """根据诗词 ID 和模型标识符获取单个标注"""
        pass

    @abstractmethod
    def update_or_insert(
        self,
        poem_id: int,
        model_identifier: str,
        status: str,
        annotation_result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新或插入标注（UPSERT）"""
        pass

    @abstractmethod
    def get_with_poems(
        self,
        model_identifier: Optional[str] = None,
        status: Optional[str] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Tuple[AnnotationModel, Any]], int]:
        """获取标注数据（带诗词信息），支持分页和过滤"""
        pass


class AnnotationRepositoryImpl(AnnotationRepository):
    """
    标注结果仓库实现
    
    基于 SQL 数据库的实现
    """

    def __init__(self, connection_factory):
        """
        初始化标注结果仓库
        
        Args:
            connection_factory: 数据库连接工厂函数
        """
        self._connection_factory = connection_factory

    def _get_connection(self):
        """获取数据库连接"""
        return self._connection_factory()

    def get_by_id(self, id: int) -> Optional[AnnotationModel]:
        """根据 ID 获取单个标注"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, poem_id, model_identifier, status, annotation_result,
                   error_message, created_at, updated_at
            FROM annotations
            WHERE id = ?
        """, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[AnnotationModel]:
        """获取所有标注（支持分页）"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT id, poem_id, model_identifier, status, annotation_result,
                   error_message, created_at, updated_at
            FROM annotations
            ORDER BY created_at DESC
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

    def add(self, entity: AnnotationModel) -> AnnotationModel:
        """添加单个标注"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO annotations
            (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.poem_id,
            entity.model_identifier,
            entity.status,
            entity.annotation_result,
            entity.error_message,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        ))
        conn.commit()
        return entity

    def add_batch(self, entities: List[AnnotationModel]) -> List[AnnotationModel]:
        """批量添加标注"""
        conn = self._get_connection()
        cursor = conn.cursor()
        data = []
        for entity in entities:
            data.append((
                entity.poem_id,
                entity.model_identifier,
                entity.status,
                entity.annotation_result,
                entity.error_message,
                entity.created_at.isoformat(),
                entity.updated_at.isoformat()
            ))
        cursor.executemany("""
            INSERT INTO annotations
            (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        return entities

    def update(self, entity: AnnotationModel) -> AnnotationModel:
        """更新单个标注"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE annotations
            SET status = ?, annotation_result = ?, error_message = ?, updated_at = ?
            WHERE id = ?
        """, (
            entity.status,
            entity.annotation_result,
            entity.error_message,
            entity.updated_at.isoformat(),
            entity.id
        ))
        conn.commit()
        return entity

    def delete(self, id: int) -> bool:
        """删除单个标注"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM annotations WHERE id = ?", (id,))
        conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """获取标注总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM annotations")
        return cursor.fetchone()[0]

    def get_by_poem_id(self, poem_id: int) -> List[AnnotationModel]:
        """根据诗词 ID 获取所有标注"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, poem_id, model_identifier, status, annotation_result,
                   error_message, created_at, updated_at
            FROM annotations
            WHERE poem_id = ?
            ORDER BY model_identifier, created_at DESC
        """, (poem_id,))
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def get_by_model(
        self,
        model_identifier: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnnotationModel]:
        """根据模型标识符获取标注"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, poem_id, model_identifier, status, annotation_result,
                   error_message, created_at, updated_at
            FROM annotations
            WHERE model_identifier = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (model_identifier, limit, offset))
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def get_by_poem_and_model(
        self,
        poem_id: int,
        model_identifier: str
    ) -> Optional[AnnotationModel]:
        """根据诗词 ID 和模型标识符获取单个标注"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, poem_id, model_identifier, status, annotation_result,
                   error_message, created_at, updated_at
            FROM annotations
            WHERE poem_id = ? AND model_identifier = ?
        """, (poem_id, model_identifier))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update_or_insert(
        self,
        poem_id: int,
        model_identifier: str,
        status: str,
        annotation_result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新或插入标注（UPSERT）"""
        from datetime import datetime, timezone, timedelta

        conn = self._get_connection()
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO annotations
            (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                status = excluded.status,
                annotation_result = excluded.annotation_result,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
        """, (
            poem_id,
            model_identifier,
            status,
            annotation_result,
            error_message,
            now,
            now
        ))
        conn.commit()
        return cursor.rowcount > 0

    def get_with_poems(
        self,
        model_identifier: Optional[str] = None,
        status: Optional[str] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Tuple[AnnotationModel, Any]], int]:
        """
        获取标注数据（带诗词信息），支持分页和过滤

        Args:
            model_identifier: 模型标识符过滤
            status: 状态过滤
            author: 作者过滤
            title: 标题过滤
            page: 页码
            per_page: 每页数量

        Returns:
            (标注列表，总数) - 每个标注是一个 (AnnotationModel, PoetryModel) 元组
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        if model_identifier:
            conditions.append("a.model_identifier = ?")
            params.append(model_identifier)
        if status:
            conditions.append("a.status = ?")
            params.append(status)
        if author:
            conditions.append("p.author LIKE ?")
            params.append(f"%{author}%")
        if title:
            conditions.append("p.title LIKE ?")
            params.append(f"%{title}%")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # 计算总数
        count_query = f"""
            SELECT COUNT(*)
            FROM annotations a
            JOIN poems p ON a.poem_id = p.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # 获取分页数据
        offset = (page - 1) * per_page
        query = f"""
            SELECT
                a.id, a.poem_id, a.model_identifier, a.status, a.annotation_result,
                a.error_message, a.created_at, a.updated_at,
                p.id as poem_id_col, p.title, p.author, p.paragraphs, p.full_text,
                p.author_desc, p.created_at, p.updated_at
            FROM annotations a
            JOIN poems p ON a.poem_id = p.id
            {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            # 创建 AnnotationModel
            annotation = self._row_to_model(row)
            # 创建 PoetryModel
            from datetime import datetime
            paragraphs = row['paragraphs']
            if isinstance(paragraphs, str):
                import json
                try:
                    paragraphs = json.loads(paragraphs)
                except (json.JSONDecodeError, ValueError):
                    paragraphs = [paragraphs] if paragraphs else []

            poem = type('PoetryModel', (), {})()
            poem.id = row['poem_id_col']
            poem.title = row['title']
            poem.author = row['author']
            poem.paragraphs = paragraphs
            poem.full_text = row['full_text']
            poem.author_desc = row['author_desc']

            results.append((annotation, poem))

        return results, total

    def get_statistics(self) -> AnnotationStatistics:
        """获取标注统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 总体统计
        cursor.execute("""
            SELECT
                COUNT(DISTINCT p.id) as total_poems,
                COUNT(a.id) as total_annotations,
                COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_annotations,
                COUNT(CASE WHEN a.status = 'failed' THEN 1 END) as failed_annotations
            FROM poems p
            LEFT JOIN annotations a ON p.id = a.poem_id
        """)
        row = cursor.fetchone()
        total_poems = row[0] or 0
        total_annotations = row[1] or 0
        completed_annotations = row[2] or 0
        failed_annotations = row[3] or 0
        success_rate = (completed_annotations / total_annotations * 100) if total_annotations > 0 else 0.0

        # 按模型统计
        cursor.execute("""
            SELECT
                model_identifier,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM annotations
            GROUP BY model_identifier
            ORDER BY model_identifier
        """)
        by_model = {}
        for model_row in cursor.fetchall():
            model, total, completed, failed = model_row
            by_model[model] = {
                'total': total,
                'completed': completed,
                'failed': failed,
                'success_rate': (completed / total * 100) if total > 0 else 0.0
            }

        # 按状态统计
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM annotations
            GROUP BY status
        """)
        by_status = {row[0]: row[1] for row in cursor.fetchall()}

        return AnnotationStatistics(
            total_poems=total_poems,
            total_annotations=total_annotations,
            completed_annotations=completed_annotations,
            failed_annotations=failed_annotations,
            success_rate=success_rate,
            by_model=by_model,
            by_status=by_status,
        )

    def _row_to_model(self, row) -> AnnotationModel:
        """将数据库行转换为 AnnotationModel 实例"""
        from datetime import datetime
        
        return AnnotationModel(
            id=row['id'],
            poem_id=row['poem_id'],
            model_identifier=row['model_identifier'],
            status=row['status'],
            annotation_result=row['annotation_result'],
            error_message=row['error_message'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now(),
        )


# 延迟导入 sqlite3 以避免模块加载问题
import sqlite3
