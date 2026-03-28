"""
图表组件
包含可复用的图表渲染组件
"""

import plotly.express as px
import streamlit as st
import pandas as pd


def render_sunburst(
    df: pd.DataFrame, 
    key: str = "sunburst",
    title: str = "情感层级分布",
    show_warning: bool = True
):
    """
    渲染旭日图组件
    
    :param df: 包含 id, parent_id, count, name_zh, percentage 列的 DataFrame
    :param key: Streamlit 组件的唯一 key
    :param title: 图表标题
    :param show_warning: 是否显示空数据警告
    """
    if df.empty:
        if show_warning:
            st.warning("无数据")
        return
    
    try:
        fig = px.sunburst(
            df, 
            ids='id', 
            parents='parent_id', 
            values='count',
            names='name_zh', 
            branchvalues="total", 
            title=title,
            hover_data={'count': True}, 
            custom_data=['name_zh', 'percentage']
        )
        fig.update_traces(
            hovertemplate='<b>%{customdata[0]}</b><br>ID: %{id}<br>出现次数： %{value}<br>占比： %{customdata[1]:.2f}%<extra></extra>'
        )
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True, key=key)
    except Exception as e:
        st.error(f"绘制旭日图时发生错误：{e}")
        st.subheader("用于绘图的数据帧:")
        st.dataframe(df)


def render_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: str = None,
    y_label: str = None,
    key: str = "bar_chart",
    orientation: str = 'v',
    color: str = None,
    barmode: str = 'group'
):
    """
    渲染条形图组件
    
    :param df: 数据 DataFrame
    :param x: x 轴字段名
    :param y: y 轴字段名
    :param title: 图表标题
    :param x_label: x 轴标签
    :param y_label: y 轴标签
    :param key: Streamlit 组件的唯一 key
    :param orientation: 方向 ('v' 垂直，'h' 水平)
    :param color: 颜色分组字段
    :param barmode: 条形图模式 ('group', 'stack', 'overlay')
    """
    if df.empty:
        st.info("暂无数据")
        return
    
    labels = {}
    if x_label:
        labels[x] = x_label
    if y_label:
        labels[y] = y_label
    
    fig = px.bar(
        df, 
        x=x, 
        y=y, 
        color=color,
        barmode=barmode,
        title=title,
        labels=labels,
        orientation=orientation
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: str = None,
    y_label: str = None,
    key: str = "line_chart",
    color: str = None
):
    """
    渲染折线图组件
    
    :param df: 数据 DataFrame
    :param x: x 轴字段名
    :param y: y 轴字段名
    :param title: 图表标题
    :param x_label: x 轴标签
    :param y_label: y 轴标签
    :param key: Streamlit 组件的唯一 key
    :param color: 颜色分组字段
    """
    if df.empty:
        st.info("暂无数据")
        return
    
    labels = {}
    if x_label:
        labels[x] = x_label
    if y_label:
        labels[y] = y_label
    
    fig = px.line(
        df, 
        x=x, 
        y=y, 
        color=color,
        title=title,
        labels=labels
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
