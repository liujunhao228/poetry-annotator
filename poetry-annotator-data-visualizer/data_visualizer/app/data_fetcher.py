import streamlit as st
import hashlib
from data_visualizer.app.cache_manager import get_data_processor, get_db_manager
from data_visualizer.app.disk_cache_manager import get_disk_cache_manager

# 获取全局磁盘缓存管理器实例
disk_cache = get_disk_cache_manager()

# --- Data Fetching Functions (parameterized by db_key) ---
# 重构说明：
# 1. 每个函数内部增加了磁盘缓存逻辑。
# 2. 缓存键由函数名、db_key和所有影响结果的参数生成。
# 3. 如果磁盘缓存命中，则直接返回缓存数据，跳过后续计算。
# 4. 如果未命中，则执行原始逻辑，并将最终结果存入磁盘缓存。
# 5. TTL (Time-To-Live) 根据数据类型设定，静态数据长，动态/计算密集型短。

def _get_cache_key(func_name: str, db_key: str, **kwargs) -> str:
    """生成统一的缓存键。"""
    sorted_items = str(sorted(kwargs.items()))
    raw_key = f"{func_name}:{db_key}:{sorted_items}"
    return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

@st.cache_data(show_spinner="正在加载模型性能数据...")
def get_model_performance_data(db_key: str):
    # 1. 生成缓存键
    cache_key = _get_cache_key("get_model_performance_data", db_key)
    # 2. 尝试从磁盘缓存获取
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    # 3. 磁盘缓存未命中，执行原始逻辑
    processor = get_data_processor(db_key)
    df = processor.compute_model_performance()
    # 4. 将结果存入磁盘缓存 (例如，缓存1小时)
    disk_cache.set(cache_key, df, ttl=3600)
    return df

@st.cache_data(show_spinner="正在加载标注趋势数据...")
def get_model_annotation_trends_data(db_key: str, start_date_iso, end_date_iso):
    cache_key = _get_cache_key("get_model_annotation_trends_data", db_key, start_date_iso=start_date_iso, end_date_iso=end_date_iso)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_model_annotation_trends(start_date_iso, end_date_iso)
    # 趋势数据变化较频繁，缓存10分钟
    disk_cache.set(cache_key, df, ttl=600)
    return df

@st.cache_data(show_spinner="正在加载诗人作品数量数据...")
def get_poem_count_by_author_data(db_key: str):
    cache_key = _get_cache_key("get_poem_count_by_author_data", db_key)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    manager = get_db_manager(db_key)
    df = manager.get_poem_count_by_author()
    # 作者作品数相对稳定，缓存30分钟
    disk_cache.set(cache_key, df, ttl=1800)
    return df

@st.cache_data(show_spinner="正在加载诗词长度分布数据...")
def get_poem_length_distribution_data(db_key: str, method: str):
    cache_key = _get_cache_key("get_poem_length_distribution_data", db_key, method=method)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_poem_length_distribution(method=method)
    # 长度分布相对稳定，缓存30分钟
    disk_cache.set(cache_key, df, ttl=1800)
    return df

@st.cache_data(show_spinner="正在加载情感分布数据...")
def get_emotion_distribution_data(db_key: str):
    cache_key = _get_cache_key("get_emotion_distribution_data", db_key)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_emotion_distribution_actual()
    # 情感分布计算较重，缓存1小时
    disk_cache.set(cache_key, df, ttl=3600)
    return df

@st.cache_data(show_spinner="正在加载高频情感共现...")
def get_frequent_emotion_combinations_data(db_key: str, top_n: int):
    cache_key = _get_cache_key("get_frequent_emotion_combinations_data", db_key, top_n=top_n)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_frequent_emotion_combinations(limit=top_n)
    # 高频共现计算较重，缓存30分钟
    disk_cache.set(cache_key, df, ttl=1800)
    return df

@st.cache_data(show_spinner="正在加载全诗情感集合(实际)...")
def get_frequent_poem_emotion_sets_data_actual(db_key: str, top_n: int):
    cache_key = _get_cache_key("get_frequent_poem_emotion_sets_data_actual", db_key, top_n=top_n)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_frequent_poem_emotion_sets_actual(limit=top_n)
    # 全诗情感集合计算较重，缓存30分钟
    disk_cache.set(cache_key, df, ttl=1800)
    return df

@st.cache_data(show_spinner="正在加载全诗情感集合(频率)...")
def get_frequent_poem_emotion_sets_data_frequency(db_key: str, top_n: int):
    cache_key = _get_cache_key("get_frequent_poem_emotion_sets_data_frequency", db_key, top_n=top_n)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.compute_frequent_poem_emotion_sets_frequency(limit=top_n)
    # 全诗情感集合计算较重，缓存30分钟
    disk_cache.set(cache_key, df, ttl=1800)
    return df

# [OPTIMIZATION 3.4] 添加 max_transactions 参数
@st.cache_data(show_spinner="正在进行 Apriori 挖掘...")
def get_apriori_results_data(db_key: str, level: str, min_support: float, min_length: int, max_transactions: int = None):
    """
    获取 Apriori 挖掘结果数据。
    
    :param db_key: 数据库键
    :param level: 分析层级 ('sentence' 或 'poem')
    :param min_support: 最小支持度阈值 (0 到 1 之间)
    :param min_length: 项集的最短长度
    :param max_transactions: 最大事务数，用于限制计算规模。如果为 None，则不限制。
    :return: 包含高频项集、支持度和可读名称的 DataFrame
    """
    cache_key = _get_cache_key("get_apriori_results_data", db_key, level=level, min_support=min_support, min_length=min_length, max_transactions=max_transactions)
    cached_df = disk_cache.get(cache_key)
    if cached_df is not None:
        return cached_df
    processor = get_data_processor(db_key)
    df = processor.mine_frequent_emotion_itemsets_apriori(
        level=level, min_support=min_support, min_length=min_length, max_transactions=max_transactions
    )
    # Apriori挖掘非常耗时，缓存时间可以稍长，但建议用户手动清除
    disk_cache.set(cache_key, df, ttl=7200) # 缓存2小时
    return df
