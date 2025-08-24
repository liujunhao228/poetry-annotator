"""
默认数据查询插件实现
"""
import json
import logging
from typing import List, Dict, Any, Optional, Set
from src.data.plugin_interfaces.core import DataQueryPlugin
from src.data.models import Poem, Author, Annotation
from src.data.separate_databases import get_separate_db_manager


class DefaultQueryPlugin(DataQueryPlugin):
    """默认数据查询插件实现"""
    
    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)
        # 获取分离数据库管理器
        self.separate_db_manager = get_separate_db_manager(db_name)
    
    def get_name(self) -> str:
        return "default_query"
    
    def get_description(self) -> str:
        return "默认数据查询插件实现"
    
    def get_poems_to_annotate(self, model_identifier: str, 
                             limit: Optional[int] = None, 
                             start_id: Optional[int] = None, 
                             end_id: Optional[int] = None,
                             force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词"""
        params = []
        
        # 查询 'title' 而不是 'rhythmic'
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
        
        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))

        return poems
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息"""
        # 查询 'title'
        rows = self.separate_db_manager.raw_data_db.execute_query("""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id = ?
        """, (poem_id,))
        
        if rows:
            row = rows[0]
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            return Poem.from_dict(poem_dict)
        
        return None
    
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息"""
        if not poem_ids:
            return []
        
        # 查询 'title'
        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """
        
        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(poem_ids))
        
        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))
        
        return poems
    
    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        rows = self.separate_db_manager.raw_data_db.execute_query("SELECT name, description, short_description FROM authors ORDER BY name")
        
        return [Author.from_dict(dict(row)) for row in rows]
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页"""
        # 查询 'title'
        query = "SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc FROM poems p LEFT JOIN authors au ON p.author = au.name"
        conditions = []
        params = []

        if author:
            conditions.append("p.author LIKE ?")
            params.append(f"%{author}%")
        
        if title:
            # 按 'title' 字段搜索
            conditions.append("p.title LIKE ?")
            params.append(f"%{title}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Get total count for pagination
        count_query = query.replace("p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc", "COUNT(*)")
        count_rows = self.separate_db_manager.raw_data_db.execute_query(count_query, tuple(params))
        total_count = count_rows[0][0]

        # Add pagination to the main query
        offset = (page - 1) * per_page
        query += " ORDER BY p.id LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))

        return {
            "poems": poems,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "pages": (total_count + per_page - 1) // per_page
        }
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        """高效检查一组 poem_id 是否已被特定模型成功标注"""
        if not poem_ids:
            return set()

        completed_ids = set()
        try:
            # 使用参数化查询防止SQL注入
            placeholders = ','.join('?' * len(poem_ids))
            query = f"""
                SELECT poem_id
                FROM annotations
                WHERE 
                    poem_id IN ({placeholders})
                    AND model_identifier = ?
                    AND status = 'completed'
            """
            
            params = poem_ids + [model_identifier]
            rows = self.separate_db_manager.annotation_db.execute_query(query, tuple(params))
            
            # 使用生成器表达式和 set.update 最高效地处理结果
            completed_ids.update(row[0] for row in rows)
            
        except Exception as e:
            self.logger.error(f"检查标注状态时发生数据库错误: {e}")
        
        return completed_ids