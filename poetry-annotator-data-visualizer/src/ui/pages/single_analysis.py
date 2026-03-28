"""
单库分析页面
负责单库分析模式的所有 UI 逻辑
"""

import streamlit as st
from datetime import datetime
from typing import Optional

from src.services.model_service import ModelService
from src.services.poem_service import PoemService
from src.services.emotion_service import EmotionService
from src.ui.components.charts import render_sunburst, render_bar_chart, render_line_chart
from src.ui.components.tables import (
    render_model_performance_table,
    render_apriori_table,
    render_emotion_combinations_table,
    render_poem_emotion_sets_table,
)
from src.ui.components.controls import (
    render_top_n_slider,
    render_method_radio,
    render_refresh_button,
)


class AprioriState:
    """管理 Apriori 挖掘的会话状态"""
    
    def __init__(self):
        self.level = "poem"
        self.min_length = 2
        self.min_support_percent = 1.0
        self.enable_max_transactions = True
        self.max_transactions = 5000
        self.is_mining = False
        self.results_df = None
        self.error_message = ""
    
    def set_parameters(self, level, min_length, min_support_percent, enable_max_transactions, max_transactions):
        self.level = level
        self.min_length = min_length
        self.min_support_percent = min_support_percent
        self.enable_max_transactions = enable_max_transactions
        self.max_transactions = max_transactions if enable_max_transactions else None
        self.error_message = ""
    
    def get_min_support(self):
        return self.min_support_percent / 100.0
    
    def start_mining(self):
        self.is_mining = True
        self.results_df = None
        self.error_message = ""
    
    def set_results(self, df):
        self.results_df = df
        self.is_mining = False
    
    def set_error(self, message):
        self.error_message = message
        self.is_mining = False
    
    def reset(self):
        self.is_mining = False
        self.results_df = None
        self.error_message = ""


class SingleAnalysisPage:
    """单库分析页面"""
    
    def __init__(
        self, 
        db_key: str,
        model_service: ModelService,
        poem_service: PoemService,
        emotion_service: EmotionService
    ):
        self.db_key = db_key
        self.model_service = model_service
        self.poem_service = poem_service
        self.emotion_service = emotion_service
        
        # 初始化或获取 Apriori 状态
        if 'apriori_state' not in st.session_state:
            st.session_state.apriori_state = AprioriState()
        self.apriori_state = st.session_state.apriori_state
    
    def render(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """渲染单库分析页面"""
        st.header(f"标注结果分析：{self.db_key}")
        
        # 标注分析标签页
        self._render_annotation_tab(start_date, end_date)
        
        # 诗词数据概览标签页
        self._render_poem_overview_tab()
        
        # 情感分析标签页
        self._render_emotion_tab()
    
    def _render_annotation_tab(self, start_date: Optional[str], end_date: Optional[str]):
        """渲染标注分析标签页"""
        st.subheader("模型性能总览")
        model_perf_df = self.model_service.get_model_performance()
        render_model_performance_table(model_perf_df)
        
        # 标注趋势
        header_col, button_col = st.columns([0.85, 0.15])
        with header_col:
            st.subheader("标注趋势")
        with button_col:
            if render_refresh_button(f"refresh_trends_{self.db_key}", "🔄 刷新趋势", "仅重新加载趋势数据"):
                self.model_service.clear_cache()
                st.rerun()
        
        trends_df = self.model_service.get_annotation_trends(start_date, end_date)
        if not trends_df.empty:
            summary_df = trends_df.groupby('annotation_date')['completed'].sum().reset_index()
            render_line_chart(
                summary_df,
                x='annotation_date',
                y='completed',
                title="每日成功标注数量",
                x_label="日期",
                y_label="成功标注数"
            )
        else:
            st.info("所选日期范围内无标注趋势数据。")
    
    def _render_poem_overview_tab(self):
        """渲染诗词数据概览标签页"""
        # 诗人作品数量分布
        header_col, button_col = st.columns([0.85, 0.15])
        with header_col:
            st.subheader("诗人作品数量分布")
        with button_col:
            if render_refresh_button(f"refresh_poets_{self.db_key}", "🔄 刷新图表", "仅重新加载诗人数据"):
                self.poem_service.clear_cache()
                st.rerun()
        
        top_n = render_top_n_slider(f"author_count_{self.db_key}", "显示 Top N 创作者", default_value=20)
        author_df = self.poem_service.get_author_poem_counts()
        if not author_df.empty:
            render_bar_chart(
                author_df.head(top_n),
                x='author',
                y='poem_count',
                title=f'作品数量最多的创作者 (Top {top_n})',
                x_label='创作者',
                y_label='作品数量'
            )
        
        # 诗词长度分布
        st.subheader("诗词长度分布")
        method = render_method_radio(
            f'len_method_{self.db_key}',
            "选择统计方法",
            {'按字数': 'characters', '按词数': 'words'}
        )
        length_df = self.poem_service.get_poem_length_distribution(method)
        if not length_df.empty:
            render_bar_chart(
                length_df,
                x='length_band',
                y='count',
                title=f'诗词长度分布 ({method})',
                x_label='长度区间',
                y_label='数量'
            )
    
    def _render_emotion_tab(self):
        """渲染情感分析标签页"""
        emotion_dist_df = self.emotion_service.get_emotion_distribution()
        
        if emotion_dist_df.empty:
            st.warning("未找到情感分布数据。")
            return
        
        # 情感类型层级分布
        header_col, button_col = st.columns([0.85, 0.15])
        with header_col:
            st.subheader("情感类型层级分布")
        with button_col:
            if render_refresh_button(f"refresh_emotion_dist_{self.db_key}", "🔄 刷新分布", "仅重新加载情感分布数据"):
                self.emotion_service.clear_cache()
                st.rerun()
        
        render_sunburst(emotion_dist_df, key=f"sunburst_{self.db_key}")
        
        # 情感频次统计
        st.subheader("情感频次统计")
        emotion_freq_df = emotion_dist_df.sort_values('count', ascending=False)
        top_n = render_top_n_slider(f"emotion_freq_slider_{self.db_key}", "显示 Top N 情感类别", max_value=min(100, len(emotion_freq_df)))
        df_to_plot = emotion_freq_df.head(top_n)
        
        render_bar_chart(
            df_to_plot,
            x='count',
            y='name_zh',
            title=f'情感类别频次排行 (Top {top_n})',
            x_label='出现次数',
            y_label='情感类别',
            orientation='h'
        )
        
        # 情感共现与关联规则挖掘
        self._render_emotion_cooccurrence_section()
    
    def _render_emotion_cooccurrence_section(self):
        """渲染情感共现与关联规则挖掘部分"""
        st.subheader("情感共现与关联规则挖掘")
        tab_sql_sentence, tab_sql_poem_actual, tab_sql_poem_frequency, tab_apriori = st.tabs([
            "**单句内共现 (SQL 计数)**",
            "**全诗内共现 - 实际 (SQL 计数)**",
            "**全诗内共现 - 频率 (SQL 计数)**",
            "**高级挖掘 (Apriori)**"
        ])
        
        with tab_sql_sentence:
            st.markdown("⚡️ **快速概览**: 使用 SQL 直接统计**一句诗中**共同出现的多种情感。")
            top_n = render_top_n_slider(f"combo_sentence_{self.db_key}", "选择显示组合数量", default_value=15)
            combos_df = self.emotion_service.get_frequent_emotion_combinations(top_n)
            render_emotion_combinations_table(combos_df)
        
        with tab_sql_poem_actual:
            st.markdown("⚡️ **实际普遍性**: 使用 SQL 直接统计**一首诗内**（基于最新标注）共同出现的不同情感。")
            top_n = render_top_n_slider(f"combo_poem_actual_{self.db_key}", "选择显示组合数量", default_value=15)
            sets_df = self.emotion_service.get_frequent_poem_emotion_sets(top_n, use_actual=True)
            render_poem_emotion_sets_table(sets_df)
        
        with tab_sql_poem_frequency:
            st.markdown("⚡️ **标注频率**: 使用 SQL 直接统计**一首诗内**（基于所有标注）共同出现的不同情感。")
            top_n = render_top_n_slider(f"combo_poem_frequency_{self.db_key}", "选择显示组合数量", default_value=15)
            sets_df = self.emotion_service.get_frequent_poem_emotion_sets(top_n, use_actual=False)
            render_poem_emotion_sets_table(sets_df)
        
        with tab_apriori:
            self._render_apriori_tab()
    
    def _render_apriori_tab(self):
        """渲染 Apriori 高级挖掘标签页"""
        st.markdown("🔬 **深度挖掘**: 使用 Apriori 算法发现频繁项集，探索不同稀有度的情感组合。")
        st.info("此功能计算密集。为提升体验，参数调整后点击按钮才会启动挖掘。")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            level = render_method_radio(
                f"apriori_level_{self.db_key}",
                "分析粒度",
                {"句子级别": "sentence", "诗词级别": "poem"},
                horizontal=False
            )
        with col2:
            min_length = st.slider("组合中最少情感数", 2, 5, self.apriori_state.min_length, key=f"apriori_len_{self.db_key}")
        
        min_support_percent = st.slider(
            "最小支持度 (%)", 0.1, 10.0, self.apriori_state.min_support_percent, step=0.1,
            key=f"apriori_support_{self.db_key}",
            help="一个情感组合出现的频率。值越低，发现的组合越稀有、越多。"
        )
        
        # 性能控制选项
        st.markdown("### ⚙️ 性能控制选项")
        enable_max_transactions = st.checkbox(
            "限制最大事务数",
            value=self.apriori_state.enable_max_transactions,
            key=f"enable_max_transactions_{self.db_key}",
            help="取消勾选以处理所有事务（可能需要较长时间）"
        )
        
        if enable_max_transactions:
            max_transactions = st.slider(
                "最大事务数 (控制计算规模)",
                100, 50000, self.apriori_state.max_transactions,
                key=f"apriori_max_transactions_{self.db_key}"
            )
        else:
            max_transactions = None
            st.info("当前设置将处理所有事务，可能需要较长时间。")
        
        # 参数更新按钮
        if st.button("🔄 更新参数", key=f"update_params_{self.db_key}"):
            self.apriori_state.set_parameters(
                level, min_length, min_support_percent, enable_max_transactions, max_transactions
            )
            st.success("参数已更新！")
        
        # 挖掘控制按钮
        button_col1, button_col2, button_col3 = st.columns(3)
        with button_col1:
            if st.button("🚀 开始/重新 Apriori 挖掘", key=f"start_apriori_{self.db_key}"):
                self.apriori_state.start_mining()
                st.rerun()
        with button_col2:
            if self.apriori_state.is_mining and st.button("⏹️ 停止挖掘", key=f"stop_apriori_{self.db_key}"):
                self.apriori_state.reset()
                st.rerun()
        with button_col3:
            if not self.apriori_state.is_mining and (self.apriori_state.results_df is not None or self.apriori_state.error_message):
                if st.button("🗑️ 清除结果", key=f"clear_apriori_{self.db_key}"):
                    self.apriori_state.reset()
                    st.rerun()
        
        # 执行挖掘并显示结果
        if self.apriori_state.is_mining:
            with st.spinner("正在进行 Apriori 挖掘，请稍候..."):
                try:
                    results_df = self.emotion_service.mine_apriori(
                        level=self.apriori_state.level,
                        min_support=self.apriori_state.get_min_support(),
                        min_length=self.apriori_state.min_length,
                        max_transactions=self.apriori_state.max_transactions
                    )
                    self.apriori_state.set_results(results_df)
                except Exception as e:
                    self.apriori_state.set_error(f"挖掘过程中发生错误：{e}")
        
        # 显示结果
        if self.apriori_state.results_df is not None and not self.apriori_state.results_df.empty:
            st.markdown("---")
            st.subheader(f"挖掘结果 (支持度 > {self.apriori_state.min_support_percent:.1f}%)")
            result_count = len(self.apriori_state.results_df)
            if result_count > 1:
                top_n = st.slider("显示前 N 条结果", 1, result_count, min(25, result_count), key=f"apriori_rows_{self.db_key}")
                display_df = self.apriori_state.results_df.head(top_n)
            else:
                st.info(f"发现 {result_count} 个结果")
                display_df = self.apriori_state.results_df
            render_apriori_table(display_df)
        elif self.apriori_state.error_message:
            st.error(self.apriori_state.error_message)
        elif self.apriori_state.is_mining:
            st.info("挖掘已启动，请等待...")
        else:
            st.info("点击 '开始/重新 Apriori 挖掘' 按钮以启动挖掘。")
