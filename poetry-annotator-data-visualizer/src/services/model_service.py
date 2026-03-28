"""
模型服务
负责模型性能相关的业务逻辑
"""

import pandas as pd
from typing import Optional
from src.core.db_manager import DBManager
from src.core.data_processor import DataProcessor
from src.core.cache import CacheManager


class ModelService:
    """
    模型服务
    
    负责：
    - 模型性能数据获取
    - 标注趋势分析
    """
    
    def __init__(self, db_manager: DBManager, cache_manager: Optional[CacheManager] = None):
        """
        初始化模型服务
        
        :param db_manager: DBManager 实例
        :param cache_manager: CacheManager 实例（可选）
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.processor = DataProcessor(db_manager)
    
    def get_model_performance(self, use_cache: bool = True) -> pd.DataFrame:
        """
        获取模型性能数据
        
        :param use_cache: 是否使用缓存
        :return: 包含模型性能指标的 DataFrame
        """
        cache_key = "model_performance"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.processor.compute_model_performance()
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=3600)
        
        return result
    
    def get_annotation_trends(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取标注趋势数据
        
        :param start_date: 开始日期 (ISO 格式)
        :param end_date: 结束日期 (ISO 格式)
        :param use_cache: 是否使用缓存
        :return: 包含标注趋势的 DataFrame
        """
        cache_key = f"annotation_trends_{start_date}_{end_date}"
        
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        result = self.processor.compute_model_annotation_trends(start_date, end_date)
        
        if use_cache and self.cache_manager and not result.empty:
            self.cache_manager.set(cache_key, result, ttl=600)
        
        return result
    
    def clear_cache(self):
        """清除服务缓存"""
        if self.cache_manager:
            self.cache_manager.invalidate("model_")
            self.cache_manager.invalidate("annotation_")
        self.processor.clear_cache()
        self.db_manager.clear_cache()
