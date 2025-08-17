#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import json
from pathlib import Path
import threading
import os

# 导入基类和可复用的通用组件
from .base_tab import TaskExecutorTab
from .common_widgets import (
    PathSelector, 
    create_option_frame,
    configure_grid_row_column
)


class RecoveryTab(TaskExecutorTab):
    """
    从日志恢复数据的UI选项卡。
    
    此选项卡允许用户配置并启动 `recover_from_log_v7.py` 脚本，
    用于从日志文件中恢复因意外中断而未保存的标注数据。
    """
    
    def get_tab_name(self):
        """返回选项卡名称，用于保存偏好设置"""
        return "RecoveryTab"
    
    def __init__(self, master):
        # 设置按钮文本属性
        self.start_button_text = "开始恢复"
        self.stop_button_text = "停止恢复"
        
        # 调用父类构造函数，传入对应的脚本名称
        super().__init__(master, "recover_from_log_v7.py")
        
        # 设置UI界面并更新状态
        self._setup_ui()
        self._update_ui_state()
        
        # 启动父类中用于处理子进程输出的队列轮询
        self.master.after(100, self.process_queue)
    
    def _setup_ui(self):
        """
        统一创建并布局所有UI组件。
        这是UI初始化和布局的核心方法。
        """
        # --- 核心布局策略 ---
        # 使用 PanedWindow 分割设置区域和日志/控制区域
        # ---------------------
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(fill="both", expand=True)

        # 创建一个主容器来容纳所有"设置"相关的UI组件
        settings_container = ttk.Frame(paned_window)
        paned_window.add(settings_container, weight=0)

        # 配置settings_container的列权重，使其可以水平扩展
        settings_container.columnconfigure(0, weight=1)

        # 依次创建并布局各个设置区域
        self._create_log_path_selector(settings_container, row=0)
        self._create_db_path_selector(settings_container, row=1)
        self._create_other_options(settings_container, row=2)

        # 创建一个用于容纳通用控件的容器
        common_widgets_container = ttk.Frame(paned_window)
        paned_window.add(common_widgets_container, weight=1)

        # 调用父类方法，并将新创建的容器传递进去
        self._create_common_widgets(common_widgets_container)

    def _create_log_path_selector(self, parent, row):
        """创建日志路径选择器。"""
        log_path_frame = create_option_frame(parent, "日志来源选择")
        log_path_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        # 配置网格，使第二列(路径选择器)可以随窗口宽度变化
        configure_grid_row_column(log_path_frame, col_weights=[0, 1])

        self.log_source_var = tk.StringVar(value="file")
        
        # --- 日志文件选择 (使用grid布局) ---
        self.log_file_radio = ttk.Radiobutton(
            log_path_frame, text="指定单个日志文件", 
            variable=self.log_source_var, value="file", 
            command=self._update_ui_state
        )
        self.log_file_radio.grid(row=0, column=0, sticky="w", padx=5)

        self.log_file_selector = PathSelector(
            log_path_frame, label_text="", 
            file_types=[("日志文件", "*.log"), ("所有文件", "*.*")], 
            mode="file"
        )
        self.log_file_selector.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # --- 日志目录选择 (使用grid布局) ---
        self.log_dir_radio = ttk.Radiobutton(
            log_path_frame, text="指定日志文件目录", 
            variable=self.log_source_var, value="dir", 
            command=self._update_ui_state
        )
        self.log_dir_radio.grid(row=1, column=0, sticky="w", padx=5)

        self.log_dir_selector = PathSelector(
            log_path_frame, label_text="", 
            file_types=[("日志文件", "*.log"), ("所有文件", "*.*")], 
            mode="dir"
        )
        self.log_dir_selector.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

    def _create_db_path_selector(self, parent, row):
        """创建数据库路径选择器。"""
        db_path_frame = create_option_frame(parent, "数据库路径 (可选)")
        db_path_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        self.db_path_selector = PathSelector(
            db_path_frame, label_text="", 
            file_types=[("数据库文件", "*.db"), ("所有文件", "*.*")], 
            mode="file"
        )
        self.db_path_selector.pack(fill="x", expand=True, padx=5, pady=2)

    def _create_other_options(self, parent, row):
        """创建其他选项。"""
        other_options_frame = create_option_frame(parent, "其他选项")
        other_options_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        self.dry_run_var = tk.BooleanVar(value=True)  # 默认勾选，更安全
        self.dry_run_check = ttk.Checkbutton(
            other_options_frame, text="试运行 (Dry Run) - 仅分析日志，不写入数据库", 
            variable=self.dry_run_var
        )
        self.dry_run_check.pack(fill="x", padx=10, pady=5)

    def _update_ui_state(self, is_running=False):
        """根据任务是否正在运行，动态更新所有UI控件的状态（启用/禁用）。"""
        state = "disabled" if is_running else "normal"
        
        # 1. 更新日志来源相关控件状态
        is_file_source = self.log_source_var.get() == "file"
        self.log_file_radio['state'] = state
        self.log_file_selector.set_state(state if is_file_source else "disabled")
        self.log_dir_radio['state'] = state
        self.log_dir_selector.set_state(state if not is_file_source else "disabled")

        # 2. 更新数据库路径选择器状态
        self.db_path_selector.set_state(state)

        # 3. 更新其他选项状态
        self.dry_run_check['state'] = state

        # 4. 更新父类提供的基础控件（开始/停止按钮，状态栏）
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"

    def start_task(self):
        """
        收集所有UI配置，构建命令行参数，并启动后台任务线程。
        """
        # --- 1. 构建命令列表 ---
        command = [sys.executable, str(self.script_path)]
        
        # 日志来源
        if self.log_source_var.get() == "file":
            log_file = self.log_file_selector.get_path()
            if not log_file: 
                self.log_message("错误: 请指定一个日志文件路径。\n"); return
            command.extend(["--file", log_file])
        else:
            log_dir = self.log_dir_selector.get_path()
            if not log_dir: 
                self.log_message("错误: 请指定一个日志文件目录。\n"); return
            command.extend(["--dir", log_dir])
            
        # 数据库路径（如果提供了）
        db_path = self.db_path_selector.get_path()
        if db_path:
            command.extend(["--db-path", db_path])
        
        # Dry run 选项 - 注意脚本默认是 dry run，需要 --write 才会实际写入
        if not self.dry_run_var.get():  # 如果用户取消了 dry run 选项
            command.append("--write")   # 则添加 --write 标志
            
        # --- 2. 准备UI并执行任务 ---
        # 清空日志区域
        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        
        # 显示将要执行的命令
        display_command = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command)
        self.log_message(f"执行命令: {display_command}\n" + "="*80 + "\n")
        
        # 更新UI为"运行中"状态
        self._update_ui_state(is_running=True)
        
        # 创建并启动后台线程来运行子进程
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()
