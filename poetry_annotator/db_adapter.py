"""
数据库适配器 - 支持多种数据库后端
"""

import sqlite3
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def connect(self):
        """建立数据库连接"""
        pass

    @abstractmethod
    def init_database(self):
        """初始化数据库表结构"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None):
        """执行查询"""
        pass

    @abstractmethod
    def execute_update(self, query: str, params: Optional[tuple] = None):
        """执行更新操作"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 数据库适配器"""

    def connect(self):
        """建立 SQLite 数据库连接"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """初始化 SQLite 数据库表结构"""
        self.logger.info("开始初始化 SQLite 数据库...")
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poems (
                id INTEGER PRIMARY KEY,
                title TEXT,
                author TEXT,
                paragraphs TEXT,
                full_text TEXT,
                author_desc TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY,
                poem_id INTEGER,
                model_identifier TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('completed', 'failed')),
                annotation_result TEXT,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(poem_id) REFERENCES poems(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                name TEXT PRIMARY KEY,
                description TEXT,
                short_description TEXT,
                created_at TEXT
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_poem_author ON poems(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_poem_model ON annotations(poem_id, model_identifier)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uidx_poem_model ON annotations(poem_id, model_identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_status ON annotations(status)')

        conn.commit()
        conn.close()
        self.logger.info("SQLite 数据库初始化完成")

    def execute_query(self, query: str, params: Optional[tuple] = None):
        """执行查询操作"""
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def execute_update(self, query: str, params: Optional[tuple] = None):
        """执行更新操作"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount


def get_database_adapter(db_type: str, db_path: str) -> DatabaseAdapter:
    """根据数据库类型获取对应的适配器"""
    if db_type.lower() == 'sqlite':
        return SQLiteAdapter(db_path)
    return SQLiteAdapter(db_path)


def normalize_poem_data(poem_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化诗词数据，处理字段命名差异"""
    normalized = poem_data.copy()
    if 'rhythmic' in normalized and 'title' not in normalized:
        normalized['title'] = normalized['rhythmic']
    elif 'title' in normalized and 'rhythmic' not in normalized:
        normalized['rhythmic'] = normalized['title']
    return normalized
