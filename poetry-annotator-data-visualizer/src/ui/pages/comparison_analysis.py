"""
双库对比分析页面
负责双库对比模式的所有 UI 逻辑
"""

import streamlit as st
import pandas as pd
from typing import Optional, List

from src.services.model_service import ModelService
from src.services.poem_service import PoemService
from src.services.emotion_service import EmotionService
from src.ui.components.charts import render_sunburst, render_bar_chart, render_line_chart
from src.ui.components.tables import render_apriori_table
from src.ui.components.controls import render_top_n_slider, render_method_radio


class ComparisonAprioriState:
    """管理对比模式 Apriori 挖掘的会话状态"""
    
    def __init__(self):
        self.compare_min_length = 2
        self.compare_min_support_percent = 0.5
        self.compare_enable_max_transactions = True
        self.compare_max_transactions = 5000
        self.is_mining = False
        self.compare_results_df = None
        self.error_message = ""
    
    def set_parameters(self, min_length, min_support_percent, enable_max_transactions, max_transactions):
        self.compare_min_length = min_length
        self.compare_min_support_percent = min_support_percent
        self.compare_enable_max_transactions = enable_max_transactions
        self.compare_max_transactions = max_transactions if enable_max_transactions else None
        self.error_message = ""
    
    def get_compare_min_support(self):
        return self.compare_min_support_percent / 100.0
    
    def start_mining(self):
        self.is_mining = True
        self.compare_results_df = None
        self.error_message = ""
    
    def set_results(self, df):
        self.compare_results_df = df
        self.is_mining = False
    
    def set_error(self, message):
        self.error_message = message
        self.is_mining = False
    
    def reset(self):
        self.is_mining = False
        self.compare_results_df = None
        self.error_message = ""


class ComparisonAnalysisPage:
    """双库对比分析页面"""
    
    def __init__(
        self,
        db_keys: List[str],
        model_services: List[ModelService],
        poem_services: List[PoemService],
        emotion_services: List[EmotionService]
    ):
        self.db_keys = db_keys
        self.model_services = model_services
        self.poem_services = poem_services
        self.emotion_services = emotion_services
        
        # 初始化或获取对比模式的 Apriori 状态
        if 'apriori_state_compare' not in st.session_state:
            st.session_state.apriori_state_compare = ComparisonAprioriState()
        self.apriori_state = st.session_state.apriori_state_compare
    
    def render(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """渲染双库对比分析页面"""
        db1, db2 = self.db_keys
        
        # 标注分析标签页
        self._render_annotation_tab(db1, db2, start_date, end_date)
        
        # 诗词数据概览标签页
        self._render_poem_overview_tab(db1, db2)
        
        # 情感分析标签页
        self._render_emotion_tab(db1, db2)
    
    def _render_annotation_tab(self, db1: str, db2: str, start_date: Optional[str], end_date: Optional[str]):
        """渲染标注分析标签页"""
        st.header("标注结果分析 (对比)")
        st.subheader("模型性能总览")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(db1)
            model_perf_df1 = self.model_services[0].get_model_performance()
            from src.ui.components.tables import render_model_performance_table
            render_model_performance_table(model_perf_df1, key=f"model_table_{db1}")
        with col2:
            st.subheader(db2)
            model_perf_df2 = self.model_services[1].get_model_performance()
            render_model_performance_table(model_perf_df2, key=f"model_table_{db2}")
        
        # 标注趋势对比
        st.subheader("标注趋势 (叠加对比)")
        self._render_annotation_trend_comparison(start_date, end_date)
    
    def _render_annotation_trend_comparison(self, start_date: Optional[str], end_date: Optional[str]):
        """渲染标注趋势对比图表"""
        combined_df = pd.DataFrame()
        for i, db_key in enumerate(self.db_keys):
            df = self.model_services[i].get_annotation_trends(start_date, end_date)
            if not df.empty:
                df['source'] = db_key
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        if not combined_df.empty:
            trend_chart_df = combined_df.groupby(['annotation_date', 'source'])['completed'].sum().reset_index()
            render_line_chart(
                trend_chart_df,
                x='annotation_date',
                y='completed',
                title='每日成功标注数量趋势对比',
                x_label='日期',
                y_label='成功标注数量',
                color='source'
            )
        else:
            st.info("所选日期范围内无数据进行标注趋势对比。")
    
    def _render_poem_overview_tab(self, db1: str, db2: str):
        """渲染诗词数据概览标签页"""
        st.header("诗词数据概览 (对比)")
        
        # 创作者作品数量并排对比
        st.subheader("创作者作品数量 (并排对比)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(db1)
            author_df1 = self.poem_services[0].get_author_poem_counts()
            if not author_df1.empty:
                render_bar_chart(
                    author_df1.head(20),
                    x='author',
                    y='poem_count',
                    title=f'{db1} - 作品数量最多的创作者',
                    x_label='创作者',
                    y_label='作品数量'
                )
        with col2:
            st.subheader(db2)
            author_df2 = self.poem_services[1].get_author_poem_counts()
            if not author_df2.empty:
                render_bar_chart(
                    author_df2.head(20),
                    x='author',
                    y='poem_count',
                    title=f'{db2} - 作品数量最多的创作者',
                    x_label='创作者',
                    y_label='作品数量'
                )
        
        # 诗词长度分布叠加对比
        st.subheader("诗词长度分布 (叠加对比)")
        method = render_method_radio(
            'len_method_compare',
            "选择统计方法",
            {'按字数': 'characters', '按词数': 'words'}
        )
        self._render_poem_length_comparison(method)
    
    def _render_poem_length_comparison(self, method: str):
        """渲染诗词长度分布对比图表"""
        combined_df = pd.DataFrame()
        for i, db_key in enumerate(self.db_keys):
            df = self.poem_services[i].get_poem_length_distribution(method)
            if not df.empty:
                df['source'] = db_key
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        if not combined_df.empty:
            render_bar_chart(
                combined_df,
                x='length_band',
                y='count',
                title=f'诗词长度分布对比 ({method})',
                x_label='长度区间',
                y_label='数量',
                color='source',
                barmode='group'
            )
        else:
            st.info("暂无数据进行诗词长度对比。")
    
    def _render_emotion_tab(self, db1: str, db2: str):
        """渲染情感分析标签页"""
        st.header("情感分析 (对比)")
        
        # 情感层级分布并排对比
        st.subheader("情感层级分布 (并排对比)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(db1)
            emotion_df1 = self.emotion_services[0].get_emotion_distribution()
            render_sunburst(emotion_df1, key=f"sunburst_{db1}", title=f"{db1} - 情感层级分布")
        with col2:
            st.subheader(db2)
            emotion_df2 = self.emotion_services[1].get_emotion_distribution()
            render_sunburst(emotion_df2, key=f"sunburst_{db2}", title=f"{db2} - 情感层级分布")
        
        st.markdown("---")
        
        # 聚合对比：情感分类引用百分比差异
        st.subheader(f"聚合对比：情感分类引用百分比差异 ({db2} vs {db1})")
        self._render_emotion_percentage_comparison(db1, db2)
        
        st.markdown("---")
        
        # 聚合对比：高频情感组合支持度差异
        st.subheader(f"聚合对比：高频情感组合支持度差异 ({db2} vs {db1})")
        st.info("使用 Apriori 算法在 **诗词级别** 进行对比挖掘。参数调整后点击按钮才会启动挖掘。")
        self._render_apriori_comparison()
    
    def _render_emotion_percentage_comparison(self, db1: str, db2: str):
        """渲染情感百分比对比表格"""
        sunburst_df1 = self.emotion_services[0].get_emotion_distribution()
        sunburst_df2 = self.emotion_services[1].get_emotion_distribution()
        
        if not sunburst_df1.empty and not sunburst_df2.empty:
            df1_comp = sunburst_df1[['name_zh', 'percentage', 'count']].rename(
                columns={'percentage': f'percentage_{db1}', 'count': f'count_{db1}'}
            )
            df2_comp = sunburst_df2[['name_zh', 'percentage', 'count']].rename(
                columns={'percentage': f'percentage_{db2}', 'count': f'count_{db2}'}
            )
            merged_df = pd.merge(df1_comp, df2_comp, on='name_zh', how='outer').fillna(0)
            merged_df['percentage_diff'] = merged_df[f'percentage_{db2}'] - merged_df[f'percentage_{db1}']
            merged_df = merged_df.sort_values(by='percentage_diff', ascending=False, key=abs)
            
            st.dataframe(
                merged_df,
                column_config={
                    'name_zh': "情感分类",
                    f'percentage_{db1}': st.column_config.NumberColumn(f"{db1} 占比 (%)", format="%.2f"),
                    f'percentage_{db2}': st.column_config.NumberColumn(f"{db2} 占比 (%)", format="%.2f"),
                    'percentage_diff': st.column_config.NumberColumn(f"增减百分点 ({db2}-{db1})", format="%+.2f"),
                    f'count_{db1}': st.column_config.NumberColumn(f"{db1} 引用数"),
                    f'count_{db2}': st.column_config.NumberColumn(f"{db2} 引用数")
                },
                column_order=['name_zh', f'percentage_{db1}', f'percentage_{db2}', 'percentage_diff', f'count_{db1}', f'count_{db2}'],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("一个或两个数据库缺少情感分布数据，无法进行聚合对比。")
    
    def _render_apriori_comparison(self):
        """渲染 Apriori 对比挖掘"""
        # 参数设置
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            min_length = st.slider(
                "组合中最少情感数", 2, 5, 
                self.apriori_state.compare_min_length, 
                key="apriori_len_compare"
            )
        with col_b:
            min_support_percent = st.slider(
                "最小支持度 (%)", 0.1, 5.0, 
                self.apriori_state.compare_min_support_percent, 
                step=0.1, 
                key="apriori_support_compare"
            )
        with col_c:
            enable_max_transactions = st.checkbox(
                "限制最大事务数", 
                value=self.apriori_state.compare_enable_max_transactions, 
                key="enable_max_transactions_compare"
            )
            if enable_max_transactions:
                max_transactions = st.number_input(
                    "最大事务数", min_value=100, max_value=50000, 
                    value=self.apriori_state.compare_max_transactions, 
                    key="apriori_max_transactions_compare"
                )
            else:
                max_transactions = None
        
        # 参数更新按钮
        if st.button("🔄 更新对比参数", key="update_params_compare"):
            self.apriori_state.set_parameters(
                min_length, min_support_percent, enable_max_transactions, max_transactions
            )
            st.success("对比参数已更新！")
        
        # 挖掘控制按钮
        button_col1, button_col2, button_col3 = st.columns(3)
        with button_col1:
            if st.button("🚀 开始/重新对比挖掘", key="start_apriori_compare"):
                self.apriori_state.start_mining()
                st.rerun()
        with button_col2:
            if self.apriori_state.is_mining and st.button("⏹️ 停止对比挖掘", key="stop_apriori_compare"):
                self.apriori_state.reset()
                st.rerun()
        with button_col3:
            if not self.apriori_state.is_mining and (self.apriori_state.compare_results_df is not None or self.apriori_state.error_message):
                if st.button("🗑️ 清除对比结果", key="clear_apriori_compare"):
                    self.apriori_state.reset()
                    st.rerun()
        
        # 执行挖掘
        if self.apriori_state.is_mining:
            with st.spinner("正在为两个数据库执行 Apriori 对比挖掘..."):
                try:
                    apriori_df1 = self.emotion_services[0].mine_apriori(
                        level='poem',
                        min_support=self.apriori_state.get_compare_min_support(),
                        min_length=self.apriori_state.compare_min_length,
                        max_transactions=self.apriori_state.compare_max_transactions
                    )
                    apriori_df2 = self.emotion_services[1].mine_apriori(
                        level='poem',
                        min_support=self.apriori_state.get_compare_min_support(),
                        min_length=self.apriori_state.compare_min_length,
                        max_transactions=self.apriori_state.compare_max_transactions
                    )
                    
                    if apriori_df1.empty and apriori_df2.empty:
                        self.apriori_state.set_error("在当前设置下，两个数据库均未发现任何情感组合。请尝试降低参数。")
                    else:
                        df1_comp = apriori_df1[['itemsets_readable', 'support']].rename(
                            columns={'support': f'support_{self.db_keys[0]}'}
                        )
                        df2_comp = apriori_df2[['itemsets_readable', 'support']].rename(
                            columns={'support': f'support_{self.db_keys[1]}'}
                        )
                        merged_df = pd.merge(df1_comp, df2_comp, on='itemsets_readable', how='outer').fillna(0)
                        
                        if not merged_df.empty:
                            merged_df['support_diff'] = merged_df[f'support_{self.db_keys[1]}'] - merged_df[f'support_{self.db_keys[0]}']
                            merged_df = merged_df[(merged_df[f'support_{self.db_keys[0]}'] > 0) | (merged_df[f'support_{self.db_keys[1]}'] > 0)]
                            merged_df = merged_df.reindex(merged_df['support_diff'].abs().sort_values(ascending=False).index)
                            self.apriori_state.set_results(merged_df)
                        else:
                            self.apriori_state.set_error("合并后的对比结果为空。")
                except Exception as e:
                    self.apriori_state.set_error(f"对比挖掘过程中发生错误：{e}")
        
        # 显示结果
        if self.apriori_state.compare_results_df is not None and not self.apriori_state.compare_results_df.empty:
            db1, db2 = self.db_keys
            st.dataframe(
                self.apriori_state.compare_results_df,
                column_config={
                    'itemsets_readable': "高频情感组合",
                    f'support_{db1}': st.column_config.NumberColumn(f"{db1} 支持度", format="%.4f"),
                    f'support_{db2}': st.column_config.NumberColumn(f"{db2} 支持度", format="%.4f"),
                    'support_diff': st.column_config.NumberColumn(f"支持度差异 ({db2}-{db1})", format="%+.4f")
                },
                column_order=['itemsets_readable', f'support_{db1}', f'support_{db2}', 'support_diff'],
                use_container_width=True,
                hide_index=True
            )
        elif self.apriori_state.error_message:
            st.error(self.apriori_state.error_message)
        elif self.apriori_state.is_mining:
            st.info("对比挖掘已启动，请等待...")
        else:
            st.info("点击 '开始/重新对比挖掘' 按钮以启动挖掘。")
