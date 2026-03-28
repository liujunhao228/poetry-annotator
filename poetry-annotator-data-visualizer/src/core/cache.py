"""
统一缓存管理器：L1 内存 + L2 磁盘两级缓存
"""

import hashlib
import pickle
import time
from pathlib import Path
from typing import Optional, Any
import pandas as pd

from data_visualizer.utils import logger


class CacheManager:
    """
    统一缓存管理器
    
    - L1: 内存缓存 (使用 dict + lru_cache 策略)
    - L2: 磁盘缓存 (使用 pickle 序列化到 SQLite 或文件)
    """
    
    def __init__(self, cache_dir: Path, max_memory_items: int = 100):
        """
        初始化缓存管理器
        
        :param cache_dir: 磁盘缓存目录
        :param max_memory_items: L1 缓存最大条目数
        """
        self.cache_dir = cache_dir
        self.max_memory_items = max_memory_items
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # L1 内存缓存 - 使用简单的 dict，配合手动 LRU 管理
        self._memory_cache: dict[str, tuple[Any, float]] = {}  # {key: (data, timestamp)}
        
        # L2 磁盘缓存使用 SQLite
        self._init_disk_cache()
    
    def _init_disk_cache(self):
        """初始化磁盘缓存数据库"""
        import sqlite3
        self._disk_db_path = self.cache_dir / "cache.db"
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                data BLOB NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                ttl_seconds INTEGER
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON cache_entries(accessed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_created_at ON cache_entries(created_at)')
        conn.commit()
        conn.close()
        logger.debug(f"磁盘缓存数据库已初始化：{self._disk_db_path}")
    
    def _generate_key(self, func_name: str, **kwargs) -> str:
        """根据函数名和参数生成唯一的缓存键"""
        sorted_items = str(sorted(kwargs.items()))
        raw_key = f"{func_name}:{sorted_items}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16]
    
    def _evict_lru_memory(self):
        """L1 缓存超出限制时，移除最久未使用的条目"""
        if len(self._memory_cache) <= self.max_memory_items:
            return
        
        # 按访问时间排序，移除最旧的
        sorted_items = sorted(self._memory_cache.items(), key=lambda x: x[1][1])
        items_to_remove = len(self._memory_cache) - self.max_memory_items
        for key, _ in sorted_items[:items_to_remove]:
            del self._memory_cache[key]
    
    def _evict_expired_disk(self):
        """清理过期的磁盘缓存条目"""
        import sqlite3
        current_time = time.time()
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        # 删除已过期的条目
        cursor.execute('''
            DELETE FROM cache_entries 
            WHERE ttl_seconds IS NOT NULL 
            AND (created_at + ttl_seconds) < ?
        ''', (current_time,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            logger.debug(f"清理了 {deleted} 条过期的磁盘缓存")
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        从缓存中获取数据
        
        :param key: 缓存键
        :return: 缓存的 DataFrame，如果未命中或已过期则返回 None
        """
        # 尝试 L1 内存缓存
        if key in self._memory_cache:
            data, _ = self._memory_cache[key]
            # 更新访问时间
            self._memory_cache[key] = (data, time.time())
            logger.debug(f"L1 缓存命中：{key}")
            return data
        
        # 尝试 L2 磁盘缓存
        import sqlite3
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        cursor.execute('''
            SELECT data, created_at, ttl_seconds FROM cache_entries WHERE key = ?
        ''', (key,))
        row = cursor.fetchone()
        
        if row is None:
            conn.close()
            logger.debug(f"缓存未命中：{key}")
            return None
        
        data_blob, created_at, ttl_seconds = row
        
        # 检查是否过期
        if ttl_seconds is not None and (current_time - created_at) > ttl_seconds:
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            conn.close()
            logger.debug(f"缓存已过期：{key}")
            return None
        
        # 反序列化数据
        try:
            import io
            buffer = io.BytesIO(data_blob)
            df = pd.read_pickle(buffer)
            
            # 更新访问时间
            cursor.execute('''
                UPDATE cache_entries SET accessed_at = ? WHERE key = ?
            ''', (current_time, key))
            conn.commit()
            conn.close()
            
            # 回填 L1 缓存
            self._memory_cache[key] = (df, current_time)
            self._evict_lru_memory()
            
            logger.debug(f"L2 缓存命中：{key}")
            return df
            
        except Exception as e:
            logger.error(f"反序列化缓存数据失败：{e}")
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            conn.close()
            return None
    
    def set(self, key: str, data: pd.DataFrame, ttl: Optional[int] = None, persist: bool = True):
        """
        将数据存入缓存
        
        :param key: 缓存键
        :param data: 要缓存的 DataFrame
        :param ttl: 生存时间（秒），None 表示永不过期
        :param persist: 是否持久化到磁盘
        """
        current_time = time.time()
        
        # 存入 L1 内存缓存
        self._memory_cache[key] = (data, current_time)
        self._evict_lru_memory()
        
        if not persist:
            return
        
        # 存入 L2 磁盘缓存
        import sqlite3
        import io
        
        try:
            buffer = io.BytesIO()
            data.to_pickle(buffer)
            data_blob = buffer.getvalue()
            
            conn = sqlite3.connect(self._disk_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries
                (key, data, created_at, accessed_at, ttl_seconds)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, data_blob, current_time, current_time, ttl))
            
            conn.commit()
            conn.close()
            logger.debug(f"数据已存入磁盘缓存：{key} (TTL: {ttl})")
            
        except Exception as e:
            logger.error(f"将数据存入磁盘缓存时发生错误：{e}")
    
    def invalidate(self, pattern: str):
        """
        根据键的前缀模式使缓存失效
        
        :param pattern: 键的前缀模式
        """
        # 清除 L1 中匹配的缓存
        keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(pattern)]
        for key in keys_to_remove:
            del self._memory_cache[key]
        
        # 清除 L2 中匹配的缓存
        import sqlite3
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries WHERE key LIKE ?", (f"{pattern}%",))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"已根据模式 '{pattern}' 清除 {deleted} 条磁盘缓存条目")
    
    def clear(self):
        """清除所有缓存"""
        self._memory_cache.clear()
        
        import sqlite3
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()
        logger.info("所有缓存已清除")
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        import sqlite3
        conn = sqlite3.connect(self._disk_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache_entries")
        disk_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "l1_memory_items": len(self._memory_cache),
            "l2_disk_items": disk_count,
            "l1_max_items": self.max_memory_items
        }


# 全局单例实例
_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager(cache_dir: str = None, max_memory_items: int = 100) -> CacheManager:
    """获取全局缓存管理器单例实例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        if cache_dir is None:
            from data_visualizer.config import visualizer_project_root
            cache_dir = str(visualizer_project_root / ".cache")
        _cache_manager_instance = CacheManager(Path(cache_dir), max_memory_items)
    return _cache_manager_instance
