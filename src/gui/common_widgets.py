#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定义可复用的 Tkinter GUI 组件。
适配全新的配置管理与数据管理体系。
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from src.config import config_manager


class LogLevelSelector(ttk.Frame):
    """
    一个用于选择控制台和文件日志级别的组合框框架。
    """
    def __init__(self, master, console_label="控制台日志级别:", file_label="文件日志级别:",
                 initial_console_level="INFO", initial_file_level="DEBUG"):
        super().__init__(master)
        
        self.console_log_level_var = tk.StringVar(value=initial_console_level)
        self.file_log_level_var = tk.StringVar(value=initial_file_level)
        
        # 控制台日志级别
        ttk.Label(self, text=console_label).pack(side="left", padx=(10, 5), pady=5)
        self.console_log_level_combo = ttk.Combobox(
            self, textvariable=self.console_log_level_var, 
            values=["DEBUG", "INFO", "WARNING", "ERROR"], 
            width=10, state="readonly"
        )
        self.console_log_level_combo.pack(side="left", padx=5, pady=5)
        
        # 文件日志级别
        ttk.Label(self, text=file_label).pack(side="left", padx=(20, 5), pady=5)
        self.file_log_level_combo = ttk.Combobox(
            self, textvariable=self.file_log_level_var, 
            values=["DEBUG", "INFO", "WARNING", "ERROR"], 
            width=10, state="readonly"
        )
        self.file_log_level_combo.pack(side="left", padx=5, pady=5)

    def get_console_level(self):
        """获取当前选择的控制台日志级别"""
        return self.console_log_level_var.get()
        
    def get_file_level(self):
        """获取当前选择的文件日志级别"""
        return self.file_log_level_var.get()

    def set_state(self, state):
        """设置组件状态"""
        self.console_log_level_combo['state'] = state
        self.file_log_level_combo['state'] = state


class DatabaseSelector(ttk.Frame):
    """
    一个用于选择数据库的组合框框架。
    适配新的多数据库配置管理体系。
    """
    def __init__(self, master, label_text="数据库:", initial_selection=None):
        super().__init__(master)
        
        self.db_var = tk.StringVar()
        if initial_selection:
            self.db_var.set(initial_selection)
            
        ttk.Label(self, text=label_text).pack(side="left", padx=(10, 5), pady=5)
        self.db_combobox = ttk.Combobox(self, textvariable=self.db_var, state="readonly", width=30)
        self.db_combobox.pack(side="left", padx=5, pady=5)
        self._populate_databases()
        
        # 绑定数据库选择变化事件 (如果需要)
        # self.db_var.trace_add("write", self._on_db_change)

    def _populate_databases(self):
        """填充数据库下拉框"""
        try:
            # 使用新的配置管理器API获取数据库配置
            db_config = config_manager.get_effective_database_config()
            if 'db_paths' in db_config:
                db_names = list(db_config['db_paths'].keys())
                if db_names:
                    self.db_combobox['values'] = db_names
                    if not self.db_var.get():
                        self.db_combobox.set(db_names[0])
                else:
                    self.db_combobox.set("无可用数据库")
            elif 'db_path' in db_config:
                # 单数据库模式，使用默认名称
                self.db_combobox['values'] = ["default"]
                self.db_combobox.set("default")
            else:
                self.db_combobox.set("无数据库配置")
        except Exception as e:
            self.db_combobox.set("加载失败")
            # 需要一个回调或日志记录机制来处理错误
            print(f"警告: 加载数据库配置失败: {e}")

    def get_selected_db(self):
        """获取当前选择的数据库名称"""
        db_name = self.db_var.get()
        if not db_name or "无" in db_name or "失败" in db_name:
            return None
        return db_name

    def get_selected_db_path(self):
        """
        获取当前选择的数据库的完整路径。
        返回 None 如果没有有效选择或配置错误。
        """
        db_name = self.get_selected_db()
        if not db_name:
            return None
        try:
            # 使用新的配置管理器API获取数据库配置
            db_config = config_manager.get_effective_database_config()
            if 'db_paths' in db_config and db_name in db_config['db_paths']:
                return db_config['db_paths'][db_name]
            elif 'db_path' in db_config and db_name == "default":
                return db_config['db_path']
            else:
                return None
        except Exception as e:
            print(f"警告: 获取数据库 '{db_name}' 路径失败: {e}")
            return None
            
    def set_state(self, state):
        """设置组件状态"""
        self.db_combobox['state'] = state


class ModelSelector(ttk.Frame):
    """
    一个用于选择模型的组合框框架。
    支持单个模型选择或使用所有模型的选项。
    适配新的模型配置管理体系。
    """
    def __init__(self, master, label_text="模型:", 
                 single_model_text="指定单个模型", all_models_text="使用所有已配置的模型",
                 initial_mode="single", initial_selection=None):
        super().__init__(master)
        
        self.model_choice_var = tk.StringVar(value=initial_mode) # "single" or "all"
        self.model_var = tk.StringVar()
        if initial_selection:
            self.model_var.set(initial_selection)
            
        # 单个模型选择
        self.single_model_radio = ttk.Radiobutton(
            self, text=single_model_text, 
            variable=self.model_choice_var, value="single"
        )
        self.single_model_radio.pack(side="left", padx=5, pady=5)
        
        self.model_combobox = ttk.Combobox(
            self, textvariable=self.model_var, state="readonly", width=30
        )
        self.model_combobox.pack(side="left", padx=5, pady=5)
        self._populate_models()
        
        # 所有模型选项
        self.all_models_radio = ttk.Radiobutton(
            self, text=all_models_text, 
            variable=self.model_choice_var, value="all"
        )
        self.all_models_radio.pack(side="left", padx=20, pady=5)

    def _populate_models(self):
        """填充模型下拉框"""
        try:
            # 使用新的配置管理器API获取模型配置列表
            model_configs = config_manager.get_effective_model_configs()
            # 提取模型名称
            models = []
            for i, config in enumerate(model_configs):
                # 优先使用 model_identifier 作为显示名称，如果没有则使用 name，再没有则使用索引
                model_name = config.get('model_identifier') or config.get('name') or f"模型{i}"
                models.append(model_name)
            
            if models:
                self.model_combobox['values'] = models
                if not self.model_var.get():
                    self.model_combobox.set(models[0])
            else:
                self.model_combobox.set("无可用模型")
        except Exception as e:
            self.model_combobox.set("加载失败")
            # 需要一个回调或日志记录机制来处理错误
            print(f"警告: 加载模型配置失败: {e}")

    def get_mode(self):
        """获取当前选择的模式 ('single' 或 'all')"""
        return self.model_choice_var.get()
        
    def get_selected_model(self):
        """
        获取当前选择的模型名称。
        如果模式是 'all'，则返回 None。
        """
        if self.get_mode() == "all":
            return None
        model_name = self.model_var.get()
        if not model_name or "无" in model_name or "失败" in model_name:
            return None
        return model_name
        
    def set_state(self, state):
        """设置组件状态"""
        self.single_model_radio['state'] = state
        self.all_models_radio['state'] = state
        combobox_state = 'readonly' if state == 'normal' and self.get_mode() == 'single' else 'disabled'
        self.model_combobox['state'] = combobox_state


class PathSelector(ttk.Frame):
    """
    一个用于选择文件或目录路径的通用框架。
    支持浏览文件、目录或同时支持两者。
    """
    def __init__(self, master, label_text="路径:", 
                 file_types=[("所有文件", "*.*")],
                 mode="file", # "file", "dir", "both"
                 initial_path=""):
        super().__init__(master)
        
        self.mode = mode
        self.file_types = file_types
        self.path_var = tk.StringVar(value=initial_path)
        
        ttk.Label(self, text=label_text).pack(side="left", padx=(10, 5), pady=5)
        self.path_entry = ttk.Entry(self, textvariable=self.path_var, width=50)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        button_frame = ttk.Frame(self)
        button_frame.pack(side="left", padx=5, pady=5)
        
        if self.mode in ["file", "both"]:
            self.browse_file_btn = ttk.Button(button_frame, text="浏览文件...", command=self._browse_file)
            self.browse_file_btn.pack(side="left", padx=(0, 2))
        if self.mode in ["dir", "both"]:
            self.browse_dir_btn = ttk.Button(button_frame, text="浏览目录...", command=self._browse_dir)
            self.browse_dir_btn.pack(side="left")

    def _browse_file(self):
        """打开文件选择对话框"""
        path = filedialog.askopenfilename(title="选择文件", filetypes=self.file_types)
        if path:
            self.path_var.set(path)
            
    def _browse_dir(self):
        """打开目录选择对话框"""
        path = filedialog.askdirectory(title="选择目录")
        if path:
            self.path_var.set(Path(path).resolve())

    def get_path(self):
        """获取当前输入的路径"""
        return self.path_var.get().strip()

    def set_state(self, state):
        """设置组件状态"""
        self.path_entry['state'] = state
        if hasattr(self, 'browse_file_btn'):
            self.browse_file_btn['state'] = state
        if hasattr(self, 'browse_dir_btn'):
            self.browse_dir_btn['state'] = state


# --- 辅助函数 ---

def create_option_frame(parent, text, padding=(5, 5)):
    """
    创建一个带标题的选项框架 (LabelFrame)。
    
    Args:
        parent: 父容器。
        text (str): 框架标题。
        padding (tuple): 内边距 (horizontal, vertical)。
        
    Returns:
        ttk.LabelFrame: 新创建的框架。
    """
    frame = ttk.LabelFrame(parent, text=text, padding=padding)
    # 不再自动 pack，让调用者决定如何布局
    return frame

def configure_grid_row_column(frame, row_weights=None, col_weights=None):
    """
    配置框架的网格行和列权重，以便子组件可以随窗口大小调整。
    
    Args:
        frame: 要配置的框架。
        row_weights (list): 每一行的权重列表。例如 [1, 0] 表示第一行可扩展，第二行固定。
        col_weights (list): 每一列的权重列表。
    """
    if row_weights:
        for i, weight in enumerate(row_weights):
            frame.rowconfigure(i, weight=weight)
    if col_weights:
        for i, weight in enumerate(col_weights):
            frame.columnconfigure(i, weight=weight)