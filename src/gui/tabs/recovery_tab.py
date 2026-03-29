"""日志恢复功能选项卡"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
from typing import Any, Optional

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from .base_tab import BaseTab
from ..models.config import RecoveryConfig
from ..models.config_manager import UnifiedConfigManager
from ..styles import get_colors, get_fonts


class RecoveryTab(BaseTab):
    """日志恢复功能选项卡"""

    def __init__(self, master: Any, config_service: Any, config_manager: Optional[UnifiedConfigManager] = None):
        self.config_service = config_service
        self._config_manager = config_manager
        self.config_file = Path('config') / 'gui_recovery.json'

        # 配置对象 - 优先从统一配置管理器获取
        if config_manager:
            self.config = config_manager.recovery
        else:
            self.config = RecoveryConfig.load(self.config_file)

        super().__init__(
            master=master,
            title="日志恢复",
            script_name="recover_from_log_v7.py",
            config_service=config_service
        )

        # 修改按钮文本
        if self.start_button:
            self.start_button.config(text="▶ 开始恢复")
        if self.stop_button:
            self.stop_button.config(text="⏹ 停止恢复")

        # 启动日志队列处理
        if self.log_panel:
            self.log_panel.start_processing()

    def _create_options_panel(self) -> None:
        """创建选项配置面板"""
        # 使用卡片式布局
        self.options_frame = ttkb.Frame(self)
        self.options_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.options_frame.grid_columnconfigure(0, weight=1)

        # 恢复选项
        self._create_recovery_options_frame()

        # 加载配置到 UI
        self._load_config_to_ui()

    def _create_recovery_options_frame(self) -> None:
        """创建恢复选项框"""
        frame = ttk.LabelFrame(self.options_frame, text="📋 恢复选项")
        frame.grid(row=0, column=0, sticky="ew", pady=5)
        frame.grid_columnconfigure(1, weight=1)
        
        # 内部容器添加间距
        inner = ttkb.Frame(frame)
        inner.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        inner.grid_columnconfigure(1, weight=1)
        
        frame = inner
        self.options_frame = frame

        # 日志路径输入
        path_frame = ttkb.Frame(frame)
        path_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        path_frame.grid_columnconfigure(1, weight=1)

        ttkb.Label(path_frame, text="日志文件或目录路径:", width=15).pack(side="left")

        self.log_path_var = tk.StringVar()
        self.log_path_entry = ttkb.Entry(path_frame, textvariable=self.log_path_var, width=50)
        self.log_path_entry.pack(side="left", padx=5, fill="x", expand=True)

        # 浏览按钮容器
        browse_buttons_frame = ttkb.Frame(path_frame)
        browse_buttons_frame.pack(side="left", padx=5)

        self.browse_file_btn = ttkb.Button(
            browse_buttons_frame,
            text="浏览文件...",
            command=self._browse_file,
            bootstyle=OUTLINE,
            width=8
        )
        self.browse_file_btn.pack(side="left", padx=(0, 2))

        self.browse_dir_btn = ttkb.Button(
            browse_buttons_frame,
            text="浏览目录...",
            command=self._browse_dir,
            bootstyle=OUTLINE,
            width=8
        )
        self.browse_dir_btn.pack(side="left")

        # Dry Run 选项
        self.dry_run_var = tk.BooleanVar(value=True)
        ttkb.Checkbutton(
            frame,
            text="试运行 (Dry Run) - 仅分析日志，不写入数据库",
            variable=self.dry_run_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=10)

        # 数据库路径输入
        db_frame = ttkb.Frame(frame)
        db_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        db_frame.grid_columnconfigure(1, weight=1)

        ttkb.Label(db_frame, text="数据库路径 (可选):", width=15).grid(row=0, column=0, padx=5, sticky="w")

        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttkb.Entry(db_frame, textvariable=self.db_path_var, width=50)
        self.db_path_entry.grid(row=0, column=1, padx=5, sticky="ew")

        self.browse_db_btn = ttkb.Button(
            db_frame,
            text="浏览数据库...",
            command=self._browse_db,
            bootstyle=OUTLINE,
            width=8
        )
        self.browse_db_btn.grid(row=0, column=2, padx=5)

        self.recovery_widgets = [
            self.log_path_entry, self.browse_file_btn, self.browse_dir_btn,
            self.dry_run_var, self.db_path_entry, self.browse_db_btn
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

        # 使用统一配置管理器或独立保存
        if self._config_manager:
            self._config_manager.save()
        else:
            self.config.save(self.config_file)

    def _update_options_state(self, enabled: bool) -> None:
        """更新选项控件状态"""
        state = 'normal' if enabled else 'disabled'

        for widget in self.recovery_widgets:
            if isinstance(widget, (ttkb.Entry, ttkb.Button)):
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

        # 清空日志
        self.clear_log()

        # 禁用所有输入控件并更新按钮状态为加载中
        self._set_all_inputs_disabled(True)
        self.start_button.config(
            state="disabled",
            text="⏳ 恢复执行中..."
        )

        # 使用线程执行，避免 UI 阻塞
        import threading
        def run_task():
            try:
                success = self._execute_script(args)
                # 执行完成后恢复 UI
                self.after(0, lambda: self._on_task_complete(success))
            except Exception as e:
                self.after(0, lambda: self._on_task_error(e))
        
        thread = threading.Thread(target=run_task)
        thread.start()

    def _set_all_inputs_disabled(self, disabled: bool) -> None:
        """禁用/启用所有输入控件"""
        state = "disabled" if disabled else "normal"
        
        for widget in self.recovery_widgets:
            if isinstance(widget, (ttkb.Entry, ttkb.Button)):
                widget['state'] = state if not disabled else 'disabled'

    def _on_task_complete(self, success: bool) -> None:
        """任务完成回调"""
        self.start_button.config(state="normal", text="▶ 开始恢复")
        self._set_all_inputs_disabled(False)
        
        if success:
            self._log("\n✅ 恢复执行完成\n")
        else:
            self._log("\n❌ 恢复执行失败\n")

    def _on_task_error(self, error: Exception) -> None:
        """任务错误回调"""
        self.start_button.config(state="normal", text="▶ 开始恢复")
        self._set_all_inputs_disabled(False)
        self._log(f"\n❌ 任务异常：{str(error)}\n")

    def on_closing(self) -> None:
        """窗口关闭前的处理"""
        try:
            self._save_config_from_ui()
        except Exception as e:
            print(f"关闭时保存 Recovery 配置失败：{e}")
