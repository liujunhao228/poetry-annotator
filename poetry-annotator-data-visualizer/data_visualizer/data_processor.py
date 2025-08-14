import pandas as pd
from functools import lru_cache
from data_visualizer.db_manager import DBManager
from data_visualizer.config import CACHE_MAX_SIZE_DATA_PROCESSING
from data_visualizer.utils import logger

# 确保 mlxtend 已安装: pip install mlxtend
try:
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori
    # 尝试导入 tqdm 用于进度显示
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    logger.error("mlxtend 库未安装，Apriori 高级挖掘功能将不可用。请运行 'pip install mlxtend'。")
    TransactionEncoder = None
    apriori = None
    TQDM_AVAILABLE = False

class DataProcessor:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_model_performance(self) -> pd.DataFrame:
        """
        计算各模型的性能指标（成功率等）。
        利用 DBManager 缓存的原始聚合数据，在此进行进一步计算。
        """
        df_summary = self.db_manager.get_annotation_summary_by_model()
        if df_summary.empty:
            logger.warning("无标注汇总数据用于模型性能计算。")
            return pd.DataFrame(columns=['model_identifier', 'total_annotations', 'completed', 'failed', 'success_rate'])

        # 将状态列转换为单独的列，并填充0
        pivot_df = df_summary.pivot_table(index='model_identifier', columns='status', values='count', fill_value=0)
        
        # 确保存在 'completed' 和 'failed' 列，即使某个模型没有对应的状态
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

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_poem_length_distribution(self, method: str = 'words') -> pd.DataFrame:
        """
        计算诗词长度分布。
        :param method: 统计方法 ('words' 或 'characters')
        """
        poems_df = self.db_manager.get_all_poems()
        if poems_df.empty:
            logger.warning("无诗词数据用于长度分布计算。")
            return pd.DataFrame()

        def calculate_length(text, m):
            if not isinstance(text, str): # Handle potential non-string types
                return 0
            if m == 'words':
                return len(text.split())
            elif m == 'characters':
                return len(text)
            return 0
        
        # 只在计算时加载需要的列
        poems_df['poem_length'] = poems_df['full_text'].apply(lambda x: calculate_length(x, method))

        # 定义长度区间
        bins = [0, 50, 100, 150, 200, 300, 500, float('inf')]
        labels = ['0-50', '51-100', '101-150', '151-200', '201-300', '301-500', '500+']
        
        # 使用pd.cut创建长度区间分类
        poems_df['length_band'] = pd.cut(poems_df['poem_length'], bins=bins, labels=labels, right=True, include_lowest=True)

        distribution = poems_df['length_band'].value_counts().sort_index().reset_index()
        distribution.columns = ['length_band', 'count']
        logger.debug(f"诗词长度分布 ({method}) 计算完成。")
        return distribution

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_model_annotation_trends(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        按模型计算每日标注趋势。
        直接从 DBManager 获取已过滤日期的数据。
        :param start_date: 开始日期
        :param end_date: 结束日期
        """
        df = self.db_manager.get_annotations_with_poem_info(start_date, end_date)
        if df.empty:
            logger.warning(f"在 {start_date} 到 {end_date} 范围内无标注数据用于趋势分析。")
            return pd.DataFrame()

        # 转换为日期格式进行分组
        df['annotation_date'] = pd.to_datetime(df['annotation_created_at']).dt.date
        
        # 按日期、模型、状态分组计数
        trends_df = df.groupby(['annotation_date', 'model_identifier', 'status']).size().unstack(fill_value=0).reset_index()
        
        # 确保 'completed' 和 'failed' 列存在
        if 'completed' not in trends_df.columns:
            trends_df['completed'] = 0
        if 'failed' not in trends_df.columns:
            trends_df['failed'] = 0

        trends_df['total_annotations'] = trends_df['completed'] + trends_df['failed']
        
        logger.debug(f"模型标注趋势 ({start_date}-{end_date}) 计算完成。")
        return trends_df.sort_values(['annotation_date', 'model_identifier'])

    # --- 情感分析处理方法 ---
    @lru_cache(maxsize=1) # 情感类别基本不变，缓存1条即可
    def get_emotion_categories_map(self) -> dict:
        """获取情感ID到中文名的映射字典，用于后续转换。"""
        df = self.db_manager.get_all_emotion_categories()
        if df.empty:
            logger.warning("未能加载情感分类映射，后续可读性转换将受影响。")
            return {}
        return df.set_index('id')['name_zh'].to_dict()

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_emotion_distribution_frequency(self) -> pd.DataFrame:
        """
        【已修正】计算情感分布（基于所有标注），为旭日图准备完整层级的数据。
        此版本通过手动计算父节点的计数值，确保旭日图的稳健渲染，避免内外圈比例失衡。
        """
        all_categories_df = self.db_manager.get_all_emotion_categories()
        if all_categories_df.empty:
            logger.warning("情感分类表为空，无法计算分布。")
            return pd.DataFrame()

        # --- 数据预处理，提高健壮性 ---
        all_categories_df['id'] = all_categories_df['id'].astype(str)
        # 清理父ID，确保与子ID的ID格式一致
        all_categories_df['parent_id'] = all_categories_df['parent_id'].fillna('').astype(str)
        # 顶级分类的 parent_id 应为空字符串，以作为旭日图的根
        all_categories_df.loc[all_categories_df['level'] == 1, 'parent_id'] = ''

        # --- 获取叶子节点（二级分类）的计数值 ---
        # get_emotion_distribution_frequency 只返回有标注记录的叶子节点及其count
        leaf_dist_df = self.db_manager.get_emotion_distribution_frequency()
        if leaf_dist_df.empty:
            logger.warning("无情感标注数据用于分布计算。将返回所有分类，但计数值均为0。")
            all_categories_df['count'] = 0
            all_categories_df['percentage'] = 0.0
            return all_categories_df

        # --- 合并数据并计算父节点计数值 ---
        # 将叶子节点的计数值合并到完整的分类表中
        merged_df = pd.merge(
            all_categories_df,
            leaf_dist_df[['id', 'count']],
            on='id',
            how='left'
        )
        # 未匹配到的计数值（包括所有父节点和未出现的叶子节点）填充为0
        merged_df['count'] = merged_df['count'].fillna(0).astype(int)

        # --- 核心修复：手动计算父节点的 count ---
        # 1. 按 parent_id 分组，计算每个父节点下所有子节点的 count 总和
        parent_sums = merged_df[merged_df['level'] == 2].groupby('parent_id')['count'].sum()
        
        # 2. 将计算出的总和更新（赋值）到父节点（一级分类）的 'count' 列中
        #    使用 .map() 将 parent_sums 映射回 merged_df，确保数据对齐
        #    这可以防止父节点计数值被重复计算或遗漏
        parent_ids_series = merged_df.loc[merged_df['level'] == 1, 'id']
        parent_counts = parent_ids_series.map(parent_sums).fillna(0).astype(int)
        
        # 使用 .loc 进行安全的赋值
        merged_df.loc[merged_df['level'] == 1, 'count'] = parent_counts

        # --- [新增] 添加百分比计算逻辑 ---
        total_emotion_count = merged_df['count'].sum()
        if total_emotion_count > 0:
            merged_df['percentage'] = (merged_df['count'] / total_emotion_count * 100).round(2)
        else:
            merged_df['percentage'] = 0.0

        return merged_df

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_emotion_distribution_actual(self) -> pd.DataFrame:
        """
        【已修正】计算情感分布（基于最新标注），为旭日图准备完整层级的数据。
        此版本通过手动计算父节点的计数值，确保旭日图的稳健渲染，避免内外圈比例失衡。
        """
        all_categories_df = self.db_manager.get_all_emotion_categories()
        if all_categories_df.empty:
            logger.warning("情感分类表为空，无法计算分布。")
            return pd.DataFrame()

        # --- 数据预处理，提高健壮性 ---
        all_categories_df['id'] = all_categories_df['id'].astype(str)
        # 清理父ID，确保与子ID的ID格式一致
        all_categories_df['parent_id'] = all_categories_df['parent_id'].fillna('').astype(str)
        # 顶级分类的 parent_id 应为空字符串，以作为旭日图的根
        all_categories_df.loc[all_categories_df['level'] == 1, 'parent_id'] = ''

        # --- 获取叶子节点（二级分类）的计数值 ---
        # get_emotion_distribution_actual 只返回有标注记录的叶子节点及其count
        leaf_dist_df = self.db_manager.get_emotion_distribution_actual()
        if leaf_dist_df.empty:
            logger.warning("无情感标注数据用于分布计算。将返回所有分类，但计数值均为0。")
            all_categories_df['count'] = 0
            all_categories_df['percentage'] = 0.0
            return all_categories_df

        # --- 合并数据并计算父节点计数值 ---
        # 将叶子节点的计数值合并到完整的分类表中
        merged_df = pd.merge(
            all_categories_df,
            leaf_dist_df[['id', 'count']],
            on='id',
            how='left'
        )
        # 未匹配到的计数值（包括所有父节点和未出现的叶子节点）填充为0
        merged_df['count'] = merged_df['count'].fillna(0).astype(int)

        # --- 核心修复：手动计算父节点的 count ---
        # 1. 按 parent_id 分组，计算每个父节点下所有子节点的 count 总和
        parent_sums = merged_df[merged_df['level'] == 2].groupby('parent_id')['count'].sum()
        
        # 2. 将计算出的总和更新（赋值）到父节点（一级分类）的 'count' 列中
        #    使用 .map() 将 parent_sums 映射回 merged_df，确保数据对齐
        #    这可以防止父节点计数值被重复计算或遗漏
        parent_ids_series = merged_df.loc[merged_df['level'] == 1, 'id']
        parent_counts = parent_ids_series.map(parent_sums).fillna(0).astype(int)
        
        # 使用 .loc 进行安全的赋值
        merged_df.loc[merged_df['level'] == 1, 'count'] = parent_counts

        # --- [新增] 添加百分比计算逻辑 ---
        total_emotion_count = merged_df['count'].sum()
        if total_emotion_count > 0:
            merged_df['percentage'] = (merged_df['count'] / total_emotion_count * 100).round(2)
        else:
            merged_df['percentage'] = 0.0

        return merged_df


    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_frequent_emotion_combinations(self, limit: int = 20) -> pd.DataFrame:
        """处理高频情感共现数据，将ID转换为可读文本。"""
        combos_df = self.db_manager.get_frequent_emotion_combinations(limit=limit)
        if combos_df.empty:
            logger.info("无高频情感共现数据。")
            return pd.DataFrame()
        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            # 如果映射表为空，直接返回原始id，避免程序崩溃
            combos_df['combination_readable'] = combos_df['emotion_combo_ids']
            return combos_df

        def format_cooccurrence(id_string):
            if not isinstance(id_string, str):
                return "无效组合"
            
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知ID({id})") for id in ids]
            
            # 不再区分主次，直接用逗号连接
            return ', '.join(names)

        combos_df['combination_readable'] = combos_df['emotion_combo_ids'].apply(format_cooccurrence)
        logger.debug(f"高频情感共现 (Top {limit}) 数据计算完成。")
        # 返回对前端友好的列
        return combos_df[['combination_readable', 'combo_count', 'sentence_text']]

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_frequent_poem_emotion_sets_frequency(self, limit: int = 20) -> pd.DataFrame:
        """处理高频全诗情感集合数据（基于所有标注），将ID转换为可读文本。"""
        sets_df = self.db_manager.get_frequent_poem_emotion_sets_frequency(limit=limit)
        if sets_df.empty:
            logger.info("无高频全诗情感集合数据。")
            return pd.DataFrame()
        
        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            # 如果映射表为空，直接返回原始id，避免程序崩溃
            sets_df['set_readable'] = sets_df['emotion_set_ids']
            return sets_df

        def format_set(id_string):
            if not isinstance(id_string, str):
                return "无效集合"
            
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知ID({id})") for id in ids]
            return ', '.join(names)

        sets_df['set_readable'] = sets_df['emotion_set_ids'].apply(format_set)
        logger.debug(f"高频全诗情感集合 (Top {limit}) 数据计算完成。")
        # 返回对前端友好的列
        return sets_df[['set_readable', 'set_count', 'poem_example']]

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def compute_frequent_poem_emotion_sets_actual(self, limit: int = 20) -> pd.DataFrame:
        """处理高频全诗情感集合数据（基于最新标注），将ID转换为可读文本。"""
        sets_df = self.db_manager.get_frequent_poem_emotion_sets_actual(limit=limit)
        if sets_df.empty:
            logger.info("无高频全诗情感集合数据。")
            return pd.DataFrame()
        
        id_to_name_map = self.get_emotion_categories_map()
        if not id_to_name_map:
            # 如果映射表为空，直接返回原始id，避免程序崩溃
            sets_df['set_readable'] = sets_df['emotion_set_ids']
            return sets_df

        def format_set(id_string):
            if not isinstance(id_string, str):
                return "无效集合"
            
            ids = id_string.strip(';').split(';')
            names = [id_to_name_map.get(id, f"未知ID({id})") for id in ids]
            return ', '.join(names)

        sets_df['set_readable'] = sets_df['emotion_set_ids'].apply(format_set)
        logger.debug(f"高频全诗情感集合 (Top {limit}) 数据计算完成。")
        # 返回对前端友好的列
        return sets_df[['set_readable', 'set_count', 'poem_example']]

    @lru_cache(maxsize=CACHE_MAX_SIZE_DATA_PROCESSING)
    def mine_frequent_emotion_itemsets_apriori(self, level: str, min_support: float, min_length: int = 2, max_transactions: int = None) -> pd.DataFrame:
        """
        使用 Apriori 算法挖掘高频情感项集。
        :param level: 分析层级 ('sentence' 或 'poem')。
        :param min_support: 最小支持度阈值 (0 到 1 之间)。
        :param min_length: 项集的最短长度（例如，2表示至少包含两种情感）。
        :param max_transactions: 最大事务数，用于限制计算规模。如果为 None，则不限制。
        :return: 包含高频项集、支持度和可读名称的 DataFrame。
        """
        if apriori is None:
            logger.error("无法执行 Apriori 挖掘，因为 mlxtend 库未加载。")
            return pd.DataFrame(columns=['itemsets_readable', 'support', 'length'])
        transactions = self.db_manager.get_emotion_transactions(level=level)
        if not transactions:
            logger.info(f"在 {level} 级别未找到用于 Apriori 挖掘的事务数据。")
            return pd.DataFrame()
        
        # 限制事务数量以提高性能（如果指定了最大事务数）
        original_count = len(transactions)
        if max_transactions is not None and len(transactions) > max_transactions:
            logger.info(f"事务数从 {original_count} 限制到 {max_transactions}")
            transactions = transactions[:max_transactions]
        
        # 提前过滤不满足最小长度的事务
        transactions = [t for t in transactions if len(t) >= min_length]
        if not transactions:
            logger.info("过滤后没有满足最小长度要求的事务。")
            return pd.DataFrame()
            
        # 检查事务数量是否过大，给出警告
        warning_threshold = 5000  # 超过此值会记录警告
        if len(transactions) > warning_threshold:
            logger.warning(f"当前处理的事务数量 ({len(transactions)}) 较大，Apriori 算法可能需要较长时间运行。")
            
        # 1. 将事务数据转换为 one-hot 编码的 DataFrame
        te = TransactionEncoder()
        
        # 显示进度条（如果可用）
        if TQDM_AVAILABLE:
            print("正在转换事务数据...")
            te_ary = te.fit(transactions).transform(tqdm(transactions, desc="转换事务数据", unit="事务"))
        else:
            te_ary = te.fit(transactions).transform(transactions)
            
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
        
        # 如果数据框为空，直接返回空结果
        if df_encoded.empty:
            logger.info("编码后的事务数据为空。")
            return pd.DataFrame(columns=['itemsets_readable', 'support', 'length'])
            
        # 检查编码后的数据维度，给出警告
        if len(df_encoded.columns) > 100:  # 如果情感类别过多
            logger.warning(f"情感类别数量较多 ({len(df_encoded.columns)})，Apriori 算法可能需要较长时间运行。")
            
        # 2. 运行 Apriori 算法
        print(f"正在执行 Apriori 算法 (最小支持度: {min_support})...")
        # 使用 tqdm 显示进度（如果可用）
        if TQDM_AVAILABLE:
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True, verbose=1)
        else:
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
            
        if frequent_itemsets.empty:
            logger.info(f"在最小支持度 {min_support} 下未发现任何高频项集。")
            return pd.DataFrame()
            
        # 3. 结果格式化和转换
        # 计算项集长度用于筛选
        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
        
        # 筛选出长度符合要求的项集
        filtered_itemsets = frequent_itemsets[frequent_itemsets['length'] >= min_length].copy()
        if filtered_itemsets.empty:
            return pd.DataFrame()
            
        # 获取情感ID到名称的映射
        id_to_name_map = self.get_emotion_categories_map()
        def format_itemset(itemset):
            # itemset 是一个 frozenset，例如 frozenset({'E1', 'E2'})
            names = [id_to_name_map.get(id, f"未知ID({id})") for id in itemset]
            return ', '.join(sorted(names))
        filtered_itemsets['itemsets_readable'] = filtered_itemsets['itemsets'].apply(format_itemset)
        
        # 重新排序列，并按支持度降序排序
        result_df = filtered_itemsets[['itemsets_readable', 'support', 'length']].sort_values(by='support', ascending=False)
        
        logger.debug(f"Apriori 挖掘完成，发现 {len(result_df)} 个高频项集 (min_support={min_support}, min_length={min_length})。")
        return result_df

    def clear_cache(self):
        """清除DataProcessor的所有LRU缓存."""
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
