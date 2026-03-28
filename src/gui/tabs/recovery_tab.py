"""日志恢复功能选项卡"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
from typing import Any, Optional

from .base_tab import BaseTab
from ..models.config import RecoveryConfig


class RecoveryTab(BaseTab):
    """日志恢复功能选项卡"""
    
    def __init__(self, master: Any, config_service: Any):
        self.config_service = config_service
        self.config_file = Path('config') / 'gui_recovery.json'
        
        # 配置对象
        self.config = RecoveryConfig.load(self.config_file)
        
        super().__init__(
            master=master,
            title="日志恢复",
            script_name="recover_from_log_v7.py",
            config_service=config_service
        )
        
        # 修改按钮文本
        if self.start_button:
            self.start_button.config(text="开始恢复")
        if self.stop_button:
            self.stop_button.config(text="停止恢复")
        
        # 启动日志队列处理
        if self.log_panel:
            self.log_panel.start_processing()
    
    def _create_options_panel(self) -> None:
        """创建选项配置面板"""
        # 恢复选项
        self._create_recovery_options_frame()
        
        # 加载配置到 UI
        self._load_config_to_ui()
    
    def _create_recovery_options_frame(self) -> None:
        """创建恢复选项框"""
        frame = ttk.LabelFrame(self, text="恢复选项")
        frame.pack(fill="x", padx=5, pady=5)
        self.options_frame = frame
        
        # 日志路径输入
        ttk.Label(frame, text="日志文件或目录路径:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.log_path_var = tk.StringVar()
        self.log_path_entry = ttk.Entry(frame, textvariable=self.log_path_var, width=60)
        self.log_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 浏览按钮容器
        browse_buttons_frame = ttk.Frame(frame)
        browse_buttons_frame.grid(row=0, column=2, padx=5, pady=5)
        
        self.browse_file_btn = ttk.Button(
            browse_buttons_frame, 
            text="浏览文件...", 
            command=self._browse_file
        )
        self.browse_file_btn.pack(side="left", padx=(0, 2))
        
        self.browse_dir_btn = ttk.Button(
            browse_buttons_frame, 
            text="浏览目录...", 
            command=self._browse_dir
        )
        self.browse_dir_btn.pack(side="left")
        
        frame.columnconfigure(1, weight=1)
        
        # Dry Run 选项
        self.dry_run_var = tk.BooleanVar(value=True)
        self.dry_run_check = ttk.Checkbutton(
            frame, 
            text="试运行 (Dry Run) - 仅分析日志，不写入数据库", 
            variable=self.dry_run_var
        )
        self.dry_run_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # 数据库路径输入
        ttk.Label(frame, text="数据库路径 (可选):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(frame, textvariable=self.db_path_var, width=60)
        self.db_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.browse_db_btn = ttk.Button(
            frame, 
            text="浏览数据库...", 
            command=self._browse_db
        )
        self.browse_db_btn.grid(row=2, column=2, padx=5, pady=5)
        
        self.recovery_widgets = [
            self.log_path_entry, self.browse_file_btn, self.browse_dir_btn,
            self.dry_run_check, self.db_path_entry, self.browse_db_btn
        ]
    
    def _browse_file(self) -> None:
        """浏览日志文件"""
        path = filedialog.askopenfilename(
            title="选择日志文件", 
            filetypes=[("日志文件", "*.log"), ("所有文件", "*.*")]
        )
        if path:
            self.log_path_var.set(path)
    
    def _browse_dir(self) -> None:
        """浏览日志目录"""
        path = filedialog.askdirectory(title="选择日志目录")
        if path:
            self.log_path_var.set(os.path.normpath(path))
    
    def _browse_db(self) -> None:
        """浏览数据库文件"""
        path = filedialog.askopenfilename(
            title="选择数据库文件", 
            filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")]
        )
        if path:
            self.db_path_var.set(path)
    
    def _load_config_to_ui(self) -> None:
        """加载配置到 UI"""
        self.log_path_var.set(self.config.log_path)
        self.db_path_var.set(self.config.db_path)
        self.dry_run_var.set(self.config.dry_run)
    
    def _save_config_from_ui(self) -> None:
        """从 UI 保存配置"""
        self.config.log_path = self.log_path_var.get()
        self.config.log_path_type = "file" if os.path.isfile(self.config.log_path) else "dir"
        self.config.db_path = self.db_path_var.get()
        self.config.dry_run = self.dry_run_var.get()
        
        self.config.save(self.config_file)
    
    def _update_options_state(self, enabled: bool) -> None:
        """更新选项控件状态"""
        state = 'normal' if enabled else 'disabled'
        
        for widget in self.recovery_widgets:
            widget['state'] = state
    
    def start_task(self) -> None:
        """开始任务"""
        log_path = self.log_path_var.get()
        if not log_path:
            self._log("错误：请指定日志文件或目录路径\n")
            return
        
        # 判断是文件还是目录
        if os.path.isfile(log_path):
            args = ["--file", log_path]
        elif os.path.isdir(log_path):
            args = ["--dir", log_path]
        else:
            self._log("错误：指定的路径既不是文件也不是目录\n")
            return
        
        # 添加数据库路径参数（如果提供了）
        db_path = self.db_path_var.get()
        if db_path:
            args.extend(["--db-path", db_path])
        
        # Dry run 选项
        if not self.dry_run_var.get():
            args.append("--write")
        
        # 清空日志并启动任务
        self.clear_log()
        
        if self._execute_script(args):
            self._update_ui_state(is_running=True)
            self._save_config_from_ui()
    
    def on_closing(self) -> None:
        """窗口关闭前的处理"""
        self._save_config_from_ui()
