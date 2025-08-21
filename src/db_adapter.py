import sqlite3
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类，用于支持多种数据库"""
    
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

    @abstractmethod
    def begin_transaction(self):
        """开始事务"""
        pass

    @abstractmethod
    def commit_transaction(self):
        """提交事务"""
        pass

    @abstractmethod
    def rollback_transaction(self):
        """回滚事务"""
        pass

    @abstractmethod
    def close(self):
        """关闭数据库连接"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self._conn = None

    def connect(self):
        """建立SQLite数据库连接"""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def begin_transaction(self):
        """开始事务"""
        conn = self.connect()
        conn.execute("BEGIN;")

    def commit_transaction(self):
        """提交事务"""
        if self._conn:
            self._conn.commit()

    def rollback_transaction(self):
        """回滚事务"""
        if self._conn:
            self._conn.rollback()

    def init_database(self):
        """初始化SQLite数据库表结构"""
        self.logger.info("开始初始化SQLite数据库...")
        conn = self.connect()
        cursor = conn.cursor()

        # 创建诗词表 - 兼容title和rhythmic字段
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poems (
                id INTEGER PRIMARY KEY,
                title TEXT,
                author TEXT,
                paragraphs TEXT,
                full_text TEXT,
                author_desc TEXT,
                data_status TEXT DEFAULT 'active',
                pre_classification TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 创建标注结果表
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

        # 创建作者表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                name TEXT PRIMARY KEY,
                description TEXT,
                short_description TEXT,
                created_at TEXT
            )
        ''')

        # 为数据可视化添加额外的表
        # 情感分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_categories (
                id TEXT PRIMARY KEY,
                name_zh TEXT NOT NULL,
                name_en TEXT,
                parent_id TEXT,
                level INTEGER NOT NULL,
                FOREIGN KEY(parent_id) REFERENCES emotion_categories(id)
            )
        ''')

        # 句子标注表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentence_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                annotation_id INTEGER NOT NULL,
                poem_id INTEGER NOT NULL,
                sentence_uid TEXT NOT NULL,
                sentence_text TEXT,
                FOREIGN KEY(annotation_id) REFERENCES annotations(id) ON DELETE CASCADE
            )
        ''')

        # 句子情感链接表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentence_emotion_links (
                sentence_annotation_id INTEGER NOT NULL,
                emotion_id TEXT NOT NULL,
                is_primary BOOLEAN NOT NULL,
                PRIMARY KEY (sentence_annotation_id, emotion_id),
                FOREIGN KEY(sentence_annotation_id) REFERENCES sentence_annotations(id) ON DELETE CASCADE,
                FOREIGN KEY(emotion_id) REFERENCES emotion_categories(id)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_poem_author ON poems(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_poem_model ON annotations(poem_id, model_identifier)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uidx_poem_model ON annotations(poem_id, model_identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_status ON annotations(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_created_at ON annotations(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_poem_created_at ON poems(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emotion_parent_id ON emotion_categories(parent_id)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uidx_sentence_ref ON sentence_annotations(annotation_id, sentence_uid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_link_emotion_id ON sentence_emotion_links(emotion_id)')

        conn.commit()
        self.logger.info("SQLite数据库初始化完成")
    
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
        return rows
    
    def execute_update(self, query: str, params: Optional[tuple] = None, commit: bool = True):
        """执行更新操作"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rowcount = cursor.rowcount
        if commit:
            conn.commit()
        return rowcount


def get_database_adapter(db_type: str, db_path: str) -> DatabaseAdapter:
    """根据数据库类型获取对应的适配器"""
    if db_type.lower() == 'sqlite':
        return SQLiteAdapter(db_path)
    else:
        # 默认使用SQLite适配器
        return SQLiteAdapter(db_path)


def normalize_poem_data(poem_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化诗词数据，处理字段命名差异"""
    normalized = poem_data.copy()
    
    # 处理title/rhythmic字段差异
    # 如果有rhythmic字段但没有title字段，则使用rhythmic作为title
    if 'rhythmic' in normalized and 'title' not in normalized:
        normalized['title'] = normalized['rhythmic']
    # 如果有title字段但没有rhythmic字段，则使用title作为rhythmic（保持向后兼容）
    elif 'title' in normalized and 'rhythmic' not in normalized:
        normalized['rhythmic'] = normalized['title']
    
    return normalized