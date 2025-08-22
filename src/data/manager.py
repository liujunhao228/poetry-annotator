"""
数据管理器模块
"""
import sqlite3
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import config_manager
from .adapter import get_database_adapter, normalize_poem_data
from .models import Poem, Author, Annotation
from .exceptions import DataError, DatabaseError
from datetime import datetime


class DataManager:
    """数据管理器，负责数据库操作和数据预处理"""
    
    def __init__(self, db_name: str = "default"):
        db_config = config_manager.get_database_config()
        
        # 处理新的多数据库配置
        if 'db_paths' in db_config:
            db_paths = db_config['db_paths']
            if db_name == "default":
                # 默认使用第一个数据库
                self.db_path = next(iter(db_paths.values()))
                self.db_name = next(iter(db_paths.keys()))
            else:
                if db_name not in db_paths:
                    raise ValueError(f"数据库 '{db_name}' 未在配置中定义。")
                self.db_path = db_paths[db_name]
                self.db_name = db_name
        # 回退到旧的单数据库配置
        elif 'db_path' in db_config:
            self.db_path = db_config['db_path']
            self.db_name = "default"
        else:
            raise ValueError("配置文件中未找到数据库路径配置。")
            
        # 如果source_dir还没有被设置（比如在initialize_all_databases_from_source_folders中），使用默认值
        if not hasattr(self, 'source_dir'):
            self.source_dir = config_manager.get_data_config()['source_dir']
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"数据管理器初始化 - 数据库: {self.db_path}, 数据源: {self.source_dir}")
        
        # 检查数据库文件是否存在，如果不存在则初始化
        if not Path(self.db_path).exists():
            self.logger.info(f"数据库文件 {self.db_path} 不存在，正在初始化...")
            self._initialize_database_if_not_exists()
        
        # 初始化数据库适配器
        self.db_adapter = get_database_adapter('sqlite', self.db_path)
        # DataManager 不再负责初始化数据库表结构
        
        # 为不同数据库设置ID前缀，确保全局唯一性
        self._set_id_prefix()
        
        # 初始化标注日志记录器
        self._init_annotation_logger()
        
        # 初始化分离数据库适配器
        self._init_separate_databases()
        
    def _init_separate_databases(self):
        """初始化分离数据库适配器，为每个主数据库创建独立的分离数据库"""
        from .separate_databases import SeparateDatabaseManager
        separate_db_manager = SeparateDatabaseManager(main_db_name=self.db_name)
        
        # 获取各个分离数据库的适配器
        self.raw_data_db = separate_db_manager.raw_data_db
        self.annotation_db = separate_db_manager.annotation_db
        self.emotion_db = separate_db_manager.emotion_db
    
    def _init_annotation_logger(self):
        """初始化标注结果专用日志记录器 - 已移除以避免重复日志记录"""
        # 不再创建分散的日志记录器，使用AnnotationDataLogger进行统一聚合记录
        self.annotation_logger = None
    
    def _log_annotation_result(self, poem_id: int, model_identifier: str, status: str, 
                              annotation_result: Optional[str] = None, 
                              error_message: Optional[str] = None):
        """记录标注结果到专用日志文件（单行JSON格式） - 已移除以避免重复日志记录"""
        # 不再记录分散的日志，使用AnnotationDataLogger进行统一聚合记录
        pass
    
    def _set_id_prefix(self):
        """为不同数据库设置ID前缀，确保全局唯一性"""
        # 定义数据库名称到前缀的映射
        db_prefixes = {
            "TangShi": 1000000,  # 唐诗ID前缀
            "SongCi": 2000000,   # 宋词ID前缀
            "YuanQu": 3000000,   # 元曲ID前缀
            "default": 0         # 默认数据库前缀
        }
        
        # 根据数据库名称设置前缀
        self.id_prefix = db_prefixes.get(self.db_name, 0)
        self.logger.info(f"数据库 {self.db_name} 的ID前缀设置为: {self.id_prefix}")
    
    @classmethod
    def initialize_all_databases_from_source_folders(cls, clear_existing: bool = False) -> Dict[str, Dict[str, int]]:
        """根据source_json下的子文件夹初始化所有数据库"""
        from .initializer import initialize_all_databases_from_source_folders
        return initialize_all_databases_from_source_folders(clear_existing)

    def load_data_from_json(self, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        file_path = Path(self.source_dir) / json_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {file_path}")
        
        self.logger.debug(f"加载JSON文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.logger.debug(f"JSON文件 {json_file} 加载完成，包含 {len(data)} 条记录")
        return data
    
    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据 - [修改] 适配唐诗/宋诗文件格式"""
        source_path = Path(self.source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"数据源目录不存在: {source_path}")
        
        all_data = []
        
        # [修改] 查找所有 poet.*.*.json 和 ci.*.*.json 文件
        poet_files = list(source_path.glob('poet.*.*.json'))
        ci_files = list(source_path.glob('ci.*.*.json'))
        json_files = poet_files + ci_files
        json_files.sort()  # 确保按文件名排序
        
        self.logger.info(f"找到 {len(json_files)} 个JSON文件 ({len(poet_files)} 个poet文件, {len(ci_files)} 个ci文件)")
        
        for json_file in json_files:
            try:
                self.logger.debug(f"处理文件: {json_file.name}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
                self.logger.debug(f"文件 {json_file.name} 处理完成，包含 {len(data)} 条记录")
            except Exception as e:
                self.logger.error(f"处理文件 {json_file.name} 时出错: {e}")
        
        self.logger.info(f"所有JSON文件加载完成，总计 {len(all_data)} 条记录")
        return all_data
    
    def load_author_data(self) -> List[Dict[str, Any]]:
        """加载作者数据 - [修改] 适配唐诗/宋诗作者文件格式"""
        source_path = Path(self.source_dir)
        if not source_path.exists():
            self.logger.warning(f"数据源目录不存在: {source_path}")
            return []

        all_authors = []
        # 查找所有 authors.*.json 和 author.*.json 文件
        authors_files = list(source_path.glob('authors.*.json'))
        author_files = list(source_path.glob('author.*.json'))
        author_files = sorted(authors_files + author_files)

        if not author_files:
            self.logger.warning("在数据源目录中未找到作者文件。")
            return []

        self.logger.info(f"找到 {len(author_files)} 个作者文件: {[f.name for f in author_files]}")

        for author_file in author_files:
            try:
                with open(author_file, 'r', encoding='utf-8') as f:
                    authors = json.load(f)
                all_authors.extend(authors)
                self.logger.info(f"从 {author_file.name} 加载了 {len(authors)} 位作者信息。")
            except Exception as e:
                self.logger.error(f"加载作者文件 {author_file.name} 时出错: {e}")
        
        self.logger.info(f"所有作者文件加载完成，总计加载了 {len(all_authors)} 位作者信息。")
        return all_authors
    
    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息 - [修改] 适配新的 'desc' 字段"""
        from datetime import datetime, timezone, timedelta
        self.logger.info(f"开始批量插入 {len(authors_data)} 位作者信息...")
        conn = self.raw_data_db.connect()
        cursor = conn.cursor()

        inserted_count = 0
        tz = timezone(timedelta(hours=8))  # 东八区
        now = datetime.now(tz).isoformat()
        for author_data in authors_data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO authors 
                    (name, description, short_description, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    author_data.get('name', ''),
                    author_data.get('desc', ''),  # [修改] 使用 'desc' 字段
                    author_data.get('short_description', ''), # 新格式无此字段，优雅降级
                    now
                ))
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"插入作者 {author_data.get('name', 'Unknown')} 时出错: {e}")

        conn.commit()
        conn.close()

        self.logger.info(f"作者信息插入完成，成功插入 {inserted_count} 位作者")
        return inserted_count
    
    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """批量插入诗词到数据库 - [修改] 适配 'title' 字段"""
        from datetime import datetime, timezone, timedelta
        self.logger.info(f"开始批量插入 {len(poems_data)} 首诗词...")
        conn = self.raw_data_db.connect()
        cursor = conn.cursor()

        inserted_count = 0
        current_id = start_id or 1
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        for poem_data in poems_data:
            # 标准化诗词数据，处理字段命名差异
            normalized_data = normalize_poem_data(poem_data)
            
            paragraphs = normalized_data.get('paragraphs', [])
            full_text = '\n'.join(paragraphs)

            # 使用全局唯一ID
            global_id = self.id_prefix + current_id

            # 使用 'title' 字段
            cursor.execute('''
                INSERT OR REPLACE INTO poems 
                (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                global_id,  # 使用全局唯一ID
                normalized_data.get('title', ''), # 从 'title' 获取
                normalized_data.get('author', ''),
                json.dumps(paragraphs, ensure_ascii=False),
                full_text,
                normalized_data.get('author_desc', ''),
                'active',  # 默认数据状态为active
                now,
                now
            ))
            inserted_count += 1
            current_id += 1

        conn.commit()
        conn.close()

        self.logger.info(f"诗词插入完成，成功插入 {inserted_count} 首诗词")
        return inserted_count
    
    def get_poems_to_annotate(self, model_identifier: str, 
                               limit: Optional[int] = None, 
                               start_id: Optional[int] = None, 
                               end_id: Optional[int] = None,
                               force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词 - [修改] 查询 'title'"""
        params = []
        
        # [修改] 查询 'title' 而不是 'rhythmic'
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
        
        rows = self.raw_data_db.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))

        return poems

    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息 - [修改] 查询 'title'"""
        if not poem_ids:
            return []
        
        # [修改] 查询 'title'
        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """
        
        rows = self.raw_data_db.execute_query(query, tuple(poem_ids))
        
        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))
        
        return poems

    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息 - [修改] 查询 'title'"""
        # [修改] 查询 'title'
        rows = self.raw_data_db.execute_query("""
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
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None, 
                        error_message: Optional[str] = None) -> bool:
        """保存标注结果到annotations表 (UPSERT)，时间戳带时区"""
        # 不再记录分散的日志，使用AnnotationDataLogger进行统一聚合记录
        from datetime import datetime, timezone, timedelta
        self.logger.debug(f"保存标注结果 - 诗词ID: {poem_id}, 模型: {model_identifier}, 状态: {status}")

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        try:
            rowcount = self.annotation_db.execute_update('''
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

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息 (增强版)"""
        self.logger.debug("开始获取数据库统计信息...")
        
        # 总诗词数量
        rows = self.raw_data_db.execute_query("SELECT COUNT(*) FROM poems")
        total_poems = rows[0][0]
        
        # 总作者数
        rows = self.raw_data_db.execute_query("SELECT COUNT(*) FROM authors")
        total_authors = rows[0][0]
        
        # 按模型和状态统计标注数量
        rows = self.annotation_db.execute_query("""
            SELECT model_identifier, status, COUNT(*) 
            FROM annotations 
            GROUP BY model_identifier, status
        """)
        model_status_counts = rows
        
        # 格式化模型统计
        stats_by_model = {}
        for model, status, count in model_status_counts:
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
    
    def initialize_database_from_json(self, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        self.logger.info("开始初始化数据库...")
        
        if clear_existing:
            self.logger.info("清空现有数据...")
            self.annotation_db.execute_update("DELETE FROM annotations")
            self.raw_data_db.execute_update("DELETE FROM poems")
            self.raw_data_db.execute_update("DELETE FROM authors")
            self.logger.info("现有数据已清空")
        
        # 加载作者数据
        authors = self.load_author_data()
        author_count = 0
        if authors:
            author_count = self.batch_insert_authors(authors)
            self.logger.info(f"插入了 {author_count} 位作者信息")
        
        # 加载诗词数据
        poems = self.load_all_json_files()
        poem_count = 0
        if poems:
            # 使用 batch_insert_poems 并从ID=1开始
            poem_count = self.batch_insert_poems(poems, start_id=1)
            print(f"插入了 {poem_count} 首诗词")
        
        print("数据库初始化完成!")
        return {
            'authors': author_count,
            'poems': poem_count
        }
    
    def export_results(self, output_format: str = 'jsonl', 
                       output_file: Optional[str] = None,
                       model_filter: Optional[str] = None) -> str:
        """导出标注结果 - [修改] 导出 'title'"""
        # 构建查询条件
        where_clause = ""
        params = []
        if model_filter:
            where_clause = "WHERE a.model_identifier = ?"
            params.append(model_filter)
        
        # [修改] 查询 'title'
        query = f"""
            SELECT 
                p.id as poem_id,
                p.title,
                p.author,
                p.paragraphs,
                p.full_text,
                p.author_desc,
                a.model_identifier,
                a.status,
                a.annotation_result,
                a.error_message,
                a.created_at,
                a.updated_at
            FROM poems p
            INNER JOIN annotations a ON p.id = a.poem_id
            {where_clause}
            ORDER BY p.id, a.model_identifier
        """
        
        results = self.raw_data_db.execute_query(query, tuple(params))
        
        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_suffix = f"_{model_filter}" if model_filter else ""
            output_file = f"data/output/export_{timestamp}{model_suffix}.{output_format}"
        
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for row in results:
                    result_dict = {
                        'poem_id': row[0],
                        'title': row[1], # [修改]
                        'author': row[2],
                        'paragraphs': row[3],
                        'full_text': row[4],
                        'author_desc': row[5],
                        'model_identifier': row[6],
                        'status': row[7],
                        'annotation_result': row[8],
                        'error_message': row[9],
                        'created_at': row[10],
                        'updated_at': row[11]
                    }
                    f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
        
        return str(output_file)

    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        # 获取总体统计
        rows = self.raw_data_db.execute_query("""
            SELECT 
                COUNT(DISTINCT p.id) as total_poems,
                COUNT(a.id) as total_annotations,
                COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_annotations,
                COUNT(CASE WHEN a.status = 'failed' THEN 1 END) as failed_annotations
            FROM poems p
            LEFT JOIN annotations a ON p.id = a.poem_id
        """)
        
        overall_stats = rows[0]
        
        # 按模型统计
        model_stats = self.annotation_db.execute_query("""
            SELECT 
                model_identifier,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM annotations
            GROUP BY model_identifier
            ORDER BY model_identifier
        """)
        
        # 按状态统计
        status_stats = self.annotation_db.execute_query("""
            SELECT 
                status,
                COUNT(*) as count
            FROM annotations
            GROUP BY status
        """)
        
        return {
            'overall': {
                'total_poems': overall_stats[0],
                'total_annotations': overall_stats[1],
                'completed_annotations': overall_stats[2],
                'failed_annotations': overall_stats[3],
                'success_rate': (overall_stats[2] / overall_stats[1] * 100) if overall_stats[1] > 0 else 0
            },
            'by_model': {
                model: {
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'success_rate': (completed / total * 100) if total > 0 else 0
                }
                for model, total, completed, failed in model_stats
            },
            'by_status': {
                status: count for status, count in status_stats
            }
        }

    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        rows = self.raw_data_db.execute_query("SELECT name, description, short_description FROM authors ORDER BY name")
        
        return [Author.from_dict(dict(row)) for row in rows]

    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页 - [修改] 适配 'title'"""
        # [修改] 查询 'title'
        query = "SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc FROM poems p LEFT JOIN authors au ON p.author = au.name"
        conditions = []
        params = []

        if author:
            conditions.append("p.author LIKE ?")
            params.append(f"%{author}%")
        
        if title:
            # [修改] 按 'title' 字段搜索
            conditions.append("p.title LIKE ?")
            params.append(f"%{title}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Get total count for pagination
        count_query = query.replace("p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc", "COUNT(*)")
        count_rows = self.raw_data_db.execute_query(count_query, tuple(params))
        total_count = count_rows[0][0]

        # Add pagination to the main query
        offset = (page - 1) * per_page
        query += " ORDER BY p.id LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        rows = self.raw_data_db.execute_query(query, tuple(params))

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

    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> set[int]:
        """
        高效检查一组 poem_id 是否已被特定模型成功标注。
        仅查询必要的 'completed' 状态的 poem_id，非常节省资源。

        :param poem_ids: 需要检查的诗词ID列表。
        :param model_identifier: 要检查的模型的标识符。
        :return: 一个包含在这批ID中且已成功标注的 poem_id 的集合。
        """
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
            rows = self.annotation_db.execute_query(query, tuple(params))
            
            # 使用生成器表达式和 set.update 最高效地处理结果
            completed_ids.update(row[0] for row in rows)
            
        except Exception as e:
            self.logger.error(f"检查标注状态时发生数据库错误: {e}")
        
        return completed_ids

# 全局数据管理器实例
data_manager = None


def get_data_manager(db_name: str = "default"):
    """获取数据管理器实例，支持在运行时切换数据库"""
    global data_manager
    if data_manager is None or data_manager.db_name != db_name:
        data_manager = DataManager(db_name=db_name)
    return data_manager