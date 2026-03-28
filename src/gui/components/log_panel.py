"""日志输出面板组件"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
from typing import Optional, Callable, Any


class LogPanel(ttk.Frame):
    """
    可复用的日志输出面板组件
    
    提供日志文本显示、自动滚动、队列消息处理功能。
    """
    
    def __init__(
        self,
        master: Any,
        title: str = "日志输出",
        font_family: str = "Courier New",
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
        
        self.output_queue: queue.Queue = queue.Queue()
        self._process_id: Optional[str] = None
        
        self._create_widgets(title, font_family, font_size)
    
    def _create_widgets(self, title: str, font_family: str, font_size: int) -> None:
        """创建组件内的 widgets"""
        # 日志文本区域
        log_frame = ttk.LabelFrame(self, text=title)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            state="disabled",
            font=(font_family, font_size)
        )
        self.log_text.pack(fill="both", expand=True)
    
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
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)  # 自动滚动到底部
        self.log_text.config(state="disabled")
    
    def set_status(self, status: str) -> None:
        """
        设置状态栏文本（如果有的话）
        
        Args:
            status: 状态文本
        """
        # 此方法可由子类扩展添加状态栏
        pass
