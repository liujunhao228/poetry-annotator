"""
情感服务
负责情感分析相关的业务逻辑
"""

import pandas as pd
from typing import Optional
from src.core.db_manager import DBManager
from src.core.data_processor import DataProcessor
from src.core.cache import CacheManager


class EmotionService:
    """
    情感服务
    
    负责：
    - 情感分布统计
    - 情感共现分析
    - Apriori 关联规则挖掘
    """
    
    def __init__(self, db_manager: DBManager, cache_manager: Optional[CacheManager] = None):
        """
        初始化情感服务
        
        :param db_manager: DBManager 实例
        :param cache_manager: CacheManager 实例（可选）
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.processor = DataProcessor(db_manager)
    
    def get_emotion_distribution(
        self, 
        use_actual: bool = True,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取情感分布数据
        
        :param use_actual: True 使用最新标注，False 使用所有标注
        :param use_cache: 是否使用缓存
        :return: 包含完整层级的情感分布数据
        """
        cache_key = f"emotion_distribution_{'actual' if use_actual else 'frequency'}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        if use_actual:
            result = self.processor.compute_emotion_distribution_actual()
        else:
            result = self.processor.compute_emotion_distribution_frequency()
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=3600)
        
        return result
    
    def get_frequent_emotion_combinations(
        self, 
        limit: int = 20,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取高频情感共现组合（单句内）
        
        :param limit: 返回的最大组合数
        :param use_cache: 是否使用缓存
        :return: 包含可读情感组合的 DataFrame
        """
        cache_key = f"emotion_combinations_{limit}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.processor.compute_frequent_emotion_combinations(limit)
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=1800)
        
        return result
    
    def get_frequent_poem_emotion_sets(
        self, 
        limit: int = 20,
        use_actual: bool = True,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取高频全诗情感集合
        
        :param limit: 返回的最大集合数
        :param use_actual: True 使用最新标注，False 使用所有标注
        :param use_cache: 是否使用缓存
        :return: 包含可读情感集合的 DataFrame
        """
        cache_key = f"poem_emotion_sets_{'actual' if use_actual else 'frequency'}_{limit}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        if use_actual:
            result = self.processor.compute_frequent_poem_emotion_sets_actual(limit)
        else:
            result = self.processor.compute_frequent_poem_emotion_sets_frequency(limit)
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=1800)
        
        return result
    
    def mine_apriori(
        self,
        level: str,
        min_support: float,
        min_length: int = 2,
        max_transactions: Optional[int] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        使用 Apriori 算法挖掘高频情感项集
        
        :param level: 分析层级 ('sentence' 或 'poem')
        :param min_support: 最小支持度阈值 (0 到 1 之间)
        :param min_length: 项集的最短长度
        :param max_transactions: 最大事务数，用于限制计算规模
        :param use_cache: 是否使用缓存
        :return: 包含高频项集的 DataFrame
        """
        cache_key = f"apriori_{level}_{min_support}_{min_length}_{max_transactions}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.processor.mine_frequent_emotion_itemsets_apriori(
            level=level,
            min_support=min_support,
            min_length=min_length,
            max_transactions=max_transactions
        )
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=7200)
        
        return result
    
    def get_emotion_categories_map(self) -> dict:
        """获取情感 ID 到中文名的映射字典"""
        return self.processor.get_emotion_categories_map()
    
    def clear_cache(self):
        """清除服务缓存"""
        if self.cache_manager:
            self.cache_manager.invalidate("emotion_")
            self.cache_manager.invalidate("apriori_")
        self.processor.clear_cache()
        self.db_manager.clear_cache()
