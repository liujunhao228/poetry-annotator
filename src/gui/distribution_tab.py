#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import json
from pathlib import Path
import threading

# 导入基类和可复用的通用组件
from .base_tab import TaskExecutorTab
from .common_widgets import (
    LogLevelSelector, 
    DatabaseSelector, 
    ModelSelector, 
    PathSelector, 
    create_option_frame,
    configure_grid_row_column
)


class DistributionTab(TaskExecutorTab):
    """
    任务分发功能的UI选项卡。
    
    此选项卡允许用户配置并启动 `distribute_tasks.py` 脚本，
    用于大规模、高并发的诗词标注任务。
    """
    
    def get_tab_name(self):
        """返回选项卡名称，用于保存偏好设置"""
        return "DistributionTab"
    
    def __init__(self, master):
        self.config_file = Path('config') / 'gui_state.json'
        
        # 调用父类构造函数，传入对应的脚本名称
        super().__init__(master, "distribute_tasks.py")
        
        # 设置UI界面、加载配置并更新状态
        self._setup_ui()
        self.load_config()
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
        self._create_log_level_selector(settings_container, row=0)
        self._create_database_selector(settings_container, row=1)
        self._create_model_selector(settings_container, row=2)
        self._create_id_source_selector(settings_container, row=3)
        self._create_other_options(settings_container, row=4)

        # 创建一个用于容纳通用控件的容器
        common_widgets_container = ttk.Frame(paned_window)
        paned_window.add(common_widgets_container, weight=1)

        # 调用父类方法，并将新创建的容器传递进去
        self._create_common_widgets(common_widgets_container)

    def _create_log_level_selector(self, parent, row):
        """创建日志级别选择器。"""
        log_level_frame = create_option_frame(parent, "日志级别控制")
        log_level_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        # 【修复】将 log_level_frame 作为父容器(master)传入
        self.log_level_selector = LogLevelSelector(log_level_frame)
        self.log_level_selector.pack(fill="x", expand=True, padx=5, pady=2)
        
    def _create_database_selector(self, parent, row):
        """创建数据库选择器。"""
        db_frame = create_option_frame(parent, "数据库选择")
        db_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        # 【修复】将 db_frame 作为父容器(master)传入
        self.db_selector = DatabaseSelector(db_frame)
        self.db_selector.pack(fill="x", expand=True, padx=5, pady=2)
        
    def _create_model_selector(self, parent, row):
        """创建模型选择器。"""
        model_frame = create_option_frame(parent, "模型选择")
        model_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        # 【修复】将 model_frame 作为父容器(master)传入
        self.model_selector = ModelSelector(model_frame)
        self.model_selector.pack(fill="x", expand=True, padx=5, pady=2)
        
    def _create_id_source_selector(self, parent, row):
        """创建ID来源选择器。"""
        id_source_frame = create_option_frame(parent, "ID来源选择")
        id_source_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        # 配置网格，使第二列(路径选择器)可以随窗口宽度变化
        configure_grid_row_column(id_source_frame, col_weights=[0, 1])

        self.id_source_var = tk.StringVar(value="file")
        
        # --- ID文件选择 ---
        self.id_file_radio = ttk.Radiobutton(
            id_source_frame, text="指定单个ID文件", 
            variable=self.id_source_var, value="file", 
            command=self._update_ui_state
        )
        self.id_file_radio.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.id_file_selector = PathSelector(id_source_frame, label_text="", mode="file")
        self.id_file_selector.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # --- ID目录选择 ---
        self.id_dir_radio = ttk.Radiobutton(
            id_source_frame, text="指定ID文件目录", 
            variable=self.id_source_var, value="dir", 
            command=self._update_ui_state
        )
        self.id_dir_radio.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.id_dir_selector = PathSelector(id_source_frame, label_text="", mode="dir")
        self.id_dir_selector.grid(row=1, column=1, sticky="ew", padx=5, pady=2)


    def _create_other_options(self, parent, row):
        """创建其他选项。"""
        other_options_frame = create_option_frame(parent, "其他选项")
        other_options_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        self.force_rerun_var = tk.BooleanVar(value=False)
        self.force_rerun_check = ttk.Checkbutton(other_options_frame, text="强制重跑", variable=self.force_rerun_var)
        self.force_rerun_check.pack(side="left", padx=10, pady=5)
        
        self.fresh_start_var = tk.BooleanVar(value=False)
        self.fresh_start_check = ttk.Checkbutton(other_options_frame, text="全新开始", variable=self.fresh_start_var)
        self.fresh_start_check.pack(side="left", padx=10, pady=5)
        
        ttk.Label(other_options_frame, text="批次大小:").pack(side="left", padx=(20, 5), pady=5)
        self.chunk_size_var = tk.StringVar(value="1000")
        self.chunk_size_entry = ttk.Entry(other_options_frame, textvariable=self.chunk_size_var, width=10)
        self.chunk_size_entry.pack(side="left", padx=5, pady=5)
        
        self.enable_file_log_var = tk.BooleanVar(value=True)
        self.enable_file_log_check = ttk.Checkbutton(other_options_frame, text="启用文件日志", variable=self.enable_file_log_var)
        self.enable_file_log_check.pack(side="left", padx=10, pady=5)

    def save_config(self):
        """保存当前GUI配置到文件，以便下次启动时恢复。"""
        config_data = {
            'console_log_level': self.log_level_selector.get_console_level(),
            'file_log_level': self.log_level_selector.get_file_level(),
            'model_choice': self.model_selector.get_mode(),
            'selected_model': self.model_selector.get_selected_model(),
            'id_source': self.id_source_var.get(),
            'id_file_path': self.id_file_selector.get_path(),
            'id_dir_path': self.id_dir_selector.get_path(),
            'force_rerun': self.force_rerun_var.get(),
            'fresh_start': self.fresh_start_var.get(),
            'chunk_size': self.chunk_size_var.get(),
            'enable_file_log': self.enable_file_log_var.get(),
            'selected_db': self.db_selector.get_selected_db(),
        }
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"错误: 保存GUI配置失败: {e}\n")
    
    def load_config(self):
        """从文件加载GUI配置。"""
        if not self.config_file.exists():
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.log_level_selector.console_log_level_var.set(config.get('console_log_level', "INFO"))
            self.log_level_selector.file_log_level_var.set(config.get('file_log_level', "DEBUG"))
            
            self.model_selector.model_choice_var.set(config.get('model_choice', 'single'))
            selected_model = config.get('selected_model')
            if selected_model and selected_model in self.model_selector.model_combobox['values']:
                self.model_selector.model_var.set(selected_model)
                
            self.id_source_var.set(config.get('id_source', 'file'))
            self.id_file_selector.path_var.set(config.get('id_file_path', ''))
            self.id_dir_selector.path_var.set(config.get('id_dir_path', ''))
            
            self.force_rerun_var.set(config.get('force_rerun', False))
            self.fresh_start_var.set(config.get('fresh_start', False))
            self.chunk_size_var.set(config.get('chunk_size', "1000"))
            self.enable_file_log_var.set(config.get('enable_file_log', True))
            
            selected_db = config.get('selected_db')
            if selected_db and selected_db in self.db_selector.db_combobox['values']:
                self.db_selector.db_var.set(selected_db)
                
        except (json.JSONDecodeError, KeyError) as e:
            self.log_message(f"警告: 加载GUI配置失败，文件可能已损坏。将使用默认值。\n错误: {e}\n")

    def _update_ui_state(self, is_running=False):
        """根据任务是否正在运行，动态更新所有UI控件的状态（启用/禁用）。"""
        state = "disabled" if is_running else "normal"
        
        # 1. 更新通用组件状态
        self.log_level_selector.set_state(state)
        self.db_selector.set_state(state)
        self.model_selector.set_state(state)

        # 2. 更新ID来源相关控件状态
        is_file_source = self.id_source_var.get() == "file"
        self.id_file_radio['state'] = state
        self.id_file_selector.set_state(state if is_file_source else "disabled")
        self.id_dir_radio['state'] = state
        self.id_dir_selector.set_state(state if not is_file_source else "disabled")

        # 3. 更新其他选项状态
        for widget in [self.force_rerun_check, self.fresh_start_check, self.chunk_size_entry, self.enable_file_log_check]:
            widget['state'] = state

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
        
        # 日志选项
        command.extend(["--console-log-level", self.log_level_selector.get_console_level()])
        command.extend(["--file-log-level", self.log_level_selector.get_file_level()])
        if self.enable_file_log_var.get(): 
            command.append("--enable-file-log")
        
        # 数据库选择
        db_name = self.db_selector.get_selected_db()
        if not db_name:
            self.log_message("错误: 请选择一个有效的数据库。\n")
            return
        command.extend(["--db", db_name])
        
        # 模型选择
        if self.model_selector.get_mode() == "single":
            model_name = self.model_selector.get_selected_model()
            if not model_name:
                self.log_message("错误: 请选择一个有效的模型。\n")
                return
            command.extend(["--model", model_name])
        else:
            command.append("--all-models")
            
        # ID来源
        if self.id_source_var.get() == "file":
            id_file = self.id_file_selector.get_path()
            if not id_file: 
                self.log_message("错误: 请指定一个ID文件路径。\n"); return
            command.extend(["--id-file", id_file])
        else:
            id_dir = self.id_dir_selector.get_path()
            if not id_dir: 
                self.log_message("错误: 请指定一个ID文件目录。\n"); return
            command.extend(["--id-dir", id_dir])
            
        # 其他选项
        if self.force_rerun_var.get(): command.append("--force-rerun")
        if self.fresh_start_var.get(): command.append("--fresh-start")
            
        chunk_size = self.chunk_size_var.get()
        if chunk_size.isdigit() and int(chunk_size) > 0:
            command.extend(["--chunk-size", chunk_size])
        else:
            self.log_message(f"警告: 批次大小 '{chunk_size}' 无效，将使用脚本默认值。\n")
            
        # --- 2. 准备UI并执行任务 ---
        # 清空日志区域
        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        
        # 显示将要执行的命令
        display_command = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command)
        self.log_message(f"执行命令: {display_command}\n" + "="*80 + "\n")
        
        # 更新UI为“运行中”状态
        self._update_ui_state(is_running=True)
        
        # 创建并启动后台线程来运行子进程
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()
