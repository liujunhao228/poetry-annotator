"""
默认数据存储插件实现
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from src.data.plugin_interfaces.core import DataStoragePlugin
from src.data.separate_databases import get_separate_db_manager
from src.data.models import Poem, Author, Annotation


class DefaultStoragePlugin(DataStoragePlugin):
    """默认数据存储插件实现"""
    
    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)
        # 获取分离数据库管理器
        self.separate_db_manager = get_separate_db_manager(db_name)
    
    def get_name(self) -> str:
        return "default_storage"
    
    def get_description(self) -> str:
        return "默认数据存储插件实现"
    
    def initialize_database_from_json(self, source_dir: str, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        # 这个方法需要与数据处理插件协同工作
        # 实际实现会委托给数据处理插件加载数据，然后调用batch_insert方法存储
        self.logger.info("数据库初始化请求已接收，将由数据处理插件协同完成")
        return {
            'authors': 0,
            'poems': 0
        }
    
    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息"""
        self.logger.info(f"开始批量插入 {len(authors_data)} 位作者信息...")
        
        inserted_count = 0
        tz = timezone(timedelta(hours=8))  # 东八区
        now = datetime.now(tz).isoformat()
        
        # 获取数据库连接
        conn = self.separate_db_manager.raw_data_db.get_connection()
        cursor = conn.cursor()
        
        try:
            for author_data in authors_data:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO authors 
                        (name, description, short_description, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        author_data.get('name', ''),
                        author_data.get('desc', ''),  # 使用 'desc' 字段
                        author_data.get('short_description', ''), # 新格式无此字段，优雅降级
                        now
                    ))
                    inserted_count += 1
                except Exception as e:
                    self.logger.error(f"插入作者 {author_data.get('name', 'Unknown')} 时出错: {e}")

            conn.commit()
        except Exception as e:
            self.logger.error(f"批量插入作者信息时出错: {e}")
            conn.rollback()
            raise
        finally:
            # 关闭数据库连接
            self.separate_db_manager.raw_data_db.close_connection(conn)

        self.logger.info(f"作者信息插入完成，成功插入 {inserted_count} 位作者")
        return inserted_count
    
    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """批量插入诗词到数据库"""
        from src.data.adapter import normalize_poem_data
        
        self.logger.info(f"开始批量插入 {len(poems_data)} 首诗词...")
        
        inserted_count = 0
        current_id = start_id or 1
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        # 获取ID前缀
        db_prefixes = {
            "TangShi": 1000000,  # 唐诗ID前缀
            "SongCi": 2000000,   # 宋词ID前缀
            "YuanQu": 3000000,   # 元曲ID前缀
            "default": 0         # 默认数据库前缀
        }
        id_prefix = db_prefixes.get(self.db_name, 0)
        
        # 获取数据库连接
        conn = self.separate_db_manager.raw_data_db.get_connection()
        cursor = conn.cursor()
        
        try:
            for poem_data in poems_data:
                # 标准化诗词数据，处理字段命名差异
                normalized_data = normalize_poem_data(poem_data)
                
                paragraphs = normalized_data.get('paragraphs', [])
                full_text = '\n'.join(paragraphs)

                # 使用全局唯一ID
                global_id = id_prefix + current_id

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
        except Exception as e:
            self.logger.error(f"批量插入诗词时出错: {e}")
            conn.rollback()
            raise
        finally:
            # 关闭数据库连接
            self.separate_db_manager.raw_data_db.close_connection(conn)

        self.logger.info(f"诗词插入完成，成功插入 {inserted_count} 首诗词")
        return inserted_count
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                       annotation_result: Optional[str] = None, 
                       error_message: Optional[str] = None) -> bool:
        """保存标注结果到annotations表 (UPSERT)，时间戳带时区"""
        self.logger.debug(f"保存标注结果 - 诗词ID: {poem_id}, 模型: {model_identifier}, 状态: {status}")

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        # 获取数据库连接
        conn = self.separate_db_manager.annotation_db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO annotations (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                    status = excluded.status,
                    annotation_result = excluded.annotation_result,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
            ''', (poem_id, model_identifier, status, annotation_result, error_message, now, now))

            conn.commit()
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"标注结果保存成功 - 诗词ID: {poem_id}, 模型: {model_identifier}")
            return success
        except Exception as e:
            self.logger.error(f"保存标注结果失败 - 诗词ID: {poem_id}, 模型: {model_identifier}, 错误: {e}")
            conn.rollback()
            return False
        finally:
            # 关闭数据库连接
            self.separate_db_manager.annotation_db.close_connection(conn)