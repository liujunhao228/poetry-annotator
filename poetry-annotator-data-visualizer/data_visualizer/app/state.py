import streamlit as st
import pandas as pd


class AprioriMinerState:
    """
    用于管理 Apriori Interactive Miner 的 UI 状态。
    """

    def __init__(self, db_key: str):
        self.db_key = db_key
        
        # --- 用户输入参数 ---
        self.level = "poem"
        self.min_length = 2
        self.min_support_percent = 1.0
        self.enable_max_transactions = True
        self.max_transactions = 5000

        # --- 对比模式参数 ---
        self.compare_min_length = 2
        self.compare_min_support_percent = 0.5
        self.compare_enable_max_transactions = True
        self.compare_max_transactions = 5000

        # --- UI 状态 ---
        self.is_mining_single = False
        self.is_mining_compare = False
        self.single_results_df = pd.DataFrame()
        self.compare_results_df = pd.DataFrame()
        self.error_message = ""

    # --- 单库挖掘状态管理方法 ---

    def set_single_parameters(self, level, min_length, min_support_percent, enable_max_transactions, max_transactions):
        """设置单库挖掘参数"""
        self.level = level
        self.min_length = min_length
        self.min_support_percent = min_support_percent
        self.enable_max_transactions = enable_max_transactions
        self.max_transactions = max_transactions if enable_max_transactions else None
        self.error_message = "" # 清除之前的错误

    def start_single_mining(self):
        """标记单库挖掘开始"""
        self.is_mining_single = True
        self.single_results_df = pd.DataFrame() # 清除旧结果
        self.error_message = ""

    def set_single_results(self, results_df: pd.DataFrame):
        """设置单库挖掘结果"""
        self.single_results_df = results_df
        self.is_mining_single = False

    def set_single_error(self, message: str):
        """设置单库挖掘错误"""
        self.error_message = message
        self.is_mining_single = False

    def reset_single(self):
        """重置单库挖掘状态"""
        self.is_mining_single = False
        self.single_results_df = pd.DataFrame()
        self.error_message = ""

    # --- 对比挖掘状态管理方法 ---

    def set_compare_parameters(self, min_length, min_support_percent, enable_max_transactions, max_transactions):
        """设置对比挖掘参数"""
        self.compare_min_length = min_length
        self.compare_min_support_percent = min_support_percent
        self.compare_enable_max_transactions = enable_max_transactions
        self.compare_max_transactions = max_transactions if enable_max_transactions else None
        self.error_message = "" # 清除之前的错误

    def start_compare_mining(self):
        """标记对比挖掘开始"""
        self.is_mining_compare = True
        self.compare_results_df = pd.DataFrame() # 清除旧结果
        self.error_message = ""

    def set_compare_results(self, results_df: pd.DataFrame):
        """设置对比挖掘结果"""
        self.compare_results_df = results_df
        self.is_mining_compare = False

    def set_compare_error(self, message: str):
        """设置对比挖掘错误"""
        self.error_message = message
        self.is_mining_compare = False

    def reset_compare(self):
        """重置对比挖掘状态"""
        self.is_mining_compare = False
        self.compare_results_df = pd.DataFrame()
        self.error_message = ""

    # --- 通用方法 ---

    def reset_all(self):
        """重置所有状态"""
        self.__init__(self.db_key)

    def get_min_support(self):
        """获取单库挖掘的实际最小支持度值 (0-1)"""
        return self.min_support_percent / 100.0

    def get_compare_min_support(self):
        """获取对比挖掘的实际最小支持度值 (0-1)"""
        return self.compare_min_support_percent / 100.0
