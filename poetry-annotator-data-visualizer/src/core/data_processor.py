"""
数据处理器
负责数据处理、转换和分析逻辑
无 Streamlit 依赖，可独立测试
"""

import pandas as pd
from functools import lru_cache
from typing import Optional

# 确保 mlxtend 已安装
try:
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    logger = None
    TransactionEncoder = None
    apriori = None
    TQDM_AVAILABLE = False

from data_visualizer.utils import logger


class DataProcessor:
    """
    数据处理器
    
    负责：
    - 模型性能计算
    - 诗词长度分布分析
    - 标注趋势分析
    - 情感分布计算
    - 情感共现分析
    - Apriori 关联规则挖掘
    """
    
    def __init__(self, db_manager):
        """
        初始化数据处理器
        
        :param db_manager: DBManager 实例
        """
        self.db_manager = db_manager
    
    @lru_cache(maxsize=30)
    def compute_model_performance(self) -> pd.DataFrame:
        """
        计算各模型的性能指标（成功率等）
        
        :return: 包含模型性能指标的 DataFrame
        """
        df_summary = self.db_manager.get_annotation_summary_by_model()
        if df_summary.empty:
            logger.warning("无标注汇总数据用于模型性能计算。")
            return pd.DataFrame(columns=['model_identifier', 'total_annotations', 'completed', 'failed', 'success_rate'])

        # 将状态列转换为单独的列
        pivot_df = df_summary.pivot_table(index='model_identifier', columns='status', values='count', fill_value=0)

        # 确保存在 'completed' 和 'failed' 列
        if 'completed' not in pivot_df.columns:
            pivot_df['completed'] = 0
        if 'failed' not in pivot_df.columns:
            pivot_df['failed'] = 0

        pivot_df['total_annotations'] = pivot_df['completed'] + pivot_df['failed']
        pivot_df['success_rate'] = pivot_df.apply(
            lambda row: (row['completed'] / row['total_annotations']) * 100 if row['total_annotations'] > 0 else 0,
            axis=1
        )
        result_df = pivot_df[['total_annotations', 'completed', 'failed', 'success_rate']].reset_index()
        logger.debug("模型性能计算完成。")
        return result_df

    @lru_cache(maxsize=30)
    def compute_poem_length_distribution(self, method: str = 'words') -> pd.DataFrame:
        """
        计算诗词长度分布
        
        :param method: 统计方法 ('words' 或 'characters')
        :return: 包含长度分布的 DataFrame
        """
        poems_df = self.db_manager.get_all_poems()
        if poems_df.empty:
            logger.warning("无诗词数据用于长度分布计算。")
            return pd.DataFrame()

        def calculate_length(text, m):
            if not isinstance(text, str):
                return 0
            if m == 'words':
                return len(text.split())
            elif m == 'characters':
                return len(text)
            return 0

        poems_df['poem_length'] = poems_df['full_text'].apply(lambda x: calculate_length(x, method))

        # 定义长度区间
        bins = [0, 50, 100, 150, 200, 300, 500, float('inf')]
        labels = ['0-50', '51-100', '101-150', '151-200', '201-300', '301-500', '500+']

        poems_df['length_band'] = pd.cut(poems_df['poem_length'], bins=bins, labels=labels, right=True, include_lowest=True)

        distribution = poems_df['length_band'].value_counts().sort_index().reset_index()
        distribution.columns = ['length_band', 'count']
        logger.debug(f"诗词长度分布 ({method}) 计算完成。")
        return distribution

    @lru_cache(maxsize=30)
    def compute_model_annotation_trends(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        按模型计算每日标注趋势
        
        :param start_date: 开始日期 (ISO 格式)
        :param end_date: 结束日期 (ISO 格式)
        :return: 包含标注趋势的 DataFrame
        """
        df = self.db_manager.get_annotations_with_poem_info(start_date, end_date)
        if df.empty:
            logger.warning(f"在 {start_date} 到 {end_date} 范围内无标注数据用于趋势分析。")
            return pd.DataFrame()

        df['annotation_date'] = pd.to_datetime(df['annotation_created_at']).dt.date
        trends_df = df.groupby(['annotation_date', 'model_identifier', 'status']).size().unstack(fill_value=0).reset_index()

        if 'completed' not in trends_df.columns:
            trends_df['completed'] = 0
        if 'failed' not in trends_df.columns:
            trends_df['failed'] = 0

        trends_df['total_annotations'] = trends_df['completed'] + trends_df['failed']
        logger.debug(f"模型标注趋势 ({start_date}-{end_date}) 计算完成。")
        return trends_df.sort_values(['annotation_date', 'model_identifier'])

    @lru_cache(maxsize=1)
    def get_emotion_categories_map(self) -> dict:
        """获取情感 ID 到中文名的映射字典"""
        df = self.db_manager.get_all_emotion_categories()
        if df.empty:
            logger.warning("未能加载情感分类映射。")
            return {}
        return df.set_index('id')['name_zh'].to_dict()

    def _compute_emotion_distribution(self, use_actual: bool) -> pd.DataFrame:
        """
        计算情感分布的通用方法
        
        :param use_actual: True 使用最新标注，False 使用所有标注
        :return: 包含完整层级的情感分布数据
        """
        all_categories_df = self.db_manager.get_all_emotion_categories()
        if all_categories_df.empty:
            logger.warning("情感分类表为空，无法计算分布。")
            return pd.DataFrame()

        # 数据预处理
        all_categories_df['id'] = all_categories_df['id'].astype(str)
        all_categories_df['parent_id'] = all_categories_df['parent_id'].fillna('').astype(str)
        all_categories_df.loc[all_categories_df['level'] == 1, 'parent_id'] = ''

        # 获取叶子节点的计数值
        if use_actual:
            leaf_dist_df = self.db_manager.get_emotion_distribution_actual()
        else:
            leaf_dist_df = self.db_manager.get_emotion_distribution_frequency()
            
        if leaf_dist_df.empty:
            logger.warning("无情感标注数据用于分布计算。")
            all_categories_df['count'] = 0
            all_categories_df['percentage'] = 0.0
            return all_categories_df

        # 合并数据
        merged_df = pd.merge(all_categories_df, leaf_dist_df[['id', 'count']], on='id', how='left')
        merged_df['count'] = merged_df['count'].fillna(0).astype(int)

        # 手动计算父节点的 count
        parent_sums = merged_df[merged_df['level'] == 2].groupby('parent_id')['count'].sum()
        parent_ids_series = merged_df.loc[merged_df['level'] == 1, 'id']
        parent_counts = parent_ids_series.map(parent_sums).fillna(0).astype(int)
        merged_df.loc[merged_df['level'] == 1, 'count'] = parent_counts

        # 计算百分比
        total_emotion_count = merged_df['count'].sum()
        if total_emotion_count > 0:
            merged_df['percentage'] = (merged_df['count'] / total_emotion_count * 100).round(2)
        else:
            merged_df['percentage'] = 0.0

        return merged_df

    @lru_cache(maxsize=30)
    def compute_emotion_distribution_frequency(self) -> pd.DataFrame:
        """计算情感分布（基于所有标注）"""
        return self._compute_emotion_distribution(use_actual=False)

    @lru_cache(maxsize=30)
    def compute_emotion_distribution_actual(self) -> pd.DataFrame:
        """计算情感分布（基于最新标注）"""
        return self._compute_emotion_distribution(use_actual=True)

    @lru_cache(maxsize=30)
    def compute_frequent_emotion_combinations(self, limit: int = 20) -> pd.DataFrame:
        """
        处理高频情感共现数据，将 ID 转换为可读文本
        
        :param limit: 返回的最大组合数
        :return: 包含可读情感组合的 DataFrame
        """
        combos_df = self.db_manager.get_frequent_emotion_combinations(limit=limit)
        if combos_df.empty:
            logger.info("无高频情感共现数据。")
            return pd.DataFrame()

        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            combos_df['combination_readable'] = combos_df['emotion_combo_ids']
            return combos_df

        def format_cooccurrence(id_string):
            if not isinstance(id_string, str):
                return "无效组合"
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知 ID({id})") for id in ids]
            return ', '.join(names)

        combos_df['combination_readable'] = combos_df['emotion_combo_ids'].apply(format_cooccurrence)
        logger.debug(f"高频情感共现 (Top {limit}) 数据计算完成。")
        return combos_df[['combination_readable', 'combo_count', 'sentence_text']]

    @lru_cache(maxsize=30)
    def compute_frequent_poem_emotion_sets_frequency(self, limit: int = 20) -> pd.DataFrame:
        """
        处理高频全诗情感集合数据（基于所有标注）
        
        :param limit: 返回的最大集合数
        :return: 包含可读情感集合的 DataFrame
        """
        sets_df = self.db_manager.get_frequent_poem_emotion_sets_frequency(limit=limit)
        if sets_df.empty:
            logger.info("无高频全诗情感集合数据。")
            return pd.DataFrame()

        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            sets_df['set_readable'] = sets_df['emotion_set_ids']
            return sets_df

        def format_set(id_string):
            if not isinstance(id_string, str):
                return "无效集合"
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知 ID({id})") for id in ids]
            return ', '.join(names)

        sets_df['set_readable'] = sets_df['emotion_set_ids'].apply(format_set)
        logger.debug(f"高频全诗情感集合 (Top {limit}) 数据计算完成。")
        return sets_df[['set_readable', 'set_count', 'poem_example']]

    @lru_cache(maxsize=30)
    def compute_frequent_poem_emotion_sets_actual(self, limit: int = 20) -> pd.DataFrame:
        """
        处理高频全诗情感集合数据（基于最新标注）
        
        :param limit: 返回的最大集合数
        :return: 包含可读情感集合的 DataFrame
        """
        sets_df = self.db_manager.get_frequent_poem_emotion_sets_actual(limit=limit)
        if sets_df.empty:
            logger.info("无高频全诗情感集合数据。")
            return pd.DataFrame()

        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            sets_df['set_readable'] = sets_df['emotion_set_ids']
            return sets_df

        def format_set(id_string):
            if not isinstance(id_string, str):
                return "无效集合"
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知 ID({id})") for id in ids]
            return ', '.join(names)

        sets_df['set_readable'] = sets_df['emotion_set_ids'].apply(format_set)
        logger.debug(f"高频全诗情感集合 (Top {limit}) 数据计算完成。")
        return sets_df[['set_readable', 'set_count', 'poem_example']]

    @lru_cache(maxsize=30)
    def mine_frequent_emotion_itemsets_apriori(
        self, 
        level: str, 
        min_support: float, 
        min_length: int = 2, 
        max_transactions: Optional[int] = None
    ) -> pd.DataFrame:
        """
        使用 Apriori 算法挖掘高频情感项集
        
        :param level: 分析层级 ('sentence' 或 'poem')
        :param min_support: 最小支持度阈值 (0 到 1 之间)
        :param min_length: 项集的最短长度
        :param max_transactions: 最大事务数，用于限制计算规模
        :return: 包含高频项集的 DataFrame
        """
        if apriori is None:
            logger.error("无法执行 Apriori 挖掘，因为 mlxtend 库未加载。")
            return pd.DataFrame(columns=['itemsets_readable', 'support', 'length'])
        
        transactions = self.db_manager.get_emotion_transactions(level=level)
        if not transactions:
            logger.info(f"在 {level} 级别未找到用于 Apriori 挖掘的事务数据。")
            return pd.DataFrame()

        # 限制事务数量
        if max_transactions is not None and len(transactions) > max_transactions:
            logger.info(f"事务数从 {len(transactions)} 限制到 {max_transactions}")
            transactions = transactions[:max_transactions]

        # 过滤不满足最小长度的事务
        transactions = [t for t in transactions if len(t) >= min_length]
        if not transactions:
            logger.info("过滤后没有满足最小长度要求的事务。")
            return pd.DataFrame()

        if len(transactions) > 5000:
            logger.warning(f"当前处理的事务数量 ({len(transactions)}) 较大，Apriori 算法可能需要较长时间运行。")

        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        if df_encoded.empty:
            logger.info("编码后的事务数据为空。")
            return pd.DataFrame(columns=['itemsets_readable', 'support', 'length'])

        frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)

        if frequent_itemsets.empty:
            logger.info(f"在最小支持度 {min_support} 下未发现任何高频项集。")
            return pd.DataFrame()

        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
        filtered_itemsets = frequent_itemsets[frequent_itemsets['length'] >= min_length].copy()
        
        if filtered_itemsets.empty:
            return pd.DataFrame()

        id_to_name_map = self.get_emotion_categories_map()
        
        def format_itemset(itemset):
            names = [id_to_name_map.get(id, f"未知 ID({id})") for id in itemset]
            return ', '.join(sorted(names))
        
        filtered_itemsets['itemsets_readable'] = filtered_itemsets['itemsets'].apply(format_itemset)
        result_df = filtered_itemsets[['itemsets_readable', 'support', 'length']].sort_values(by='support', ascending=False)

        logger.debug(f"Apriori 挖掘完成，发现 {len(result_df)} 个高频项集。")
        return result_df

    def clear_cache(self):
        """清除 DataProcessor 的所有 LRU 缓存"""
        self.compute_model_performance.cache_clear()
        self.compute_poem_length_distribution.cache_clear()
        self.compute_model_annotation_trends.cache_clear()
        self.get_emotion_categories_map.cache_clear()
        self.compute_emotion_distribution_frequency.cache_clear()
        self.compute_emotion_distribution_actual.cache_clear()
        self.compute_frequent_emotion_combinations.cache_clear()
        self.compute_frequent_poem_emotion_sets_frequency.cache_clear()
        self.compute_frequent_poem_emotion_sets_actual.cache_clear()
        self.mine_frequent_emotion_itemsets_apriori.cache_clear()
        logger.info("DataProcessor 缓存已清除。")
