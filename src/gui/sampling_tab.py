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
from src.config import config_manager


class SamplingTab(TaskExecutorTab):
    """
    随机抽样功能的UI选项卡。
    
    此选项卡允许用户配置并启动 `random_sample.py` 脚本，
    用于从诗词数据库中随机抽取指定数量的诗词ID。
    """
    
    def get_tab_name(self):
        """返回选项卡名称，用于保存偏好设置"""
        return "SamplingTab"
    
    def __init__(self, master):
        self.config_file = Path('config') / 'sampling_gui_state.json'
        
        # 调用父类构造函数，传入对应的脚本名称
        super().__init__(master, "random_sample.py")
        
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
        self._create_basic_options(settings_container, row=2)
        self._create_sort_options(settings_container, row=3)
        self._create_output_options(settings_container, row=4)

        # 创建一个用于容纳通用控件的容器
        common_widgets_container = ttk.Frame(paned_window)
        paned_window.add(common_widgets_container, weight=1)

        # 调用父类方法，并将新创建的容器传递进去
        self._create_common_widgets(common_widgets_container)

    def _create_log_level_selector(self, parent, row):
        """创建日志级别选择器。"""
        log_level_frame = create_option_frame(parent, "日志级别控制")
        log_level_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        self.log_level_selector = LogLevelSelector(log_level_frame)
        self.log_level_selector.pack(fill="x", expand=True, padx=5, pady=2)
        
    def _create_database_selector(self, parent, row):
        """创建数据库选择器。"""
        db_frame = create_option_frame(parent, "数据库选择")
        db_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        self.db_selector = DatabaseSelector(db_frame)
        self.db_selector.pack(fill="x", expand=True, padx=5, pady=2)
        
    def _create_basic_options(self, parent, row):
        """创建基本选项。"""
        basic_options_frame = create_option_frame(parent, "基本设置")
        basic_options_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        # 抽样数量
        ttk.Label(basic_options_frame, text="抽样数量:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.count_var = tk.StringVar(value="100")
        self.count_entry = ttk.Entry(basic_options_frame, textvariable=self.count_var, width=15)
        self.count_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 只抽取active状态的诗词
        self.active_only_var = tk.BooleanVar(value=False)
        self.active_only_check = ttk.Checkbutton(basic_options_frame, text="只抽取active状态的诗词", variable=self.active_only_var)
        self.active_only_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # 排除已标注
        self.exclude_annotated_frame = ttk.LabelFrame(basic_options_frame, text="排除已标注")
        self.exclude_annotated_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.exclude_annotated_var = tk.BooleanVar(value=False)
        self.exclude_annotated_check = ttk.Checkbutton(
            self.exclude_annotated_frame, text="排除已标注的诗词", 
            variable=self.exclude_annotated_var, command=self._update_ui_state
        )
        self.exclude_annotated_check.pack(side="left", padx=5, pady=5)
        
        # 为模型选择创建一个简化版本 (只包含单个模型选择和"全部模型"选项)
        self.exclude_model_var = tk.StringVar()
        self.exclude_model_combobox = ttk.Combobox(
            self.exclude_annotated_frame, textvariable=self.exclude_model_var, 
            state="readonly", width=20
        )
        self.exclude_model_combobox.pack(side="left", padx=5, pady=5)
        self._populate_exclude_models()
        
        configure_grid_row_column(basic_options_frame, col_weights=[0, 1, 0])
        
    def _populate_exclude_models(self):
        """填充排除已标注的模型下拉框"""
        try:
            models = config_manager.list_model_configs()
            if models:
                # 在模型列表前添加"全部模型"选项
                all_models = ["全部模型"] + models
                self.exclude_model_combobox['values'] = all_models
                if not self.exclude_model_var.get():
                    self.exclude_model_combobox.set(all_models[0])  # 默认选择"全部模型"
            else:
                self.exclude_model_combobox.set("无可用模型")
        except Exception as e:
            self.exclude_model_combobox.set("加载失败")
            # 使用基类的 log_message 方法
            self.log_message(f"错误: 加载模型配置失败: {e}\n")

    def _create_sort_options(self, parent, row):
        """创建排序选项。"""
        self.sort_frame = create_option_frame(parent, "排序方式")
        self.sort_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        self.sort_choice_var = tk.StringVar(value="shuffle")
        ttk.Radiobutton(self.sort_frame, text="随机排序 (默认)", variable=self.sort_choice_var, value="shuffle").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="按ID升序", variable=self.sort_choice_var, value="sort").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="不排序", variable=self.sort_choice_var, value="no-shuffle").pack(side="left", padx=10)

    def _create_output_options(self, parent, row):
        """创建输出选项。"""
        output_frame = create_option_frame(parent, "输出设置")
        output_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        self.output_mode_var = tk.StringVar(value="dir")
        
        # 输出到目录
        self.dir_mode_radio = ttk.Radiobutton(
            output_frame, text="输出到目录", 
            variable=self.output_mode_var, value="dir", command=self._update_ui_state
        )
        self.dir_mode_radio.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        self.output_dir_selector = PathSelector(
            output_frame, "目录路径:", 
            [("所有文件", "*.*")], "dir"
        )
        self.output_dir_selector.grid(row=1, column=0, columnspan=3, sticky="ew", padx=25, pady=5)
        
        ttk.Label(output_frame, text="分段文件数:").grid(row=2, column=0, padx=(25, 5), pady=5, sticky="w")
        self.num_files_var = tk.StringVar(value="1")
        self.num_files_entry = ttk.Entry(output_frame, textvariable=self.num_files_var, width=15)
        self.num_files_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 输出到文件
        self.file_mode_radio = ttk.Radiobutton(
            output_frame, text="输出到单个文件", 
            variable=self.output_mode_var, value="file", command=self._update_ui_state
        )
        self.file_mode_radio.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10,5))
        
        self.output_file_selector = PathSelector(
            output_frame, "文件路径:", 
            [("文本文件", "*.txt"), ("所有文件", "*.*")], "file"
        )
        self.output_file_selector.grid(row=4, column=0, columnspan=3, sticky="ew", padx=25, pady=5)
        
        configure_grid_row_column(output_frame, col_weights=[0, 1, 0])

    def save_config(self):
        """保存当前GUI配置到文件，以便下次启动时恢复。"""
        config_data = {
            'console_log_level': self.log_level_selector.get_console_level(),
            'file_log_level': self.log_level_selector.get_file_level(),
            'selected_db': self.db_selector.get_selected_db(),
            'count': self.count_var.get(),
            'active_only': self.active_only_var.get(),
            'exclude_annotated': self.exclude_annotated_var.get(),
            'exclude_model': self.exclude_model_var.get(),
            'sort_choice': self.sort_choice_var.get(),
            'output_mode': self.output_mode_var.get(),
            'output_dir_path': self.output_dir_selector.get_path(),
            'num_files': self.num_files_var.get(),
            'output_file_path': self.output_file_selector.get_path(),
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
            
            selected_db = config.get('selected_db')
            if selected_db and selected_db in self.db_selector.db_combobox['values']:
                self.db_selector.db_var.set(selected_db)
                
            self.count_var.set(config.get('count', "100"))
            self.active_only_var.set(config.get('active_only', False))
            self.exclude_annotated_var.set(config.get('exclude_annotated', False))
            self.exclude_model_var.set(config.get('exclude_model', ""))
            
            self.sort_choice_var.set(config.get('sort_choice', "shuffle"))
            
            self.output_mode_var.set(config.get('output_mode', "dir"))
            self.output_dir_selector.path_var.set(config.get('output_dir_path', ""))
            self.num_files_var.set(config.get('num_files', "1"))
            self.output_file_selector.path_var.set(config.get('output_file_path', ""))
                
        except (json.JSONDecodeError, KeyError) as e:
            self.log_message(f"警告: 加载GUI配置失败，文件可能已损坏。将使用默认值。\n错误: {e}\n")

    def _update_ui_state(self, is_running=False):
        """根据任务是否正在运行，动态更新所有UI控件的状态（启用/禁用）。"""
        state = "disabled" if is_running else "normal"
        
        # 1. 更新通用组件状态
        if hasattr(self, 'log_level_selector'):
            self.log_level_selector.set_state(state)
        if hasattr(self, 'db_selector'):
            self.db_selector.set_state(state)

        # 2. 更新基本设置相关控件状态
        widgets_to_update = []
        if hasattr(self, 'count_entry'):
            widgets_to_update.append(self.count_entry)
        if hasattr(self, 'active_only_check'):
            widgets_to_update.append(self.active_only_check)
        if hasattr(self, 'exclude_annotated_check'):
            widgets_to_update.append(self.exclude_annotated_check)
            
        for widget in widgets_to_update: 
            widget['state'] = state
            
        # 更新排除已标注相关控件状态
        if hasattr(self, 'exclude_model_combobox'):
            model_state = state if self.exclude_annotated_var.get() else 'disabled'
            self.exclude_model_combobox['state'] = 'readonly' if model_state == 'normal' else 'disabled'
        
        # 3. 更新排序方式相关控件状态
        if hasattr(self, 'sort_frame'):
            for child in self.sort_frame.winfo_children():
                if isinstance(child, (ttk.Radiobutton, ttk.Button, ttk.Entry)): 
                    child.configure(state=state)
            
        # 4. 更新输出设置相关控件状态
        if hasattr(self, 'output_mode_var') and hasattr(self, 'output_dir_selector') and hasattr(self, 'num_files_entry') and hasattr(self, 'output_file_selector'):
            output_mode = self.output_mode_var.get()
            dir_state = state if output_mode == 'dir' else 'disabled'
            self.output_dir_selector.set_state(dir_state)
            self.num_files_entry['state'] = dir_state
            if hasattr(self, 'dir_mode_radio'):
                self.dir_mode_radio['state'] = state
    
            file_state = state if output_mode == 'file' else 'disabled'
            self.output_file_selector.set_state(file_state)
            if hasattr(self, 'file_mode_radio'):
                self.file_mode_radio['state'] = state
        
        # 5. 更新父类提供的基础控件（开始/停止按钮，状态栏）
        if hasattr(self, 'start_button'):
            self.start_button['state'] = 'disabled' if is_running else 'normal'
        if hasattr(self, 'stop_button'):
            self.stop_button['state'] = 'normal' if is_running else 'disabled'
        if hasattr(self, 'status_bar'):
            self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"

    def start_task(self):
        """
        收集所有UI配置，构建命令行参数，并启动后台任务线程。
        """
        # --- 1. 构建命令列表 ---
        command = [sys.executable, str(self.script_path)]
        
        # 数据库选择
        db_name = self.db_selector.get_selected_db()
        if not db_name:
            self.log_message("错误: 请选择一个有效的数据库。\n")
            return
        command.extend(["--db-name", db_name])
            
        # 基本设置
        count = self.count_var.get()
        if not (count.isdigit() and int(count) > 0): 
            self.log_message(f"错误: 抽样数量 '{count}' 必须为正整数。\n")
            return
        command.extend(["-n", count])
        
        # 添加active-only选项
        if self.active_only_var.get():
            command.append("--active-only")
        
        # 添加排除已标注的选项
        if self.exclude_annotated_var.get():
            command.append("--exclude-annotated")
            model_name = self.exclude_model_var.get()
            # 如果选择了"全部模型"，则不指定具体的模型标识符
            if model_name == "全部模型":
                pass  # 不添加 --model 参数
            elif not model_name or "无" in model_name or "失败" in model_name:
                self.log_message("错误: 请选择一个有效的模型。\n")
                return
            else:
                command.extend(["--model", model_name])
        
        # 排序方式
        sort_mode = self.sort_choice_var.get()
        if sort_mode == 'sort': 
            command.append("--sort")
        elif sort_mode == 'no-shuffle': 
            command.append("--no-shuffle")
        
        # 输出设置
        if self.output_mode_var.get() == 'file':
            output_file = self.output_file_selector.get_path()
            if not output_file: 
                self.log_message("错误: 请指定输出文件路径。\n")
                return
            command.extend(["--output-file", output_file])
        else:
            output_dir = self.output_dir_selector.get_path()
            if output_dir: 
                command.extend(["--output-dir", output_dir])
            num_files = self.num_files_var.get()
            if not (num_files.isdigit() and int(num_files) > 0): 
                self.log_message(f"错误: 分段文件数 '{num_files}' 必须为正整数。\n")
                return
            command.extend(["--num-files", num_files])
            
        # --- 2. 准备UI并执行任务 ---
        # 清空日志区域
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        # 显示将要执行的命令
        display_command = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command)
        self.log_message(f"执行命令: {display_command}" + "="*80 + "")
        
        # 更新UI为"运行中"状态
        self._update_ui_state(is_running=True)
        
        # 创建并启动后台线程来运行子进程
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()
