"""任务分发功能选项卡"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Any, Optional

from .base_tab import BaseTab
from ..components import DatabaseSelector, ModelSelector
from ..models.config import DistributionConfig


class DistributionTab(BaseTab):
    """任务分发功能选项卡"""
    
    def __init__(self, master: Any, config_service: Any):
        self.config_service = config_service
        self.config_file = Path('config') / 'gui_distribution.json'
        
        # 配置对象
        self.config = DistributionConfig.load(self.config_file)
        
        super().__init__(
            master=master,
            title="任务分发",
            script_name="distribute_tasks.py",
            config_service=config_service
        )
        
        # 启动日志队列处理
        if self.log_panel:
            self.log_panel.start_processing()
    
    def _create_options_panel(self) -> None:
        """创建选项配置面板"""
        # 1. 日志级别控制
        self._create_log_level_frame()
        
        # 2. 数据库选择
        self._create_database_selector()
        
        # 3. 模型选择
        self._create_model_selector()
        
        # 4. ID 来源选择
        self._create_id_source_frame()
        
        # 5. 其他选项
        self._create_other_options_frame()
        
        # 加载配置到 UI
        self._load_config_to_ui()
    
    def _create_log_level_frame(self) -> None:
        """创建日志级别控制框"""
        frame = ttk.LabelFrame(self, text="日志级别控制")
        frame.pack(fill="x", padx=5, pady=5)
        self.options_frame = frame  # 保存引用用于状态更新
        
        # 控制台日志级别
        ttk.Label(frame, text="控制台日志级别:").pack(side="left", padx=(10, 5), pady=5)
        self.console_log_level_var = tk.StringVar(value="INFO")
        self.console_log_level_combo = ttk.Combobox(
            frame, 
            textvariable=self.console_log_level_var, 
            values=["DEBUG", "INFO", "WARNING", "ERROR"], 
            width=10
        )
        self.console_log_level_combo.pack(side="left", padx=5, pady=5)
        
        # 文件日志级别
        ttk.Label(frame, text="文件日志级别:").pack(side="left", padx=(20, 5), pady=5)
        self.file_log_level_var = tk.StringVar(value="DEBUG")
        self.file_log_level_combo = ttk.Combobox(
            frame, 
            textvariable=self.file_log_level_var, 
            values=["DEBUG", "INFO", "WARNING", "ERROR"], 
            width=10
        )
        self.file_log_level_combo.pack(side="left", padx=5, pady=5)
    
    def _create_database_selector(self) -> None:
        """创建数据库选择器"""
        self.db_selector = DatabaseSelector(
            self,
            config_manager=self.config_service.config_manager,
            label_text="数据库选择"
        )
        self.db_selector.pack(fill="x", padx=5, pady=5)
    
    def _create_model_selector(self) -> None:
        """创建模型选择器"""
        self.model_selector = ModelSelector(
            self,
            config_manager=self.config_service.config_manager,
            label_text="模型选择",
            show_all_option=True
        )
        self.model_selector.pack(fill="x", padx=5, pady=5)
    
    def _create_id_source_frame(self) -> None:
        """创建 ID 来源选择框"""
        frame = ttk.LabelFrame(self, text="ID 来源选择")
        frame.pack(fill="x", padx=5, pady=5)
        
        self.id_source_var = tk.StringVar(value="file")
        
        # 文件模式
        self.id_file_radio = ttk.Radiobutton(
            frame, 
            text="指定单个 ID 文件", 
            variable=self.id_source_var, 
            value="file",
            command=self._update_id_source_state
        )
        self.id_file_radio.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.id_file_path_var = tk.StringVar()
        self.id_file_entry = ttk.Entry(frame, textvariable=self.id_file_path_var)
        self.id_file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.id_file_browse_btn = ttk.Button(
            frame, 
            text="浏览...", 
            command=self._browse_id_file
        )
        self.id_file_browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 目录模式
        self.id_dir_radio = ttk.Radiobutton(
            frame, 
            text="指定 ID 文件目录", 
            variable=self.id_source_var, 
            value="dir",
            command=self._update_id_source_state
        )
        self.id_dir_radio.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.id_dir_path_var = tk.StringVar()
        self.id_dir_entry = ttk.Entry(frame, textvariable=self.id_dir_path_var)
        self.id_dir_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.id_dir_browse_btn = ttk.Button(
            frame, 
            text="浏览目录...", 
            command=self._browse_id_dir
        )
        self.id_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        frame.columnconfigure(1, weight=1)
        
        # 保存引用用于状态更新
        self.id_source_widgets = [
            self.id_file_radio, self.id_file_entry, self.id_file_browse_btn,
            self.id_dir_radio, self.id_dir_entry, self.id_dir_browse_btn
        ]
    
    def _create_other_options_frame(self) -> None:
        """创建其他选项框"""
        frame = ttk.LabelFrame(self, text="其他选项")
        frame.pack(fill="x", padx=5, pady=5)
        
        # 强制重跑
        self.force_rerun_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, 
            text="强制重跑", 
            variable=self.force_rerun_var
        ).pack(side="left", padx=10, pady=5)
        
        # 全新开始
        self.fresh_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, 
            text="全新开始", 
            variable=self.fresh_start_var
        ).pack(side="left", padx=10, pady=5)
        
        # 批次大小
        ttk.Label(frame, text="批次大小:").pack(side="left", padx=(20, 5), pady=5)
        self.chunk_size_var = tk.StringVar(value="1000")
        self.chunk_size_entry = ttk.Entry(frame, textvariable=self.chunk_size_var, width=10)
        self.chunk_size_entry.pack(side="left", padx=5, pady=5)
        
        # 启用文件日志
        self.enable_file_log_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, 
            text="启用文件日志", 
            variable=self.enable_file_log_var
        ).pack(side="left", padx=10, pady=5)
        
        # 保存引用用于状态更新
        self.other_options_widgets = [
            self.console_log_level_combo, self.file_log_level_combo,
            self.chunk_size_entry
        ]
    
    def _update_id_source_state(self) -> None:
        """更新 ID 来源控件状态"""
        is_file_mode = self.id_source_var.get() == "file"
        
        self.id_file_entry['state'] = 'normal' if is_file_mode else 'disabled'
        self.id_file_browse_btn['state'] = 'normal' if is_file_mode else 'disabled'
        self.id_dir_entry['state'] = 'normal' if not is_file_mode else 'disabled'
        self.id_dir_browse_btn['state'] = 'normal' if not is_file_mode else 'disabled'
    
    def _browse_id_file(self) -> None:
        """浏览 ID 文件"""
        path = filedialog.askopenfilename(
            title="选择 ID 文件", 
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.id_file_path_var.set(path)
    
    def _browse_id_dir(self) -> None:
        """浏览 ID 文件目录"""
        initial_dir = Path(self.id_dir_path_var.get()).parent if self.id_dir_path_var.get() else None
        path = filedialog.askdirectory(
            title="选择 ID 文件所在目录", 
            initialdir=initial_dir
        )
        if path:
            self.id_dir_path_var.set(Path(path).resolve())
    
    def _load_config_to_ui(self) -> None:
        """加载配置到 UI"""
        self.console_log_level_var.set(self.config.console_log_level)
        self.file_log_level_var.set(self.config.file_log_level)
        self.model_selector.model_choice_mode.set(self.config.model_choice)
        if self.config.selected_model:
            self.model_selector.selected_model.set(self.config.selected_model)
        self.id_source_var.set(self.config.id_source)
        if self.config.id_file_path:
            self.id_file_path_var.set(self.config.id_file_path)
        if self.config.id_dir_path:
            self.id_dir_path_var.set(self.config.id_dir_path)
        self.force_rerun_var.set(self.config.force_rerun)
        self.fresh_start_var.set(self.config.fresh_start)
        self.chunk_size_var.set(str(self.config.chunk_size))
        self.enable_file_log_var.set(self.config.enable_file_log)
        
        self._update_id_source_state()
    
    def _save_config_from_ui(self) -> None:
        """从 UI 保存配置"""
        self.config.console_log_level = self.console_log_level_var.get()
        self.config.file_log_level = self.file_log_level_var.get()
        self.config.model_choice = self.model_selector.model_choice_mode.get()
        self.config.selected_model = self.model_selector.selected_model.get()
        self.config.id_source = self.id_source_var.get()
        self.config.id_file_path = self.id_file_path_var.get()
        self.config.id_dir_path = self.id_dir_path_var.get()
        self.config.force_rerun = self.force_rerun_var.get()
        self.config.fresh_start = self.fresh_start_var.get()
        self.config.chunk_size = int(self.chunk_size_var.get()) if self.chunk_size_var.get().isdigit() else 1000
        self.config.enable_file_log = self.enable_file_log_var.get()
        
        self.config.save(self.config_file)
    
    def _update_options_state(self, enabled: bool) -> None:
        """更新选项控件状态"""
        state = 'normal' if enabled else 'disabled'
        
        # 日志级别
        self.console_log_level_combo['state'] = state
        self.file_log_level_combo['state'] = state
        
        # 数据库选择器
        self.db_selector.set_enabled(enabled)
        
        # 模型选择器
        self.model_selector.update_state(not enabled)
        
        # ID 来源
        self._update_id_source_state()
        if not enabled:
            self.id_file_entry['state'] = 'disabled'
            self.id_file_browse_btn['state'] = 'disabled'
            self.id_dir_entry['state'] = 'disabled'
            self.id_dir_browse_btn['state'] = 'disabled'
        
        # 其他选项
        for widget in self.other_options_widgets:
            widget['state'] = state
    
    def start_task(self) -> None:
        """开始任务"""
        # 验证输入
        db_name = self.db_selector.get_selected_name()
        if not self.config_service.validate_database(db_name):
            self._log("错误：请选择一个有效的数据库\n")
            return
        
        # 构建命令参数
        args = []
        
        # 日志级别
        args.extend(["--console-log-level", self.console_log_level_var.get()])
        args.extend(["--file-log-level", self.file_log_level_var.get()])
        
        # 文件日志
        if self.enable_file_log_var.get():
            args.append("--enable-file-log")
        
        # 数据库
        args.extend(["--db", db_name])
        
        # 模型
        if self.model_selector.is_all_models():
            args.append("--all-models")
        else:
            model_name = self.model_selector.get_selected_model()
            if not self.config_service.validate_model(model_name):
                self._log("错误：请选择一个有效的模型\n")
                return
            args.extend(["--model", model_name])
        
        # ID 来源
        if self.id_source_var.get() == "file":
            id_file = self.id_file_path_var.get()
            if not id_file:
                self._log("错误：请指定一个 ID 文件路径\n")
                return
            args.extend(["--id-file", id_file])
        else:
            id_dir = self.id_dir_path_var.get()
            if not id_dir:
                self._log("错误：请指定一个 ID 文件目录\n")
                return
            args.extend(["--id-dir", id_dir])
        
        # 其他选项
        if self.force_rerun_var.get():
            args.append("--force-rerun")
        if self.fresh_start_var.get():
            args.append("--fresh-start")
        
        chunk_size = self.chunk_size_var.get()
        if chunk_size.isdigit() and int(chunk_size) > 0:
            args.extend(["--chunk-size", chunk_size])
        else:
            self._log(f"警告：批次大小 '{chunk_size}' 无效，将使用脚本默认值\n")
        
        # 清空日志并启动任务
        self.clear_log()
        
        if self._execute_script(args):
            self._update_ui_state(is_running=True)
            self._save_config_from_ui()
    
    def on_closing(self) -> None:
        """窗口关闭前的处理"""
        self._save_config_from_ui()
