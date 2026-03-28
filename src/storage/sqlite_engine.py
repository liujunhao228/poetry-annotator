"""
SQLite 存储引擎实现

SQLite storage engine implementation
"""

import sqlite3
import logging
from typing import Any, List, Dict, Optional
from contextlib import contextmanager
from pathlib import Path

from .engine import StorageEngine

logger = logging.getLogger(__name__)


class SQLiteEngine(StorageEngine):
    """
    SQLite 存储引擎实现
    
    提供 SQLite 数据库的连接管理和操作接口
    """

    def __init__(self, db_path: str):
        """
        初始化 SQLite 引擎
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_parent_dir()
        
        logger.info(f"SQLite 引擎初始化 - 数据库路径：{self.db_path}")

    def _ensure_parent_dir(self) -> None:
        """确保数据库文件的父目录存在"""
        parent_dir = self.db_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建数据库父目录：{parent_dir}")

    def connect(self) -> sqlite3.Connection:
        """建立 SQLite 数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            # 启用外键约束
            self._connection.execute("PRAGMA foreign_keys = ON")
            logger.debug(f"SQLite 连接已建立：{self.db_path}")
        return self._connection

    def disconnect(self) -> None:
        """关闭 SQLite 数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug(f"SQLite 连接已关闭：{self.db_path}")

    def execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询语句"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        # 将 sqlite3.Row 转换为字典
        return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新语句"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.rowcount

    def executemany(self, query: str, seq_of_parameters: List[tuple]) -> int:
        """批量执行语句"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, seq_of_parameters)
        conn.commit()
        return cursor.rowcount

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.connect()
        try:
            yield TransactionContext(conn)
            conn.commit()
            logger.debug("事务已提交")
        except Exception as e:
            conn.rollback()
            logger.warning(f"事务已回滚：{e}")
            raise

    def init_schema(self) -> None:
        """初始化数据库表结构"""
        logger.info("开始初始化 SQLite 数据库表结构...")
        
        conn = self.connect()
        cursor = conn.cursor()
        
        # 创建诗词表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poems (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                paragraphs TEXT,
                full_text TEXT NOT NULL,
                author_desc TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # 创建作者表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                short_description TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 创建标注结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poem_id INTEGER NOT NULL,
                model_identifier TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('completed', 'failed')),
                annotation_result TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (poem_id) REFERENCES poems(id),
                UNIQUE(poem_id, model_identifier)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_poems_author ON poems(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_poems_title ON poems(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_poem ON annotations(poem_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_model ON annotations(model_identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_status ON annotations(status)')
        
        conn.commit()
        logger.info("SQLite 数据库表结构初始化完成")

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connection is not None

    @property
    def engine_type(self) -> str:
        """返回引擎类型"""
        return "sqlite"

    def get_connection_factory(self):
        """获取连接工厂函数（用于 Repository）"""
        return self.connect


class TransactionContext:
    """
    事务上下文对象
    
    用于在事务块内执行操作
    """

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """在事务中执行查询"""
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = None) -> int:
        """在事务中执行更新"""
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.rowcount

    def executemany(self, query: str, seq_of_parameters: List[tuple]) -> int:
        """在事务中批量执行"""
        cursor = self._connection.cursor()
        cursor.executemany(query, seq_of_parameters)
        return cursor.rowcount


class StorageEngineFactory:
    """
    存储引擎工厂类
    
    根据配置创建对应的存储引擎实例
    """

    @staticmethod
    def create(engine_type: str, db_path: str) -> StorageEngine:
        """
        创建存储引擎实例
        
        Args:
            engine_type: 引擎类型 ('sqlite', 'postgresql', etc.)
            db_path: 数据库路径或连接字符串
            
        Returns:
            存储引擎实例
        """
        if engine_type.lower() == 'sqlite':
            return SQLiteEngine(db_path)
        else:
            # 默认使用 SQLite
            logger.warning(f"未知的引擎类型 '{engine_type}'，使用 SQLite 引擎")
            return SQLiteEngine(db_path)
