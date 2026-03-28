"""
诗词服务
负责诗词数据相关的业务逻辑
"""

import pandas as pd
from typing import Optional
from src.core.db_manager import DBManager
from src.core.data_processor import DataProcessor
from src.core.cache import CacheManager


class PoemService:
    """
    诗词服务
    
    负责：
    - 诗词数据获取
    - 诗人作品统计
    - 诗词长度分布分析
    """
    
    def __init__(self, db_manager: DBManager, cache_manager: Optional[CacheManager] = None):
        """
        初始化诗词服务
        
        :param db_manager: DBManager 实例
        :param cache_manager: CacheManager 实例（可选）
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.processor = DataProcessor(db_manager)
    
    def get_all_poems(self, use_cache: bool = True) -> pd.DataFrame:
        """
        获取所有诗词数据
        
        :param use_cache: 是否使用缓存
        :return: 包含诗词数据的 DataFrame
        """
        cache_key = "all_poems"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.db_manager.get_all_poems()
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=1800)
        
        return result
    
    def get_author_poem_counts(self, use_cache: bool = True) -> pd.DataFrame:
        """
        获取诗人作品数量统计
        
        :param use_cache: 是否使用缓存
        :return: 包含诗人作品数量的 DataFrame
        """
        cache_key = "author_poem_counts"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.db_manager.get_poem_count_by_author()
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=1800)
        
        return result
    
    def get_poem_length_distribution(
        self, 
        method: str = 'words',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取诗词长度分布
        
        :param method: 统计方法 ('words' 或 'characters')
        :param use_cache: 是否使用缓存
        :return: 包含长度分布的 DataFrame
        """
        cache_key = f"poem_length_{method}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.processor.compute_poem_length_distribution(method)
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=1800)
        
        return result
    
    def clear_cache(self):
        """清除服务缓存"""
        if self.cache_manager:
            self.cache_manager.invalidate("poem_")
            self.cache_manager.invalidate("author_")
        self.processor.clear_cache()
        self.db_manager.clear_cache()
