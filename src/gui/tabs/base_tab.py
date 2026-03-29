"""选项卡基类"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any, List
from pathlib import Path

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..services.task_executor import TaskExecutor
from ..components.log_panel import LogPanel
from ..styles import theme, get_colors, get_fonts, get_spacing


class BaseTab(ttkb.Frame):
    """
    所有功能选项卡的抽象基类

    提供通用的任务执行逻辑、日志处理、UI 状态管理。
    子类需要实现 _create_options_panel() 和 start_task() 方法。
    """

    def __init__(
        self,
        master: Any,
        title: str,
        script_name: str,
        config_service: Any
    ):
        """
        初始化选项卡

        Args:
            master: 父容器（Notebook）
            title: 选项卡标题
            script_name: 要执行的脚本文件名
            config_service: 配置服务实例
        """
        super().__init__(master)
        self.master = master
        self.title = title
        self.script_name = script_name
        self.config_service = config_service

        # 任务执行器
        self.task_executor: Optional[TaskExecutor] = None
        self._is_running = False

        # 组件引用
        self.options_frame: Optional[ttkb.Frame] = None
        self.log_panel: Optional[LogPanel] = None
        self.start_button: Optional[ttkb.Button] = None
        self.stop_button: Optional[ttkb.Button] = None
        self.status_bar: Optional[ttkb.Label] = None
        self.progress_bar: Optional[ttkb.Progressbar] = None

        # 布局 - 使用 PanedWindow 实现可调整布局
        self.pack(fill="both", expand=True, padx=12, pady=12)

        # 设置 UI（立即创建所有 UI 控件）
        self._setup_ui()

        # 初始化任务执行器（需要 master.after 支持）
        self.after(100, self._init_task_executor)

    def _setup_ui(self) -> None:
        """设置 UI 布局"""
        # 使用垂直布局，分为三个区域
        self.grid_rowconfigure(0, weight=0)  # 选项面板
        self.grid_rowconfigure(1, weight=0)  # 控制按钮
        self.grid_rowconfigure(2, weight=1)  # 日志面板
        self.grid_rowconfigure(3, weight=0)  # 状态栏
        self.grid_columnconfigure(0, weight=1)

        # 1. 选项面板 - 使用卡片式布局
        self._create_options_panel()

        # 2. 控制按钮区
        self._create_control_panel()

        # 3. 日志输出区
        self._create_log_panel()

        # 4. 状态栏（带进度条）
        self._create_status_bar()

    def _create_options_panel(self) -> None:
        """
        创建选项配置面板

        子类必须实现此方法来创建自己的选项控件。
        """
        raise NotImplementedError("子类必须实现 _create_options_panel() 方法")

    def _create_control_panel(self) -> None:
        """创建控制按钮区"""
        control_frame = ttkb.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)

        # 按钮容器
        btn_container = ttkb.Frame(control_frame)
        btn_container.grid(row=0, column=0, columnspan=2, sticky="w", padx=5)

        self.start_button = ttkb.Button(
            btn_container,
            text="▶ 开始任务",
            command=self.start_task,
            bootstyle=SUCCESS,
            width=15
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttkb.Button(
            btn_container,
            text="⏹ 停止任务",
            command=self.stop_task,
            bootstyle=DANGER,
            state="disabled",
            width=15
        )
        self.stop_button.pack(side="left", padx=5)

        # 状态指示器（右侧）
        self.status_indicator = ttkb.Label(
            control_frame,
            text="● 就绪",
            font=(get_fonts().FAMILY, get_fonts().SIZE_NORMAL, "bold")
        )
        self.status_indicator.grid(row=0, column=2, sticky="e", padx=10)

    def _create_log_panel(self) -> None:
        """创建日志输出区"""
        # 使用 LabelFrame 包装日志面板
        log_container = ttk.LabelFrame(
            self,
            text="📋 任务日志"
        )
        log_container.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        self.log_panel = LogPanel(log_container, title="")
        self.log_panel.pack(fill="both", expand=True)

    def _create_status_bar(self) -> None:
        """创建带进度条的状态栏"""
        status_frame = ttkb.Frame(self)
        status_frame.grid(row=3, column=0, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        # 状态文本
        self.status_bar = ttkb.Label(
            status_frame,
            text="状态：空闲",
            anchor="w"
        )
        self.status_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # 进度条
        self.progress_bar = ttkb.Progressbar(
            status_frame,
            mode="indeterminate",
            length=200
        )
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=(10, 5), pady=5)

    def _init_task_executor(self) -> None:
        """初始化任务执行器"""
        self.task_executor = TaskExecutor(log_callback=self._log)
        # 将 master 引用传递给 task_executor 用于 after 调用
        self.task_executor.master = self.master

    def _log(self, message: str) -> None:
        """
        日志输出回调

        Args:
            message: 日志消息
        """
        if self.log_panel:
            self.log_panel.log(message)

    def start_task(self) -> None:
        """
        开始任务

        子类必须实现此方法来构建命令参数并启动任务。
        """
        raise NotImplementedError("子类必须实现 start_task() 方法")

    def stop_task(self) -> None:
        """停止任务"""
        if self.task_executor:
            self.task_executor.stop()

    def _execute_script(self, args: List[str]) -> bool:
        """
        执行脚本的便捷方法

        Args:
            args: 命令行参数列表

        Returns:
            是否成功启动任务
        """
        if not self.task_executor:
            self._log("错误：任务执行器未初始化\n")
            return False

        return self.task_executor.execute(self.script_name, args)

    def _update_ui_state(self, is_running: bool) -> None:
        """
        根据任务状态更新 UI

        Args:
            is_running: 是否正在运行
        """
        self._is_running = is_running

        # 更新按钮状态
        if self.start_button:
            self.start_button['state'] = 'disabled' if is_running else 'normal'
        if self.stop_button:
            self.stop_button['state'] = 'normal' if is_running else 'disabled'

        # 更新状态指示器
        if self.status_indicator:
            if is_running:
                self.status_indicator.config(text="● 运行中")
            else:
                self.status_indicator.config(text="● 就绪")

        # 更新状态栏
        if self.status_bar:
            self.status_bar['text'] = "状态：任务执行中..." if is_running else "状态：空闲"

        # 更新进度条
        if self.progress_bar:
            if is_running:
                self.progress_bar.start()
            else:
                self.progress_bar.stop()

        # 更新选项控件状态
        self._update_options_state(not is_running)

    def _update_options_state(self, enabled: bool) -> None:
        """
        更新选项控件状态

        Args:
            enabled: 是否启用
        """
        # 子类可以覆盖此方法来实现自己的控件状态更新逻辑
        if self.options_frame:
            self._set_children_state(self.options_frame, enabled)

    def _set_children_state(self, parent: tk.Widget, state: str) -> None:
        """递归设置子控件状态"""
        for child in parent.winfo_children():
            if isinstance(child, (ttkb.Button, ttkb.Entry, ttkb.Combobox, ttkb.Checkbutton, ttkb.Radiobutton)):
                try:
                    if isinstance(child, ttkb.Combobox):
                        child['state'] = 'readonly' if state else 'disabled'
                    else:
                        child['state'] = 'normal' if state else 'disabled'
                except Exception:
                    pass
            # 递归处理容器
            if isinstance(child, (ttkb.Frame, ttk.LabelFrame)):
                self._set_children_state(child, state)

    def clear_log(self) -> None:
        """清空日志"""
        if self.log_panel:
            self.log_panel.clear()

    def validate_db_selection(self) -> bool:
        """验证数据库选择"""
        # 子类可以调用此方法进行数据库选择验证
        return True

    def validate_model_selection(self) -> bool:
        """验证模型选择"""
        # 子类可以调用此方法进行模型选择验证
        return True
