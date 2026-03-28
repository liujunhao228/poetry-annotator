"""
控件组件
包含可复用的用户输入控件
"""

from datetime import datetime, timedelta
import streamlit as st


def render_date_range_picker(
    key: str = "date_range",
    default_days: int = 90,
    label: str = "选择标注日期范围"
) -> tuple[str, str]:
    """
    渲染日期范围选择器组件
    
    :param key: Streamlit 组件的唯一 key
    :param default_days: 默认显示的天数范围
    :param label: 标签文本
    :return: (开始日期 ISO 字符串，结束日期 ISO 字符串) 的元组
    """
    today = datetime.now()
    default_start_date = today - timedelta(days=default_days)
    
    date_range = st.date_input(
        label, 
        value=(default_start_date, today), 
        key=key
    )
    
    if len(date_range) == 2:
        start_date_iso = date_range[0].isoformat() + "T00:00:00Z"
        end_date_iso = date_range[1].isoformat() + "T23:59:59Z"
        return start_date_iso, end_date_iso
    else:
        return None, None


def render_top_n_slider(
    key: str,
    label: str,
    min_value: int = 5,
    max_value: int = 50,
    default_value: int = 20
) -> int:
    """
    渲染 Top N 选择滑块组件
    
    :param key: Streamlit 组件的唯一 key
    :param label: 标签文本
    :param min_value: 最小值
    :param max_value: 最大值
    :param default_value: 默认值
    :return: 用户选择的 Top N 值
    """
    return st.slider(label, min_value, max_value, default_value, key=key)


def render_method_radio(
    key: str,
    label: str,
    options: dict,
    horizontal: bool = True
) -> str:
    """
    渲染方法选择单选组件
    
    :param key: Streamlit 组件的唯一 key
    :param label: 标签文本
    :param options: 选项字典 {显示文本：实际值}
    :param horizontal: 是否水平排列
    :return: 用户选择的实际值
    """
    display_options = list(options.keys())
    selected_display = st.radio(
        label, 
        display_options, 
        key=key, 
        horizontal=horizontal
    )
    return options[selected_display]


def render_view_mode_selector(key: str = "view_mode") -> str:
    """
    渲染视图模式选择器组件
    
    :param key: Streamlit 组件的唯一 key
    :return: 选择的视图模式 ("单库分析" 或 "双库对比")
    """
    return st.radio(
        "视图模式:", 
        ("单库分析", "双库对比"), 
        key=key, 
        horizontal=True
    )


def render_db_selector(
    db_paths: dict,
    key: str = "db_selector",
    label: str = "选择数据库:"
) -> str:
    """
    渲染数据库选择器组件
    
    :param db_paths: 数据库路径字典
    :param key: Streamlit 组件的唯一 key
    :param label: 标签文本
    :return: 选择的数据库键
    """
    db_keys_options = list(db_paths.keys())
    return st.selectbox(label, db_keys_options, key=key)


def render_refresh_button(
    key: str,
    label: str = "🔄 刷新",
    help_text: str = None
) -> bool:
    """
    渲染刷新按钮组件
    
    :param key: Streamlit 组件的唯一 key
    :param label: 按钮文本
    :param help_text: 帮助提示
    :return: 是否点击了刷新按钮
    """
    return st.button(label, key=key, help=help_text)


def render_cache_clear_buttons() -> str:
    """
    渲染缓存清除按钮组
    
    :return: 用户操作类型 ("memory", "disk", "all", "none")
    """
    st.markdown("---")
    
    if st.button("清除所有缓存并刷新", help="强制清除所有应用的缓存，从数据库重新加载所有数据。"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        return "all"
    
    from data_visualizer.app.disk_cache_manager import get_disk_cache_manager
    if st.button("🗑️ 清除磁盘缓存", help="清除持久化的磁盘缓存文件，下次加载数据时将重新计算并缓存。"):
        disk_cache_manager = get_disk_cache_manager()
        disk_cache_manager.clear()
        st.success("磁盘缓存已清除！")
        return "disk"
    
    return "none"
