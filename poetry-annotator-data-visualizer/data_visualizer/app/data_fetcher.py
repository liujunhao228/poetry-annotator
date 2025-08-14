import streamlit as st
from data_visualizer.app.cache_manager import get_data_processor, get_db_manager

# --- Data Fetching Functions (parameterized by db_key) ---

@st.cache_data(show_spinner="正在加载模型性能数据...")
def get_model_performance_data(db_key: str):
    processor = get_data_processor(db_key)
    return processor.compute_model_performance()

@st.cache_data(show_spinner="正在加载标注趋势数据...")
def get_model_annotation_trends_data(db_key: str, start_date_iso, end_date_iso):
    processor = get_data_processor(db_key)
    return processor.compute_model_annotation_trends(start_date_iso, end_date_iso)

@st.cache_data(show_spinner="正在加载诗人作品数量数据...")
def get_poem_count_by_author_data(db_key: str):
    manager = get_db_manager(db_key)
    return manager.get_poem_count_by_author()

@st.cache_data(show_spinner="正在加载诗词长度分布数据...")
def get_poem_length_distribution_data(db_key: str, method: str):
    processor = get_data_processor(db_key)
    return processor.compute_poem_length_distribution(method=method)

@st.cache_data(show_spinner="正在加载情感分布数据...")
def get_emotion_distribution_data(db_key: str):
    processor = get_data_processor(db_key)
    sunburst_df = processor.compute_emotion_distribution()
    return sunburst_df

@st.cache_data(show_spinner="正在加载高频情感共现...")
def get_frequent_emotion_combinations_data(db_key: str, top_n: int):
    processor = get_data_processor(db_key)
    return processor.compute_frequent_emotion_combinations(limit=top_n)

@st.cache_data(show_spinner="正在加载全诗情感集合...")
def get_frequent_poem_emotion_sets_data(db_key: str, top_n: int):
    processor = get_data_processor(db_key)
    return processor.compute_frequent_poem_emotion_sets(limit=top_n)

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
    processor = get_data_processor(db_key)
    return processor.mine_frequent_emotion_itemsets_apriori(
        level=level, min_support=min_support, min_length=min_length, max_transactions=max_transactions
    )
