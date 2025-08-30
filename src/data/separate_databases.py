"""
分离数据库管理模块
负责管理原始数据、标注数据和情感分类数据的分离存储
"""

import sqlite3
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone, timedelta
from .db_config_manager import get_separate_database_paths, ensure_database_directory_exists
from .exceptions import DatabaseError


class SeparateDatabaseManager:
    """分离数据库管理器，负责管理原始数据、标注数据和情感分类数据的分离存储"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_configs = self._get_database_configs()
        
        # 为了保持向后兼容性，添加适配器属性
        self.raw_data_db = self
        self.annotation_db = self
        self.emotion_db = self
        
    def _get_database_configs(self) -> Dict[str, str]:
        """获取分离数据库配置"""
        # 使用统一的配置管理获取分离数据库路径
        separate_paths = get_separate_database_paths()
        
        # 确保数据库目录存在
        for path in separate_paths.values():
            ensure_database_directory_exists(path)
            
        return separate_paths
    
    def _init_raw_data_database(self, db_path: str):
        """初始化原始数据数据库表结构"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS authors (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    short_description TEXT,
                    created_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS poems (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    paragraphs TEXT,
                    full_text TEXT,
                    author_desc TEXT,
                    data_status TEXT DEFAULT 'active',
                    created_at TEXT,
                    updated_at TEXT
                );
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_annotation_database(self, db_path: str):
        """初始化标注数据数据库表结构"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poem_id INTEGER,
                    model_identifier TEXT,
                    status TEXT,
                    annotation_result TEXT,
                    error_message TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(poem_id, model_identifier)
                );
                
                CREATE TABLE IF NOT EXISTS sentence_annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    annotation_id INTEGER,
                    sentence_index INTEGER,
                    sentence_text TEXT,
                    emotions TEXT,
                    created_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS sentence_emotion_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence_annotation_id INTEGER,
                    emotion_category_id INTEGER,
                    confidence REAL
                );
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_emotion_database(self, db_path: str):
        """初始化情感分类数据库表结构"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    parent_id INTEGER,
                    created_at TEXT
                );
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_all_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化所有分离的数据库"""
        results = {}
        
        # 初始化原始数据数据库
        try:
            self.logger.info(f"开始初始化原始数据数据库 ({self.db_configs['raw_data']})")
            result = self._initialize_raw_data_database(clear_existing)
            results['raw_data'] = result
            self.logger.info("原始数据数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化原始数据数据库失败: {e}")
            results['raw_data'] = {"error": str(e)}
            
        # 初始化标注数据数据库
        try:
            self.logger.info(f"开始初始化标注数据数据库 ({self.db_configs['annotation']})")
            result = self._initialize_annotation_database(clear_existing)
            results['annotation'] = result
            self.logger.info("标注数据数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化标注数据数据库失败: {e}")
            results['annotation'] = {"error": str(e)}
            
        # 初始化情感分类数据库
        try:
            self.logger.info(f"开始初始化情感分类数据库 ({self.db_configs['emotion']})")
            result = self._initialize_emotion_database(clear_existing)
            results['emotion'] = result
            self.logger.info("情感分类数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化情感分类数据库失败: {e}")
            results['emotion'] = {"error": str(e)}
            
        return results
    
    def _initialize_raw_data_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化原始数据数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['raw_data'])
        
        # 初始化数据库表结构（仅初始化原始数据相关表）
        self._init_raw_data_database(self.db_configs['raw_data'])
        
        # 如果需要清空现有数据
        if clear_existing:
            conn = sqlite3.connect(self.db_configs['raw_data'])
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM poems")
                cursor.execute("DELETE FROM authors")
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        
        return {
            "status": "success",
            "message": f"原始数据数据库初始化完成"
        }
    
    def _initialize_annotation_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化标注数据数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['annotation'])
        
        # 初始化数据库表结构（仅初始化标注数据相关表）
        self._init_annotation_database(self.db_configs['annotation'])
        
        # 如果需要清空现有数据
        if clear_existing:
            conn = sqlite3.connect(self.db_configs['annotation'])
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM annotations")
                cursor.execute("DELETE FROM sentence_annotations")
                cursor.execute("DELETE FROM sentence_emotion_links")
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        
        return {
            "status": "success",
            "message": f"标注数据数据库初始化完成"
        }
    
    def _initialize_emotion_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化情感分类数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['emotion'])
        
        # 初始化数据库表结构（仅初始化情感分类相关表）
        self._init_emotion_database(self.db_configs['emotion'])
        
        # 如果需要清空现有数据
        if clear_existing:
            conn = sqlite3.connect(self.db_configs['emotion'])
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM emotion_categories")
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        
        # 情感分类体系导入现在由插件处理，这里不再直接导入
        
        return {
            "status": "success",
            "message": f"情感分类数据库初始化完成"
        }
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据库的统计信息"""
        stats = {}
        
        # 统计原始数据数据库
        try:
            if not Path(self.db_configs['raw_data']).exists():
                stats['raw_data'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['poems', 'authors']
                
                conn = sqlite3.connect(self.db_configs['raw_data'])
                cursor = conn.cursor()
                try:
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            rows = cursor.fetchall()
                            tables_stats[table] = rows[0][0] if rows else 0
                        except Exception:
                            tables_stats[table] = "N/A"
                    
                    stats['raw_data'] = {
                        "status": "ok",
                        "path": self.db_configs['raw_data'],
                        "tables": tables_stats
                    }
                finally:
                    conn.close()
        except Exception as e:
            stats['raw_data'] = {
                "status": "error",
                "message": str(e)
            }
            
        # 统计标注数据数据库
        try:
            if not Path(self.db_configs['annotation']).exists():
                stats['annotation'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['annotations', 'sentence_annotations', 'sentence_emotion_links']
                
                conn = sqlite3.connect(self.db_configs['annotation'])
                cursor = conn.cursor()
                try:
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            rows = cursor.fetchall()
                            tables_stats[table] = rows[0][0] if rows else 0
                        except Exception:
                            tables_stats[table] = "N/A"
                    
                    stats['annotation'] = {
                        "status": "ok",
                        "path": self.db_configs['annotation'],
                        "tables": tables_stats
                    }
                finally:
                    conn.close()
        except Exception as e:
            stats['annotation'] = {
                "status": "error",
                "message": str(e)
            }
            
        # 统计情感分类数据库
        try:
            if not Path(self.db_configs['emotion']).exists():
                stats['emotion'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['emotion_categories']
                
                conn = sqlite3.connect(self.db_configs['emotion'])
                cursor = conn.cursor()
                try:
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            rows = cursor.fetchall()
                            tables_stats[table] = rows[0][0] if rows else 0
                        except Exception:
                            tables_stats[table] = "N/A"
                    
                    stats['emotion'] = {
                        "status": "ok",
                        "path": self.db_configs['emotion'],
                        "tables": tables_stats
                    }
                finally:
                    conn.close()
        except Exception as e:
            stats['emotion'] = {
                "status": "error",
                "message": str(e)
            }
            
        return stats

    def get_connection(self, db_type: str = None):
        """获取数据库连接"""
        if db_type is None:
            # 默认返回原始数据数据库连接
            db_path = self.db_configs.get('raw_data')
        else:
            db_path = self.db_configs.get(db_type)
            
        if not db_path:
            raise ValueError(f"未知的数据库类型: {db_type}")
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
            
    def close_connection(self, conn):
        """关闭数据库连接"""
        if conn:
            conn.close()
                
    def execute_query(self, query: str, params: tuple = (), db_type: str = 'raw_data'):
        """执行查询语句"""
        conn = self.get_connection(db_type)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()
                
    def execute_update(self, query: str, params: tuple = (), commit: bool = True, db_type: str = 'raw_data'):
        """执行更新语句"""
        conn = self.get_connection(db_type)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
                
    def execute_script(self, script: str, db_type: str = 'raw_data'):
        """执行SQL脚本"""
        conn = self.get_connection(db_type)
        cursor = conn.cursor()
        try:
            cursor.executescript(script)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


    def begin_transaction(self, db_type: str = 'raw_data'):
        """开始事务"""
        pass  # SQLite在执行语句时自动开始事务


    def commit_transaction(self, db_type: str = 'raw_data'):
        """提交事务"""
        pass  # 通过上下文管理器自动处理


    def rollback_transaction(self, db_type: str = 'raw_data'):
        """回滚事务"""
        pass  # 通过上下文管理器自动处理


    def init_raw_data_database(self):
        """初始化原始数据数据库表结构"""
        self._init_raw_data_database(self.db_configs['raw_data'])


    def init_annotation_database(self):
        """初始化标注数据数据库表结构"""
        self._init_annotation_database(self.db_configs['annotation'])


    def init_emotion_database(self):
        """初始化情感分类数据库表结构"""
        self._init_emotion_database(self.db_configs['emotion'])


    def connect(self):
        """获取数据库连接（为了向后兼容）"""
        return self.get_connection()


# 全局分离数据库管理器实例
separate_db_manager = None
# 锁对象，确保线程安全
import threading
_separate_db_manager_lock = threading.Lock()


def get_separate_db_manager() -> SeparateDatabaseManager:
    """获取分离数据库管理器实例"""
    global separate_db_manager, _separate_db_manager_lock
    
    # 使用双重检查锁定确保线程安全
    if separate_db_manager is None:
        with _separate_db_manager_lock:
            # 再次检查，防止重复创建
            if separate_db_manager is None:
                separate_db_manager = SeparateDatabaseManager()
    
    return separate_db_manager