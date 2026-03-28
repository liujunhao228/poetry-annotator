"""
表格组件
包含可复用的表格渲染组件
"""

import streamlit as st
import pandas as pd


def render_model_performance_table(
    df: pd.DataFrame,
    key: str = "model_performance_table"
) -> tuple[int, int, float]:
    """
    渲染模型性能表格组件
    
    :param df: 包含 model_identifier, total_annotations, completed, failed, success_rate 列的 DataFrame
    :param key: Streamlit 组件的唯一 key
    :return: (总标注数，完成数，失败数，总成功率) 的元组
    """
    if df.empty:
        st.info("暂无模型性能数据。")
        return (0, 0, 0, 0.0)
    
    total_annotations = df['total_annotations'].sum()
    completed_annotations = df['completed'].sum()
    failed_annotations = df['failed'].sum()
    overall_success_rate = (completed_annotations / total_annotations * 100) if total_annotations > 0 else 0
    
    # 显示汇总指标
    col1, col2 = st.columns(2)
    with col1:
        st.metric("总标注数", f"{total_annotations:,}")
    with col2:
        st.metric("总成功率", f"{overall_success_rate:.2f}%")
    
    # 显示详细表格
    display_df = df.set_index('model_identifier').copy()
    display_df.columns = ['总标注数', '成功', '失败', '成功率']
    st.dataframe(display_df, use_container_width=True, key=key)
    
    return (total_annotations, completed_annotations, failed_annotations, overall_success_rate)


def render_apriori_table(
    df: pd.DataFrame,
    top_n: int = None,
    key: str = "apriori_table"
):
    """
    渲染 Apriori 挖掘结果表格组件
    
    :param df: 包含 itemsets_readable, support, length 列的 DataFrame
    :param top_n: 显示前 N 条结果，None 表示显示全部
    :param key: Streamlit 组件的唯一 key
    """
    if df.empty:
        st.info("未发现高频情感组合。")
        return
    
    display_df = df.head(top_n) if top_n else df
    
    st.dataframe(
        display_df,
        column_config={
            "itemsets_readable": st.column_config.TextColumn("高频情感组合", width="large"),
            "support": st.column_config.NumberColumn("支持度", format="%.4f"),
            "length": st.column_config.NumberColumn("组合长度")
        },
        use_container_width=True,
        hide_index=True,
        key=key
    )


def render_emotion_combinations_table(
    df: pd.DataFrame,
    key: str = "emotion_combinations_table"
):
    """
    渲染情感共现组合表格组件
    
    :param df: 包含 combination_readable, combo_count, sentence_text 列的 DataFrame
    :param key: Streamlit 组件的唯一 key
    """
    if df.empty:
        st.info("暂无单句内高频情感共现数据。")
        return
    
    st.dataframe(
        df,
        column_config={
            "combination_readable": st.column_config.TextColumn("情感共现组合", width="large"),
            "combo_count": st.column_config.NumberColumn("共现次数", format="%d 次"),
            "sentence_text": st.column_config.TextColumn("示例文本")
        },
        use_container_width=True,
        hide_index=True,
        key=key
    )


def render_poem_emotion_sets_table(
    df: pd.DataFrame,
    key: str = "poem_emotion_sets_table"
):
    """
    渲染全诗情感集合表格组件
    
    :param df: 包含 set_readable, set_count, poem_example 列的 DataFrame
    :param key: Streamlit 组件的唯一 key
    """
    if df.empty:
        st.info("暂无全诗内高频情感集合数据。")
        return
    
    st.dataframe(
        df,
        column_config={
            "set_readable": st.column_config.TextColumn("情感集合", width="large"),
            "set_count": st.column_config.NumberColumn("出现次数", format="%d 首"),
            "poem_example": st.column_config.TextColumn("示例诗词")
        },
        use_container_width=True,
        hide_index=True,
        key=key
    )
