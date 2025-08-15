import streamlit as st
import plotly.express as px
import plotly.io as pio
from data_visualizer.app.data_fetcher import (
    get_model_performance_data,
    get_poem_count_by_author_data,
    get_emotion_distribution_data,
    get_frequent_emotion_combinations_data,
    get_frequent_poem_emotion_sets_data_actual,
    get_frequent_poem_emotion_sets_data_frequency,
    get_apriori_results_data,
    get_model_annotation_trends_data
)

def display_model_performance(db_key: str):
    """Displays model performance metrics and table for a given db_key."""
    model_perf_df = get_model_performance_data(db_key)
    if not model_perf_df.empty:
        total_annotations = model_perf_df['total_annotations'].sum()
        completed_annotations = model_perf_df['completed'].sum()
        failed_annotations = model_perf_df['failed'].sum()
        overall_success_rate = (completed_annotations / total_annotations * 100) if total_annotations > 0 else 0
        
        st.metric("总标注数", f"{total_annotations:,}")
        st.metric("总成功率", f"{overall_success_rate:.2f}%")
        
        st.dataframe(model_perf_df.set_index('model_identifier'), use_container_width=True)
    else:
        st.info("暂无模型性能数据。")

def display_author_poem_count(db_key: str, top_n: int = 20):
    """Displays a bar chart of top authors by poem count."""
    author_poem_counts = get_poem_count_by_author_data(db_key)
    if not author_poem_counts.empty:
        fig = px.bar(author_poem_counts.head(top_n), x='author', y='poem_count', 
                     title=f'作品数量最多的创作者 (Top {top_n})', labels={'author': '创作者', 'poem_count': '作品数量'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无诗人作品数量数据。")

def display_emotion_sunburst(db_key: str):
    """Displays the emotion distribution sunburst chart with enhanced download option."""
    sunburst_df = get_emotion_distribution_data(db_key)
    if sunburst_df.empty:
        st.warning(f"数据库 '{db_key}' 中未找到情感分布数据。")
        return
        
    try:
        fig = px.sunburst(
            sunburst_df, ids='id', parents='parent_id', values='count',
            names='name_zh', branchvalues="total", title="情感层级分布",
            hover_data={'count': True}, custom_data=['name_zh', 'percentage']
        )
        fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>ID: %{id}<br>出现次数: %{value}<br>占比: %{customdata[1]:.2f}%<extra></extra>')
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加自定义下载按钮
        # 创建一个两列布局，将按钮放在右侧
        _, download_col = st.columns([0.85, 0.15])
        with download_col:
            # 使用滑块让用户选择图片分辨率
            resolution = st.slider("下载分辨率 (DPI)", 100, 600, 300, 50, key=f"resolution_slider_{db_key}")
            
            # 确保在导出前正确应用模板和颜色序列
            fig_for_export = fig.update_layout(
                template="plotly",
                colorway=px.colors.qualitative.Set1  # 显式设置颜色序列
            )
            
            # 使用原始图表对象导出，确保颜色正确保留
            img_bytes = fig_for_export.to_image(
                format="png", 
                width=1200, 
                height=900, 
                scale=resolution/100
            )
            
            # 创建下载按钮
            st.download_button(
                label="📥 下载高清图",
                data=img_bytes,
                file_name=f"emotion_sunburst_{db_key}_{resolution}dpi.png",
                mime="image/png",
                help=f"下载分辨率为 {resolution} DPI 的高清旭日图"
            )
    except Exception as e:
        st.error(f"为 '{db_key}' 绘制旭日图时发生错误: {e}")
        st.subheader("用于绘图的数据帧:")
        st.dataframe(sunburst_df)

def display_frequent_combinations(db_key: str, top_n: int):
    """Displays frequent emotion combinations in a dataframe."""
    combo_df = get_frequent_emotion_combinations_data(db_key, top_n)
    if not combo_df.empty:
        st.dataframe(combo_df, column_config={"combination_readable": st.column_config.TextColumn("情感共现组合", width="large"), "combo_count": st.column_config.NumberColumn("共现次数", format="%d 次"), "sentence_text": st.column_config.TextColumn("示例文本")}, use_container_width=True, hide_index=True)
    else:
        st.info("暂无单句内高频情感共现数据。")
