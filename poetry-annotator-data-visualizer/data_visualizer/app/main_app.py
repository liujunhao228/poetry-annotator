import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from data_visualizer.config import APP_TITLE, DB_PATHS
from data_visualizer.utils import logger
from data_visualizer.app.cache_manager import get_db_manager, get_data_processor
from data_visualizer.app.data_fetcher import (
    get_model_performance_data,
    get_poem_count_by_author_data,
    get_emotion_distribution_data,
    get_frequent_emotion_combinations_data,
    get_frequent_poem_emotion_sets_data,
    get_apriori_results_data,
    get_model_annotation_trends_data,
    get_poem_length_distribution_data
)
from data_visualizer.app.ui_components import (
    display_model_performance,
    display_author_poem_count,
    display_emotion_sunburst,
    display_frequent_combinations
)
from data_visualizer.app.comparison_charts import (
    display_poem_length_comparison_chart,
    display_annotation_trend_comparison_chart
)

def run_app():
    """Main function to run the Streamlit application."""
    st.set_page_config(layout="wide", page_title=APP_TITLE)
    st.title(APP_TITLE)

    # --- Sidebar Controls ---
    with st.sidebar:
        st.title("控制面板")

        if st.button("清除所有缓存并刷新", help="强制清除所有应用的缓存，从数据库重新加载所有数据。"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear() # 清除会话状态
            logger.info("所有缓存已清除，应用即将刷新。")
            st.rerun()

        st.markdown("---")
        
        view_mode = st.radio("视图模式:", ("单库分析", "双库对比"), key="view_mode_selector", horizontal=True)

        db_keys_options = list(DB_PATHS.keys())
        selected_db_key = None
        if view_mode == "单库分析":
            selected_db_key = st.selectbox("选择数据库:", db_keys_options)
        
        st.markdown("---")
        st.header("数据过滤")
        today = datetime.now()
        default_start_date = today - timedelta(days=90)
        date_range = st.date_input("选择标注日期范围", value=(default_start_date, today), key="annotation_date_filter")
        if len(date_range) == 2:
            start_date_iso = date_range[0].isoformat() + "T00:00:00Z"
            end_date_iso = date_range[1].isoformat() + "T23:59:59Z"
        else:
            start_date_iso, end_date_iso = None, None

    # --- Main Panel with Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["标注分析", "诗词数据概览", "情感分析", "关于与性能"])

    if view_mode == "单库分析":
        if selected_db_key:
            with tab1:
                st.header(f"标注结果分析: {selected_db_key}")
                st.subheader("模型性能总览")
                display_model_performance(selected_db_key)
                
                header_col, button_col = st.columns([0.85, 0.15])
                with header_col:
                    st.subheader("标注趋势")
                with button_col:
                    if st.button("🔄 刷新趋势", key=f"refresh_trends_{selected_db_key}", help="仅重新加载趋势数据"):
                        get_model_annotation_trends_data.clear()

                trends_df = get_model_annotation_trends_data(selected_db_key, start_date_iso, end_date_iso)
                if not trends_df.empty:
                    fig_trend = px.line(trends_df.groupby('annotation_date')['completed'].sum().reset_index(), 
                                        x='annotation_date', y='completed', title="每日成功标注数量",
                                        labels={'completed': '成功标注数', 'annotation_date': '日期'})
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("所选日期范围内无标注趋势数据。")

            with tab2:
                st.header(f"诗词数据概览: {selected_db_key}")
                
                header_col, button_col = st.columns([0.85, 0.15])
                with header_col:
                    st.subheader("诗人作品数量分布")
                with button_col:
                    if st.button("🔄 刷新图表", key=f"refresh_poets_{selected_db_key}", help="仅重新加载诗人数据"):
                        get_poem_count_by_author_data.clear()
                
                top_n_authors = st.slider("显示 Top N 创作者", 5, 50, 20, key=f"author_count_{selected_db_key}")
                display_author_poem_count(selected_db_key, top_n=top_n_authors)
                
                st.subheader("诗词长度分布")
                method_display = st.radio("选择统计方法", ('按字数', '按词数'), key=f'len_method_{selected_db_key}', horizontal=True)
                method = {'按字数': 'characters', '按词数': 'words'}[method_display]
                df = get_poem_length_distribution_data(selected_db_key, method)
                if not df.empty:
                    fig = px.bar(df, x='length_band', y='count', title=f'诗词长度分布 ({method_display})')
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.header(f"情感类型分析: {selected_db_key}")
                emotion_dist_df = get_emotion_distribution_data(selected_db_key)

                if emotion_dist_df.empty:
                    st.warning("未找到情感分布数据。请确保已运行数据迁移脚本，或该库中有已完成的标注。")
                else:
                    header_col, button_col = st.columns([0.85, 0.15])
                    with header_col:
                        st.subheader("情感类型层级分布")
                    with button_col:
                        if st.button("🔄 刷新分布", key=f"refresh_emotion_dist_{selected_db_key}", help="仅重新加载情感分布数据"):
                            get_emotion_distribution_data.clear()
                    display_emotion_sunburst(selected_db_key)

                    st.subheader("情感频次统计")
                    # ... (rest of emotion frequency code) ...
                    emotion_freq_df = emotion_dist_df.sort_values('count', ascending=False)
                    top_n = st.slider("显示 Top N 情感类别", 10, min(100, len(emotion_freq_df)), 20, key=f"emotion_freq_slider_{selected_db_key}")
                    df_to_plot = emotion_freq_df.head(top_n)
                    fig_height = max(400, len(df_to_plot) * 30 + 100)
                    fig_bar_all = px.bar(df_to_plot, x='count', y='name_zh', orientation='h', title=f'情感类别频次排行 (Top {top_n})', labels={'name_zh': '情感类别', 'count': '出现次数'}, text='percentage', height=fig_height).update_yaxes(categoryorder="total ascending")
                    st.plotly_chart(fig_bar_all, use_container_width=True)


                    st.subheader("情感共现与关联规则挖掘")
                    tab_sql_sentence, tab_sql_poem, tab_apriori = st.tabs(["**单句内共现 (SQL 计数)**", "**全诗内共现 (SQL 计数)**", "**高级挖掘 (Apriori)**"])

                    with tab_sql_sentence:
                        st.markdown("⚡️ **快速概览**: 使用 SQL 直接统计**一句诗中**共同出现的多种情感。")
                        top_n_sentence = st.slider("选择显示组合数量", 5, 50, 15, key=f"combo_sentence_{selected_db_key}")
                        display_frequent_combinations(selected_db_key, top_n_sentence)

                    with tab_sql_poem:
                        st.markdown("⚡️ **快速概览**: 使用 SQL 直接统计**一首诗内**（不一定在同一句）共同出现的不同情感。")
                        top_n_poem = st.slider("选择显示组合数量", 5, 50, 15, key=f"combo_poem_{selected_db_key}")
                        sets_df = get_frequent_poem_emotion_sets_data(selected_db_key, top_n_poem)
                        if not sets_df.empty:
                            st.dataframe(sets_df, column_config={"set_readable": st.column_config.TextColumn("情感集合", width="large"), "set_count": st.column_config.NumberColumn("出现次数", format="%d 首"), "poem_example": st.column_config.TextColumn("示例诗词")}, use_container_width=True, hide_index=True)
                        else:
                            st.info("暂无全诗内高频情感集合数据。")

                    with tab_apriori:
                        st.markdown("🔬 **深度挖掘**: 使用 Apriori 算法发现频繁项集，探索不同稀有度的情感组合。")
                        st.info("此功能计算密集。为提升体验，挖掘将在您点击按钮后启动。")
                        
                        session_key = f"apriori_started_{selected_db_key}"
                        if session_key not in st.session_state:
                            st.session_state[session_key] = False
                        
                        if st.button("🚀 开始 Apriori 挖掘", key=f"start_apriori_{selected_db_key}"):
                            st.session_state[session_key] = True
                        if st.session_state.get(session_key):
                            if st.button("隐藏结果", key=f"reset_apriori_{selected_db_key}"):
                                st.session_state[session_key] = False
                                st.rerun()
                            st.markdown("---")
                            col1, col2 = st.columns(2)
                            with col1:
                                level_map = {"句子级别": "sentence", "诗词级别": "poem"}
                                selected_level_display = st.radio("分析粒度", level_map.keys(), key=f"apriori_level_{selected_db_key}", horizontal=True)
                                level = level_map[selected_level_display]
                            with col2:
                                min_length = st.slider("组合中最少情感数", 2, 5, 2, key=f"apriori_len_{selected_db_key}")
                            
                            min_support_percent = st.slider("最小支持度 (%)", 0.1, 10.0, 1.0, step=0.1, key=f"apriori_support_{selected_db_key}", help="一个情感组合出现的频率。值越低，发现的组合越稀有、越多。")
                            min_support = min_support_percent / 100.0
                            
                            # 新增性能控制选项
                            st.markdown("### ⚙️ 性能控制选项")
                            col3, col4 = st.columns(2)
                            with col3:
                                # 根据最小支持度自动设置合理的事务上限
                                recommended_max_transactions = max(1000, int(10000 * (1 - min_support)))  # 支持度越低，处理的数据应该越少
                                max_transactions = st.slider(
                                    "最大事务数 (控制计算规模)",
                                    100,
                                    50000,
                                    min(recommended_max_transactions, 10000),
                                    key=f"apriori_max_transactions_{selected_db_key}",
                                    help="减少此值可加快计算速度但可能丢失罕见模式"
                                )
                            
                            with col4:
                                # 动态提示用户当前设置可能导致的性能影响
                                estimated_time = "几秒到几分钟"
                                if min_support < 0.5:
                                    estimated_time = "几分钟到数十分钟"
                                if max_transactions > 10000:
                                    estimated_time += " (可能会更长)"
                                st.info(f"预计计算时间: {estimated_time}")
                            # 显示正在执行的状态
                            with st.spinner("正在进行 Apriori 挖掘，请稍候..."):
                                apriori_results_df = get_apriori_results_data(selected_db_key, level, min_support, min_length, max_transactions)
                            
                            st.markdown("---")
                            st.subheader(f"挖掘结果 (支持度 > {min_support_percent:.1f}%)")
                            if not apriori_results_df.empty:
                                # 检查数据框长度，避免滑块错误
                                result_count = len(apriori_results_df)
                                if result_count > 1:
                                    top_n_apriori = st.slider("显示前 N 条结果", 1, result_count, min(25, result_count), key=f"apriori_rows_{selected_db_key}")
                                    display_df = apriori_results_df.head(top_n_apriori)
                                else:
                                    st.info(f"发现 {result_count} 个结果")
                                    display_df = apriori_results_df
                                
                                st.dataframe(
                                    display_df, 
                                    column_config={
                                        "itemsets_readable": st.column_config.TextColumn("高频情感组合", width="large"), 
                                        "support": st.column_config.NumberColumn("支持度", format="%.4f"), 
                                        "length": st.column_config.NumberColumn("组合长度")
                                    }, 
                                    use_container_width=True, 
                                    hide_index=True
                                )
                            else:
                                st.warning(f"在当前设置下未发现任何情感组合。请尝试降低最小支持度或最小长度。")
    else:
        # --- Comparison View Mode (Code remains largely the same, but lazy loading can be applied to Apriori here too) ---
        db_keys_to_compare = db_keys_options[:2] # Default to first two
        
        with tab1:
            # ... (Existing comparison code) ...
            st.header("标注结果分析 (对比)")
            st.subheader("模型性能总览")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(db_keys_to_compare[0])
                display_model_performance(db_keys_to_compare[0])
            with col2:
                st.subheader(db_keys_to_compare[1])
                display_model_performance(db_keys_to_compare[1])
            st.subheader("标注趋势 (叠加对比)")
            display_annotation_trend_comparison_chart(db_keys_to_compare, start_date_iso, end_date_iso)


        with tab2:
            # ... (Existing comparison code) ...
            st.header("诗词数据概览 (对比)")
            st.subheader("创作者作品数量 (并排对比)")
            col1, col2 = st.columns(2)
            with col1:
                display_author_poem_count(db_keys_to_compare[0])
            with col2:
                display_author_poem_count(db_keys_to_compare[1])
            st.subheader("诗词长度分布 (叠加对比)")
            method_display = st.radio("选择统计方法", ('按字数', '按词数'), key='len_method_compare', horizontal=True)
            method = {'按字数': 'characters', '按词数': 'words'}[method_display]
            display_poem_length_comparison_chart(db_keys_to_compare, method, method_display)


        with tab3:
            st.header("情感分析 (对比)")
            st.subheader("情感层级分布 (并排对比)")
            col1, col2 = st.columns(2)
            # ... (Existing comparison sunburst code) ...
            with col1:
                st.subheader(db_keys_to_compare[0])
                display_emotion_sunburst(db_keys_to_compare[0])
            with col2:
                st.subheader(db_keys_to_compare[1])
                display_emotion_sunburst(db_keys_to_compare[1])
            st.markdown("---")
            # ... (Existing comparison diff table code) ...
            st.subheader(f"聚合对比：情感分类引用百分比差异 ({db_keys_to_compare[1]} vs {db_keys_to_compare[0]})")
            sunburst_df1 = get_emotion_distribution_data(db_keys_to_compare[0])
            sunburst_df2 = get_emotion_distribution_data(db_keys_to_compare[1])
            if not sunburst_df1.empty and not sunburst_df2.empty:
                df1_comp = sunburst_df1[['name_zh', 'percentage', 'count']].rename(columns={'percentage': f'percentage_{db_keys_to_compare[0]}','count': f'count_{db_keys_to_compare[0]}'})
                df2_comp = sunburst_df2[['name_zh', 'percentage', 'count']].rename(columns={'percentage': f'percentage_{db_keys_to_compare[1]}','count': f'count_{db_keys_to_compare[1]}'})
                merged_comp_df = pd.merge(df1_comp, df2_comp, on='name_zh', how='outer').fillna(0)
                merged_comp_df['percentage_diff'] = merged_comp_df[f'percentage_{db_keys_to_compare[1]}'] - merged_comp_df[f'percentage_{db_keys_to_compare[0]}']
                merged_comp_df = merged_comp_df.sort_values(by='percentage_diff', ascending=False, key=abs)
                st.dataframe(merged_comp_df, column_config={'name_zh': "情感分类", f'percentage_{db_keys_to_compare[0]}': st.column_config.NumberColumn(f"{db_keys_to_compare[0]} 占比 (%)", format="%.2f"), f'percentage_{db_keys_to_compare[1]}': st.column_config.NumberColumn(f"{db_keys_to_compare[1]} 占比 (%)", format="%.2f"), 'percentage_diff': st.column_config.NumberColumn(f"增减百分点 ({db_keys_to_compare[1]}-{db_keys_to_compare[0]})", format="%+.2f"), f'count_{db_keys_to_compare[0]}': st.column_config.NumberColumn(f"{db_keys_to_compare[0]} 引用数"), f'count_{db_keys_to_compare[1]}': st.column_config.NumberColumn(f"{db_keys_to_compare[1]} 引用数")}, column_order=['name_zh', f'percentage_{db_keys_to_compare[0]}', f'percentage_{db_keys_to_compare[1]}', 'percentage_diff', f'count_{db_keys_to_compare[0]}', f'count_{db_keys_to_compare[1]}'], use_container_width=True, hide_index=True)
            else:
                st.info("一个或两个数据库缺少情感分布数据，无法进行聚合对比。")

            st.markdown("---")
            
            st.subheader(f"聚合对比：高频情感组合支持度差异 ({db_keys_to_compare[1]} vs {db_keys_to_compare[0]})")
            st.info("使用 Apriori 算法在 **诗词级别** 进行对比挖掘。为减少计算开销，挖掘将在点击按钮后启动。")
            
            session_key_comp = "apriori_started_compare"
            if session_key_comp not in st.session_state:
                st.session_state[session_key_comp] = False

            if st.button("🚀 开始对比挖掘", key="start_apriori_compare"):
                st.session_state[session_key_comp] = True

            if st.session_state.get(session_key_comp):
                if st.button("隐藏对比结果", key="reset_apriori_compare"):
                    st.session_state[session_key_comp] = False
                    st.rerun()

                col_a, col_b = st.columns(2)
                with col_a:
                    min_length_compare = st.slider("组合中最少情感数", 2, 5, 2, key="apriori_len_compare")
                with col_b:
                    min_support_percent_compare = st.slider("最小支持度 (%)", 0.1, 5.0, 0.5, step=0.1, key="apriori_support_compare")
                
                min_support_compare = min_support_percent_compare / 100.0
                level_compare = 'poem'

                apriori_df1 = get_apriori_results_data(db_keys_to_compare[0], level_compare, min_support_compare, min_length_compare)
                apriori_df2 = get_apriori_results_data(db_keys_to_compare[1], level_compare, min_support_compare, min_length_compare)

                if apriori_df1.empty and apriori_df2.empty:
                    st.warning(f"在当前设置下，两个数据库均未发现任何情感组合。请尝试降低参数。")
                else:
                    df1_ap_comp = apriori_df1[['itemsets_readable', 'support']].rename(columns={'support': f'support_{db_keys_to_compare[0]}'}),
                    df2_ap_comp = apriori_df2[['itemsets_readable', 'support']].rename(columns={'support': f'support_{db_keys_to_compare[1]}'}),
                    merged_ap_df = pd.merge(df1_ap_comp, df2_ap_comp, on='itemsets_readable', how='outer').fillna(0)
                    merged_ap_df['support_diff'] = merged_ap_df[f'support_{db_keys_to_compare[1]}'] - merged_ap_df[f'support_{db_keys_to_compare[0]}']
                    merged_ap_df = merged_ap_df[(merged_ap_df[f'support_{db_keys_to_compare[0]}'] > 0) | (merged_ap_df[f'support_{db_keys_to_compare[1]}'] > 0)]
                    merged_ap_df = merged_ap_df.sort_values(by='support_diff', ascending=False, key=abs)
                    
                    top_n_apriori_comp = st.slider("显示前 N 条对比结果", 5, len(merged_ap_df), min(25, len(merged_ap_df)), key="apriori_rows_compare")
                    st.dataframe(merged_ap_df.head(top_n_apriori_comp), column_config={'itemsets_readable': "高频情感组合", f'support_{db_keys_to_compare[0]}': st.column_config.NumberColumn(f"{db_keys_to_compare[0]} 支持度", format="%.4f"), f'support_{db_keys_to_compare[1]}': st.column_config.NumberColumn(f"{db_keys_to_compare[1]} 支持度", format="%.4f"), 'support_diff': st.column_config.NumberColumn(f"支持度差异 ({db_keys_to_compare[1]}-{db_keys_to_compare[0]})", format="%+.4f")}, column_order=['itemsets_readable', f'support_{db_keys_to_compare[0]}', f'support_{db_keys_to_compare[1]}', 'support_diff'], use_container_width=True, hide_index=True)

    with tab4:
        st.header("关于与性能")
        st.markdown("""
        ### 应用优化说明
        此版本根据轻量级性能优化方案进行了升级，主要改进包括：

        - **🎯 局部刷新**: 多数图表已配备独立的刷新按钮 (🔄)，只会更新对应图表的数据，而非整个页面，响应更快捷。
        - **⚡️ 懒加载**: 计算密集的 Apriori 挖掘功能现已默认关闭，需点击“开始挖掘”按钮后才会执行。这显著降低了页面的初始加载时间。
        - **📊 表格控件**: 对于可能产生大量数据的图表（如 Apriori 结果、作者排行），增加了滑块（Slider）来控制显示条目数，避免了渲染大数据表格时的性能瓶颈。
        - **🧠 状态管理**: 通过 `st.session_state` 智能管理UI状态，确保懒加载的内容在页面刷新后依然存在，提升了交互的连贯性。

        这些优化旨在不引入复杂依赖的前提下，为个人研究项目提供一个更流畅、更高效的数据可视化体验。
        """)
        st.subheader("缓存管理")
        st.info("点击左侧侧边栏的 **[清除所有缓存并刷新]** 按钮，可以强制清除所有层级的缓存和会话状态，进行完全重置。")
