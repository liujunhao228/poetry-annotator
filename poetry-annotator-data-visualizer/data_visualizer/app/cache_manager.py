import streamlit as st
from data_visualizer.db_manager import DBManager
from data_visualizer.data_processor import DataProcessor
from data_visualizer.config import DB_PATHS
from data_visualizer.utils import logger
import os

# --- L3 Cache: Streamlit Application Layer ---
# All cache functions are now parameterized by `db_key` to ensure data isolation.

@st.cache_resource
def get_db_manager(db_key: str) -> DBManager:
    """Gets a cached DBManager instance for a specific database key."""
    if db_key not in DB_PATHS:
        st.error(f"未知的数据库标识符: {db_key}")
        return None
    db_path = DB_PATHS[db_key]
    # 确保数据库文件的目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    logger.info(f"为 '{db_key}' 创建或获取缓存的 DBManager 实例 (路径: {db_path})")
    return DBManager(db_path=db_path)

@st.cache_resource
def get_data_processor(db_key: str) -> DataProcessor:
    """Gets a cached DataProcessor instance for a specific database key."""
    manager = get_db_manager(db_key)
    if manager is None:
        return None
    logger.info(f"为 '{db_key}' 创建或获取缓存的 DataProcessor 实例")
    return DataProcessor(manager)
