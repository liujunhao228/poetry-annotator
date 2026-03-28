"""
数据管理器 - 负责数据库操作和数据预处理
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from ..db_adapter import get_database_adapter, normalize_poem_data
from ..annotation_data_logger import AnnotationDataLogger


class DataManager:
    """数据管理器，负责数据库操作和数据预处理"""

    def __init__(self, db_path: str, source_dir: str, output_dir: str, db_name_alias: str = "default"):
        self.db_path = db_path
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.db_name = db_name_alias

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"数据管理器初始化 - 数据库：{self.db_path}, 数据源：{self.source_dir}")

        self.db_adapter = get_database_adapter('sqlite', self.db_path)
        self._init_database()
        self._set_id_prefix()

    def _set_id_prefix(self):
        """为不同数据库设置 ID 前缀"""
        db_prefixes = {
            "TangShi": 1000000,
            "SongCi": 2000000,
            "YuanQu": 3000000,
            "default": 0
        }
        self.id_prefix = db_prefixes.get(self.db_name, 0)
        self.logger.info(f"数据库 {self.db_name} 的 ID 前缀设置为：{self.id_prefix}")

    def _init_database(self):
        """初始化数据库"""
        self.logger.info("开始初始化数据库...")
        self.db_adapter.init_database()
        self.logger.info("数据库初始化完成")

    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """加载所有 JSON 文件的数据"""
        source_path = Path(self.source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"数据源目录不存在：{source_path}")

        all_data = []
        poet_files = list(source_path.glob('poet.*.*.json'))
        ci_files = list(source_path.glob('ci.*.*.json'))
        json_files = sorted(poet_files + ci_files)

        self.logger.info(f"找到 {len(json_files)} 个 JSON 文件")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
            except Exception as e:
                self.logger.error(f"处理文件 {json_file.name} 时出错：{e}")

        return all_data

    def load_author_data(self) -> List[Dict[str, Any]]:
        """加载作者数据"""
        source_path = Path(self.source_dir)
        if not source_path.exists():
            self.logger.warning(f"数据源目录不存在：{source_path}")
            return []

        all_authors = []
        authors_files = list(source_path.glob('authors.*.json'))
        author_files = list(source_path.glob('author.*.json'))
        author_files = sorted(authors_files + author_files)

        if not author_files:
            self.logger.warning("在数据源目录中未找到作者文件。")
            return []

        self.logger.info(f"找到 {len(author_files)} 个作者文件")

        for author_file in author_files:
            try:
                with open(author_file, 'r', encoding='utf-8') as f:
                    authors = json.load(f)
                all_authors.extend(authors)
            except Exception as e:
                self.logger.error(f"加载作者文件 {author_file.name} 时出错：{e}")

        return all_authors

    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息"""
        self.logger.info(f"开始批量插入 {len(authors_data)} 位作者信息...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        inserted_count = 0
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        for author_data in authors_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO authors
                    (name, description, short_description, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    author_data.get('name', ''),
                    author_data.get('desc', ''),
                    author_data.get('short_description', ''),
                    now
                ))
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"插入作者 {author_data.get('name', 'Unknown')} 时出错：{e}")

        conn.commit()
        conn.close()
        self.logger.info(f"成功插入 {inserted_count} 位作者")
        return inserted_count

    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """批量插入诗词到数据库"""
        self.logger.info(f"开始批量插入 {len(poems_data)} 首诗词...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        inserted_count = 0
        current_id = start_id or 1
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        for poem_data in poems_data:
            normalized_data = normalize_poem_data(poem_data)
            paragraphs = normalized_data.get('paragraphs', [])
            full_text = '\n'.join(paragraphs)
            global_id = self.id_prefix + current_id

            cursor.execute('''
                INSERT OR REPLACE INTO poems
                (id, title, author, paragraphs, full_text, author_desc, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                global_id,
                normalized_data.get('title', ''),
                normalized_data.get('author', ''),
                json.dumps(paragraphs, ensure_ascii=False),
                full_text,
                normalized_data.get('author_desc', ''),
                now,
                now
            ))
            inserted_count += 1
            current_id += 1

        conn.commit()
        conn.close()
        self.logger.info(f"成功插入 {inserted_count} 首诗词")
        return inserted_count

    def get_poems_to_annotate(self, model_identifier: str,
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

        rows = self.db_adapter.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            poems.append(poem)

        return poems

    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Dict[str, Any]]:
        """根据 ID 列表获取诗词信息"""
        if not poem_ids:
            return []

        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """

        rows = self.db_adapter.execute_query(query, tuple(poem_ids))

        poems = []
        for row in rows:
            poem = dict(row)
            if poem.get('paragraphs'):
                poem['paragraphs'] = json.loads(poem['paragraphs'])
            poems.append(poem)

        return poems

    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None,
                        error_message: Optional[str] = None) -> bool:
        """保存标注结果到 annotations 表"""
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        try:
            rowcount = self.db_adapter.execute_update('''
                INSERT INTO annotations (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                    status = excluded.status,
                    annotation_result = excluded.annotation_result,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
            ''', (poem_id, model_identifier, status, annotation_result, error_message, now, now))

            return rowcount > 0
        except Exception as e:
            self.logger.error(f"保存标注结果失败：{e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        rows = self.db_adapter.execute_query("SELECT COUNT(*) FROM poems")
        total_poems = rows[0][0]

        rows = self.db_adapter.execute_query("SELECT COUNT(*) FROM authors")
        total_authors = rows[0][0]

        rows = self.db_adapter.execute_query("""
            SELECT model_identifier, status, COUNT(*)
            FROM annotations
            GROUP BY model_identifier, status
        """)
        model_status_counts = rows

        stats_by_model = {}
        for model, status, count in model_status_counts:
            if model not in stats_by_model:
                stats_by_model[model] = {'completed': 0, 'failed': 0, 'total_annotated': 0}
            stats_by_model[model][status] = count
            stats_by_model[model]['total_annotated'] += count

        return {
            'total_poems': total_poems,
            'total_authors': total_authors,
            'stats_by_model': stats_by_model
        }

    def initialize_database_from_json(self, clear_existing: bool = False) -> Dict[str, int]:
        """从 JSON 文件初始化数据库"""
        self.logger.info("开始初始化数据库...")

        if clear_existing:
            self.logger.info("清空现有数据...")
            self.db_adapter.execute_update("DELETE FROM annotations")
            self.db_adapter.execute_update("DELETE FROM poems")
            self.db_adapter.execute_update("DELETE FROM authors")
            self.logger.info("现有数据已清空")

        authors = self.load_author_data()
        author_count = 0
        if authors:
            author_count = self.batch_insert_authors(authors)

        poems = self.load_all_json_files()
        poem_count = 0
        if poems:
            poem_count = self.batch_insert_poems(poems, start_id=1)

        self.logger.info("数据库初始化完成!")
        return {'authors': author_count, 'poems': poem_count}

    def export_results(self, output_format: str = 'jsonl',
                       output_file: Optional[str] = None,
                       model_filter: Optional[str] = None) -> str:
        """导出标注结果"""
        where_clause = ""
        params = []
        if model_filter:
            where_clause = "WHERE a.model_identifier = ?"
            params.append(model_filter)

        query = f"""
            SELECT
                p.id as poem_id, p.title, p.author, p.paragraphs, p.full_text, p.author_desc,
                a.model_identifier, a.status, a.annotation_result, a.error_message,
                a.created_at, a.updated_at
            FROM poems p
            INNER JOIN annotations a ON p.id = a.poem_id
            {where_clause}
            ORDER BY p.id, a.model_identifier
        """

        results = self.db_adapter.execute_query(query, tuple(params))

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_suffix = f"_{model_filter}" if model_filter else ""
            output_file = f"data/output/export_{timestamp}{model_suffix}.{output_format}"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for row in results:
                    result_dict = {
                        'poem_id': row[0], 'title': row[1], 'author': row[2],
                        'paragraphs': row[3], 'full_text': row[4], 'author_desc': row[5],
                        'model_identifier': row[6], 'status': row[7], 'annotation_result': row[8],
                        'error_message': row[9], 'created_at': row[10], 'updated_at': row[11]
                    }
                    f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')

        return str(output_file)

    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> set:
        """检查一组 poem_id 是否已被特定模型成功标注"""
        if not poem_ids:
            return set()

        completed_ids = set()
        try:
            placeholders = ','.join('?' * len(poem_ids))
            query = f"""
                SELECT poem_id
                FROM annotations
                WHERE poem_id IN ({placeholders})
                    AND model_identifier = ?
                    AND status = 'completed'
            """
            params = poem_ids + [model_identifier]
            rows = self.db_adapter.execute_query(query, tuple(params))
            completed_ids.update(row[0] for row in rows)
        except Exception as e:
            self.logger.error(f"检查标注状态时发生数据库错误：{e}")

        return completed_ids
