#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import queue
import os
import sys
import json
from pathlib import Path
from typing import List, Optional, Union

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
# 注意：这个脚本作为模块被导入时，__file__ 指向的是当前模块的路径
# 但通常 gui_launcher.py 仍然是入口点，所以这里可能不需要重复添加
# 如果作为独立模块运行或导入路径有问题，可以取消下面几行的注释
# project_root = Path(__file__).parent.parent.parent.absolute() 
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))

from src.config import config_manager
# from src.data_manager import DataManager # 在基类中似乎未直接使用


class TaskExecutorTab(ttk.Frame):
    """
    一个抽象基类，为每个功能选项卡提供通用的任务执行逻辑。
    它处理子进程的启动、停止、日志输出等。
    """
    def __init__(self, master, script_name: str):
        super().__init__(master)
        self.script_name = script_name
        # 自动定位脚本路径 (更新为从项目根目录的 scripts 文件夹查找)
        # 获取项目根目录，假设此模块位于 src/gui/
        project_root = Path(__file__).parent.parent.parent.absolute()
        self.script_path = project_root / 'scripts' / self.script_name

        # 初始化任务相关成员变量
        self.process: Optional[subprocess.Popen] = None
        self.task_thread: Optional[threading.Thread] = None
        self.output_queue: queue.Queue = queue.Queue()
        
        # 日志区域偏好设置
        self.log_preferences_file = Path('config') / 'log_preferences.json'
        
        # 不再在这里设置布局管理器，让子类控制布局

    def get_tab_name(self):
        """获取选项卡名称，用于保存偏好设置"""
        # 子类应该重写此方法以返回特定的选项卡名称
        return self.__class__.__name__


    def _create_common_widgets(self, main_container):
        """在传入的 main_container 框架中创建通用的控件，如控制按钮和日志区域。"""
        # main_container 由调用者创建和布局
        main_container.rowconfigure(0, weight=0)  # 控制按钮区域不扩展
        main_container.rowconfigure(1, weight=1)  # 日志区域扩展
        main_container.columnconfigure(0, weight=1)
        
        # --- 控制与状态区 ---
        control_frame = ttk.Frame(main_container)
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=10)

        # 使用更具描述性的默认文本
        start_text = getattr(self, 'start_button_text', "开始任务")
        stop_text = getattr(self, 'stop_button_text', "停止任务")
        
        self.start_button = ttk.Button(control_frame, text=start_text, command=self.start_task)
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)

        self.stop_button = ttk.Button(control_frame, text=stop_text, command=self.stop_task, state="disabled")
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)

        # --- 日志输出区 ---
        self.log_frame = ttk.LabelFrame(main_container, text="日志输出")
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.log_frame.rowconfigure(0, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, 
            wrap=tk.WORD, 
            state="disabled", 
            font=("Courier New", 9)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # --- 状态栏 ---
        self.status_bar = ttk.Label(main_container, text="状态: 空闲", relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))

    def log_message(self, message: Union[str, bytes]):
        """
        将消息放入队列，以便在主线程中安全地更新GUI。
        
        Args:
            message: 要记录的消息，可以是字符串或字节
        """
        if message:
            # 确保消息是正确的编码
            if isinstance(message, bytes):
                try:
                    message = message.decode('utf-8')
                except UnicodeDecodeError:
                    message = message.decode('utf-8', errors='replace')
            self.output_queue.put(message)

    def _run_task_thread(self, command: List[str]):
        """在后台线程中执行子进程。
        
        Args:
            command: 要执行的命令列表
        """
        try:
            if not os.path.exists(self.script_path):
                self.output_queue.put(
                    f"错误: 找不到脚本 '{self.script_name}'！请确保它与GUI启动器在同一目录下。")
                self.output_queue.put(None)
                return

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            # 设置环境变量确保子进程编码正确
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            # 在Windows上额外设置编码环境变量
            if sys.platform.startswith('win'):
                env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=creation_flags,
                env=env  # 传递环境变量
            )
            
            if self.process.stdout is not None:
                for line in iter(self.process.stdout.readline, ''):
                    # 确保消息是正确的编码
                    if isinstance(line, bytes):
                        try:
                            line = line.decode('utf-8')
                        except UnicodeDecodeError:
                            line = line.decode('utf-8', errors='replace')
                    self.output_queue.put(line)
                self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.output_queue.put(f"****** 任务执行失败 ******{e}")
        finally:
            self.output_queue.put(None)  # 任务结束信号

    def process_queue(self):
        """
        从队列中批量获取消息并更新GUI，以减少UI操作频率，提升流畅度。
        """
        messages_to_log = []
        task_finished = False
        
        try:
            for _ in range(200): 
                line = self.output_queue.get_nowait()
                if line is None:
                    task_finished = True
                    break
                messages_to_log.append(line)
        except queue.Empty:
            pass

        if messages_to_log:
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, "".join(messages_to_log))
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

        if task_finished:
            self._on_task_finished()
        
        self.master.after(100, self.process_queue)

    def _on_task_finished(self):
        """任务完成时的处理逻辑。"""
        return_code = self.process.returncode if self.process else -1
        final_message = "" + "="*80 + ""
        
        if return_code == 0:
            final_message += "任务执行成功完成。"
            self.status_bar['text'] = "状态: 已完成"
        else:
            final_message += f"任务执行结束，返回代码: {return_code} (0表示成功)。"
            self.status_bar['text'] = f"状态: 错误 (代码: {return_code})"
        
        self.output_queue.put(final_message)
        
        self.process = None
        self._update_ui_state(is_running=False)

    def stop_task(self):
        """终止正在运行的子进程。"""
        if self.process:
            self.log_message("****** 正在尝试终止任务... ******")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
                self.log_message("任务已终止。")
            except subprocess.TimeoutExpired:
                self.log_message("无法正常终止，将强制结束。")
                self.process.kill()
            self.output_queue.put(None)

    # 以下方法必须由子类实现
    def _create_widgets(self):
        """创建特定于选项卡的控件。必须由子类实现。"""
        raise NotImplementedError
    
    def start_task(self):
        """启动任务。必须由子类实现。"""
        raise NotImplementedError
    
    def _update_ui_state(self, is_running: bool = False):
        """更新UI状态。必须由子类实现。
        
        Args:
            is_running: 任务是否正在运行
        """
        raise NotImplementedError
