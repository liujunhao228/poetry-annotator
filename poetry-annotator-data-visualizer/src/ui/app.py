"""
Streamlit 应用入口
重构后的主应用文件
"""

import streamlit as st
from datetime import datetime

from data_visualizer.config import APP_TITLE, DB_PATHS
from data_visualizer.utils import logger
from src.config_loader import get_config_loader
from src.core.cache import get_cache_manager
from src.services.model_service import ModelService
from src.services.poem_service import PoemService
from src.services.emotion_service import EmotionService
from src.ui.components.controls import render_view_mode_selector, render_db_selector, render_date_range_picker
from src.ui.pages.single_analysis import SingleAnalysisPage
from src.ui.pages.comparison_analysis import ComparisonAnalysisPage


def create_services(db_key: str, cache_manager):
    """为指定数据库创建服务实例"""
    from src.core.db_manager import DBManager
    from src.core.data_processor import DataProcessor
    
    db_manager = DBManager(DB_PATHS[db_key])
    return (
        ModelService(db_manager, cache_manager),
        PoemService(db_manager, cache_manager),
        EmotionService(db_manager, cache_manager)
    )


def run_app():
    """主应用入口函数"""
    st.set_page_config(layout="wide", page_title=APP_TITLE)
    st.title(APP_TITLE)
    
    # 加载配置
    config_loader = get_config_loader()
    ui_config = config_loader.get_ui_config()
    
    # 获取缓存管理器
    cache_config = config_loader.get_cache_config()
    cache_manager = get_cache_manager(
        cache_dir=cache_config.get('cache_dir', '.cache'),
        max_memory_items=cache_config.get('max_memory_items', 100)
    )
    
    # --- 侧边栏控制面板 ---
    with st.sidebar:
        st.title("控制面板")
        
        # 缓存管理
        st.markdown("---")
        if st.button("清除所有缓存并刷新", help="强制清除所有应用的缓存，从数据库重新加载所有数据。"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            cache_manager.clear()
            logger.info("所有缓存已清除，应用即将刷新。")
            st.rerun()
        
        if st.button("🗑️ 清除磁盘缓存", help="清除持久化的磁盘缓存文件"):
            cache_manager.clear()
            st.success("磁盘缓存已清除！")
            logger.info("用户手动清除了磁盘缓存。")
        
        st.markdown("---")
        
        # 视图模式选择
        view_mode = render_view_mode_selector()
        
        # 数据库选择
        selected_db_key = None
        if view_mode == "单库分析":
            selected_db_key = render_db_selector(DB_PATHS)
        
        st.markdown("---")
        st.header("数据过滤")
        
        # 日期范围选择
        default_days = ui_config.get('default_date_range_days', 90)
        start_date_iso, end_date_iso = render_date_range_picker(
            key="annotation_date_filter",
            default_days=default_days
        )
    
    # --- 主内容区域 ---
    if view_mode == "单库分析":
        if selected_db_key:
            # 创建服务实例
            model_service, poem_service, emotion_service = create_services(selected_db_key, cache_manager)
            
            # 渲染单库分析页面
            page = SingleAnalysisPage(
                selected_db_key,
                model_service,
                poem_service,
                emotion_service
            )
            page.render(start_date_iso, end_date_iso)
    else:
        # 双库对比模式
        db_keys = list(DB_PATHS.keys())[:2]
        
        if len(db_keys) >= 2:
            # 为两个数据库创建服务实例
            services1 = create_services(db_keys[0], cache_manager)
            services2 = create_services(db_keys[1], cache_manager)
            
            # 渲染对比分析页面
            page = ComparisonAnalysisPage(
                db_keys,
                [services1[0], services2[0]],  # ModelService
                [services1[1], services2[1]],  # PoemService
                [services1[2], services2[2]]   # EmotionService
            )
            page.render(start_date_iso, end_date_iso)
        else:
            st.warning("对比模式需要至少两个数据库。")


if __name__ == '__main__':
    logger.info(f"启动 {APP_TITLE} Streamlit 应用...")
    logger.info(f"使用的数据库路径：{DB_PATHS}")
    run_app()
