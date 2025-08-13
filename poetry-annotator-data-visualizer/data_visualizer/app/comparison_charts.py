import streamlit as st
import plotly.express as px
import pandas as pd
from data_visualizer.app.data_fetcher import (
    get_poem_length_distribution_data,
    get_model_annotation_trends_data
)

def display_poem_length_comparison_chart(db_keys: list, method: str, method_display: str):
    """Displays an overlayed bar chart for poem length distribution."""
    combined_df = pd.DataFrame()
    for db_key in db_keys:
        df = get_poem_length_distribution_data(db_key, method=method)
        if not df.empty:
            df['source'] = db_key
            combined_df = pd.concat([combined_df, df], ignore_index=True)

    if not combined_df.empty:
        fig = px.bar(combined_df, x='length_band', y='count', color='source', barmode='group',
                     title=f'诗词长度分布对比 ({method_display})',
                     labels={'length_band': '长度区间', 'count': '数量', 'source': '数据源'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据进行诗词长度对比。")

def display_annotation_trend_comparison_chart(db_keys: list, start_date_iso, end_date_iso):
    """Displays an overlayed line chart for annotation trends."""
    combined_df = pd.DataFrame()
    for db_key in db_keys:
        df = get_model_annotation_trends_data(db_key, start_date_iso, end_date_iso)
        if not df.empty:
            df['source'] = db_key
            combined_df = pd.concat([combined_df, df], ignore_index=True)

    if not combined_df.empty:
        trend_chart_df = combined_df.groupby(['annotation_date', 'source']).agg(
            completed=('completed', 'sum'), failed=('failed', 'sum')
        ).reset_index()
        fig = px.line(trend_chart_df, x='annotation_date', y='completed', color='source',
                      title='每日成功标注数量趋势对比', 
                      labels={'completed': '成功标注数量', 'annotation_date': '日期', 'source': '数据源'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("所选日期范围内无数据进行标注趋势对比。")
