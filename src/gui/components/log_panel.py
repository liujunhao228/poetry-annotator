"""日志输出面板组件"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
from typing import Optional, Callable, Any, Dict
import re

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..styles import get_colors, get_fonts


class LogPanel(ttkb.Frame):
    """
    可复用的日志输出面板组件

    提供日志文本显示、自动滚动、队列消息处理、日志级别过滤功能。
    """

    def __init__(
        self,
        master: Any,
        title: str = "日志输出",
        font_family: str = "Consolas",
        font_size: int = 9
    ):
        """
        初始化日志面板

        Args:
            master: 父容器
            title: 分组框标题
            font_family: 字体
            font_size: 字体大小
        """
        super().__init__(master)

        self._colors = get_colors()
        self.output_queue: queue.Queue = queue.Queue()
        self._process_id: Optional[str] = None
        
        # 日志级别过滤
        self._log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        self._enabled_levels = set(self._log_levels)

        self._create_widgets(title, font_family, font_size)

    def _create_widgets(self, title: str, font_family: str, font_size: int) -> None:
        """创建组件内的 widgets"""
        # 工具栏
        toolbar_frame = ttkb.Frame(self)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        # 标题标签
        if title:
            ttkb.Label(
                toolbar_frame, 
                text=f"📋 {title}"
            ).pack(side="left", padx=5)
        
        # 右侧工具按钮
        right_frame = ttkb.Frame(toolbar_frame)
        right_frame.pack(side="right")
        
        # 清空按钮
        ttkb.Button(
            right_frame,
            text="清空",
            command=self.clear,
            bootstyle=OUTLINE,
            width=6
        ).pack(side="left", padx=2)
        
        # 导出按钮
        ttkb.Button(
            right_frame,
            text="导出",
            command=self._export_log,
            bootstyle=OUTLINE,
            width=6
        ).pack(side="left", padx=2)

        # 日志文本区域 - 使用边框样式
        log_frame = ttk.LabelFrame(self, text=title if title else "日志")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # 内部容器添加间距
        inner = ttkb.Frame(log_frame)
        inner.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            inner,
            wrap=tk.WORD,
            state="disabled",
            font=(font_family, font_size),
            background=self._colors.BACKGROUND_SECONDARY,
            insertbackground=self._colors.TEXT_PRIMARY,
            selectbackground=self._colors.TABLE_SELECTED
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 配置日志级别颜色标签
        self._configure_tags()

    def _configure_tags(self) -> None:
        """配置文本标签样式"""
        self.log_text.tag_configure("DEBUG", foreground=self._colors.TEXT_SECONDARY)
        self.log_text.tag_configure("INFO", foreground=self._colors.SUCCESS)
        self.log_text.tag_configure("WARNING", foreground=self._colors.WARNING)
        self.log_text.tag_configure("ERROR", foreground=self._colors.DANGER)
        self.log_text.tag_configure("timestamp", foreground=self._colors.TEXT_SECONDARY)
        self.log_text.tag_configure("success", foreground=self._colors.SUCCESS)
        self.log_text.tag_configure("error", foreground=self._colors.DANGER)

    def log(self, message: str) -> None:
        """
        将消息放入队列（线程安全）

        Args:
            message: 要显示的日志消息
        """
        if message:
            self.output_queue.put(message)

    def clear(self) -> None:
        """清空日志内容"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def start_processing(self, interval_ms: int = 100) -> None:
        """
        启动队列消息处理

        Args:
            interval_ms: 检查队列的时间间隔（毫秒）
        """
        self._process_queue()

    def stop_processing(self) -> None:
        """停止队列消息处理"""
        if self._process_id:
            self.master.after_cancel(self._process_id)
            self._process_id = None

    def _process_queue(self) -> None:
        """从队列批量获取消息并更新 GUI"""
        messages_to_log = []

        try:
            # 批量获取最多 200 条消息
            for _ in range(200):
                line = self.output_queue.get_nowait()
                if line is None:  # 结束信号
                    break
                messages_to_log.append(line)
        except queue.Empty:
            pass

        # 批量更新 UI
        if messages_to_log:
            self._append_messages("".join(messages_to_log))

        # 继续处理
        self._process_id = self.master.after(100, self._process_queue)

    def _append_messages(self, text: str) -> None:
        """追加消息到日志文本"""
        self.log_text.config(state="normal")
        
        # 按行处理，应用颜色标签
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            # 检测日志级别并应用标签
            tag = None
            if "[DEBUG]" in line or " DEBUG " in line:
                tag = "DEBUG"
            elif "[INFO]" in line or " INFO " in line:
                tag = "INFO"
            elif "[WARNING]" in line or " WARNING " in line:
                tag = "WARNING"
            elif "[ERROR]" in line or " ERROR " in line or "错误" in line or "失败" in line:
                tag = "ERROR"
            
            # 插入文本
            if tag and tag in self._enabled_levels:
                self.log_text.insert(tk.END, line + "\n", tag)
            else:
                self.log_text.insert(tk.END, line + "\n")
        
        self.log_text.see(tk.END)  # 自动滚动到底部
        self.log_text.config(state="disabled")

    def _export_log(self) -> None:
        """导出日志到文件"""
        from tkinter import filedialog
        import datetime
        
        file_path = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                ttkb.MessageBox.showerror("错误", f"导出失败：{str(e)}")

    def set_status(self, status: str) -> None:
        """
        设置状态栏文本（如果有的话）

        Args:
            status: 状态文本
        """
        # 此方法可由子类扩展添加状态栏
        pass
