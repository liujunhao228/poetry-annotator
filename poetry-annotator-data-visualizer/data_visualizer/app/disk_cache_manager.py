import sqlite3
import pandas as pd
import hashlib
import pickle
import io
import time
from typing import Optional, Any
from data_visualizer.utils import logger


class DiskCacheManager:
    """
    磁盘缓存管理器，用于持久化存储处理后的数据（如DataFrame）。
    """

    def __init__(self, cache_db_path: str):
        """
        初始化磁盘缓存管理器。

        :param cache_db_path: SQLite缓存数据库的路径。
        """
        self.cache_db_path = cache_db_path
        self._init_db()

    def _init_db(self):
        """初始化缓存数据库表结构。"""
        conn = None
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    ttl_seconds INTEGER,
                    db_last_modified TEXT
                )
            ''')
            # 为accessed_at和created_at创建索引，以优化LRU和过期清理
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON cache_entries(accessed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_created_at ON cache_entries(created_at)')
            conn.commit()
            logger.info(f"磁盘缓存数据库已初始化: {self.cache_db_path}")
        except sqlite3.Error as e:
            logger.error(f"初始化磁盘缓存数据库失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _generate_key(self, func_name: str, db_key: str, **kwargs) -> str:
        """
        根据函数名、数据库键和参数生成唯一的缓存键。

        :param func_name: 调用的函数名。
        :param db_key: 数据库标识符。
        :param kwargs: 其他参数。
        :return: 唯一的缓存键。
        """
        # 确保字典项顺序一致以生成稳定的哈希
        sorted_items = str(sorted(kwargs.items()))
        raw_key = f"{func_name}:{db_key}:{sorted_items}"
        # 使用MD5生成固定长度的哈希作为键，足够唯一且短
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        从磁盘缓存中获取数据。

        :param key: 缓存键。
        :return: 缓存的DataFrame，如果未命中或已过期则返回None。
        """
        conn = None
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # 使用当前时间检查过期
            current_time = time.time()
            cursor.execute('''
                SELECT data, created_at, ttl_seconds FROM cache_entries WHERE key = ?
            ''', (key,))
            row = cursor.fetchone()

            if row is None:
                logger.debug(f"磁盘缓存未命中: {key}")
                return None

            data_blob, created_at, ttl_seconds = row
            # 检查TTL
            if ttl_seconds is not None and (current_time - created_at) > ttl_seconds:
                logger.debug(f"磁盘缓存已过期，正在删除: {key}")
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                conn.commit()
                return None

            # 反序列化数据
            try:
                buffer = io.BytesIO(data_blob)
                df = pd.read_pickle(buffer)
                logger.debug(f"磁盘缓存命中: {key}")
                
                # 更新访问时间
                cursor.execute('''
                    UPDATE cache_entries SET accessed_at = ? WHERE key = ?
                ''', (current_time, key))
                conn.commit()
                
                return df
            except Exception as e:
                logger.error(f"反序列化缓存数据失败: {e}")
                # 如果反序列化失败，删除损坏的条目
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                conn.commit()
                return None

        except sqlite3.Error as e:
            logger.error(f"从磁盘缓存获取数据时发生数据库错误: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def set(self, key: str, data: pd.DataFrame, ttl: Optional[int] = None):
        """
        将数据存入磁盘缓存。

        :param key: 缓存键。
        :param data: 要缓存的DataFrame。
        :param ttl: 生存时间（秒）。None表示永不过期。
        """
        conn = None
        try:
            # 序列化DataFrame
            buffer = io.BytesIO()
            data.to_pickle(buffer)
            data_blob = buffer.getvalue()

            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            current_time = time.time()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, data, created_at, accessed_at, ttl_seconds, db_last_modified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (key, data_blob, current_time, current_time, ttl, None)) # db_last_modified暂不使用
            conn.commit()
            logger.debug(f"数据已存入磁盘缓存: {key} (TTL: {ttl})")
        except (sqlite3.Error, Exception) as e:
            logger.error(f"将数据存入磁盘缓存时发生错误: {e}")
        finally:
            if conn:
                conn.close()

    def invalidate(self, pattern: str):
        """
        根据键的模式使缓存失效（此实现为简化版，仅支持前缀匹配）。
        更复杂的模式匹配需要使用LIKE或正则表达式扩展。

        :param pattern: 键的前缀模式。
        """
        conn = None
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            # 注意：SQLite的LIKE匹配可能较慢，对于大量数据可考虑其他策略
            cursor.execute("DELETE FROM cache_entries WHERE key LIKE ?", (f"{pattern}%",))
            conn.commit()
            logger.info(f"已根据模式 '{pattern}' 清除磁盘缓存条目。")
        except sqlite3.Error as e:
            logger.error(f"使磁盘缓存失效时发生错误: {e}")
        finally:
            if conn:
                conn.close()

    def clear(self):
        """清除所有磁盘缓存。"""
        conn = None
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries")
            conn.commit()
            logger.info("所有磁盘缓存已清除。")
        except sqlite3.Error as e:
            logger.error(f"清除所有磁盘缓存时发生错误: {e}")
        finally:
            if conn:
                conn.close()

# 全局单例实例
_disk_cache_manager_instance: Optional[DiskCacheManager] = None

def get_disk_cache_manager() -> DiskCacheManager:
    """获取全局磁盘缓存管理器单例实例。"""
    global _disk_cache_manager_instance
    if _disk_cache_manager_instance is None:
        # 定义缓存数据库路径，与主应用在同一目录
        import os
        from data_visualizer.config import visualizer_project_root
        cache_db_path = os.path.join(str(visualizer_project_root), 'cache.db')
        _disk_cache_manager_instance = DiskCacheManager(cache_db_path)
    return _disk_cache_manager_instance