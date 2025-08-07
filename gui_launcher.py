#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import queue
import os
import sys

# 尝试导入原始项目的配置管理器以获取模型列表
try:
    from src.config_manager import config_manager
except ImportError:
    # 如果找不到模块，提供一个友好的回退方案
    def get_fallback_config_manager():
        class FallbackConfigManager:
            def list_model_configs(self):
                print("警告: 未能找到 'src.config_manager'。无法自动加载模型列表。请确保 gui_launcher.py 与项目结构保持一致。")
                return []
        return FallbackConfigManager()
    config_manager = get_fallback_config_manager()

class TaskExecutorTab(ttk.Frame):
    """
    一个抽象基类，为每个功能选项卡提供通用的任务执行逻辑。
    它处理子进程的启动、停止、日志输出等。
    """
    def __init__(self, master, script_name):
        super().__init__(master)
        self.script_name = script_name
        # 自动定位脚本路径
        self.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.script_name)

        # 初始化任务相关成员变量
        self.process = None
        self.task_thread = None
        self.output_queue = queue.Queue()

        self.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 子类必须在自己的构造函数中调用以下方法
        # self._create_widgets()
        # self.master.after(100, self.process_queue)

    def _create_common_widgets(self):
        """创建通用的控件，如控制按钮和日志区域。"""
        # --- 控制与状态区 ---
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=5, pady=10)

        self.start_button = ttk.Button(control_frame, text="开始任务", command=self.start_task)
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)

        self.stop_button = ttk.Button(control_frame, text="停止任务", command=self.stop_task, state="disabled")
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)

        # --- 日志输出区 ---
        log_frame = ttk.LabelFrame(self, text="日志输出")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", font=("Courier New", 9))
        self.log_text.pack(fill="both", expand=True)

        # --- 状态栏 ---
        self.status_bar = ttk.Label(self, text="状态: 空闲", relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x", pady=(5,0))

    def log_message(self, message):
        """
        【此方法已废弃】
        日志消息现在由 `process_queue` 方法批量处理以提高性能。
        保留此空方法或直接删除它都可以，但建议删除以保持代码整洁。
        如果您在代码的其他地方（除了process_queue）直接调用了它，
        可以将其改为 self.output_queue.put(message + '\n')。
        """
        # 为了安全起见，我们将其重定向到队列，以防有其他地方调用
        if message:
            self.output_queue.put(message)

    def _run_task_thread(self, command):
        """在后台线程中执行子进程。"""
        try:
            if not os.path.exists(self.script_path):
                self.output_queue.put(f"错误: 找不到脚本 '{self.script_name}'！请确保它与GUI启动器在同一目录下。\n")
                self.output_queue.put(None)
                return

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
                
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=creation_flags
            )
            
            if self.process.stdout is not None:
                for line in iter(self.process.stdout.readline, ''):
                    self.output_queue.put(line)
                self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.output_queue.put(f"\n****** 任务执行失败 ******\n{e}\n")
        finally:
            self.output_queue.put(None) # 任务结束信号

    def process_queue(self):
        """
        【优化版】从队列中批量获取消息并更新GUI，以减少UI操作频率，提升流畅度。
        """
        messages_to_log = []
        task_finished = False
        
        # 1. 批量从队列中取出数据
        try:
            # 单次最多处理200条消息，防止单次UI更新量过大导致卡顿，
            # 同时也避免了无限循环耗尽UI线程时间。
            for _ in range(200): 
                line = self.output_queue.get_nowait()
                if line is None:  # "None" 是任务结束的信号
                    task_finished = True
                    break
                messages_to_log.append(line)
        except queue.Empty:
            # 队列已空，正常现象
            pass
        # 2. 如果有日志，则进行一次性UI更新
        if messages_to_log:
            self.log_text.config(state="normal")
            # 将所有日志消息合并为单个字符串后插入，这是最高效的方式
            self.log_text.insert(tk.END, "".join(messages_to_log))
            self.log_text.see(tk.END) # 滚动条也只移动一次
            self.log_text.config(state="disabled")
        # 3. 如果收到了任务结束信号，则处理收尾工作
        if task_finished:
            self._on_task_finished()
        
        # 4. 安排下一次检查
        # 即使任务结束，也保持轮询，以便GUI可以启动新任务
        self.master.after(100, self.process_queue)

    def _on_task_finished(self):
        # ... 此方法保持不变 ...
        return_code = self.process.returncode if self.process else -1
        # 准备最终的日志消息
        final_message = "\n" + "="*80 + "\n"
        if return_code == 0:
            final_message += "任务执行成功完成。\n"
            self.status_bar['text'] = "状态: 已完成"
        else:
            final_message += f"任务执行结束，返回代码: {return_code} (0表示成功)。\n"
            self.status_bar['text'] = f"状态: 错误 (代码: {return_code})"
        
        # 将最终消息放入队列，由 process_queue 统一处理显示
        self.output_queue.put(final_message)
        
        self.process = None
        self._update_ui_state(is_running=False)
    def stop_task(self):
        """终止正在运行的子进程。"""
        if self.process:
            self.log_message("\n****** 正在尝试终止任务... ******\n")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
                self.log_message("任务已终止。\n")
            except subprocess.TimeoutExpired:
                self.log_message("无法正常终止，将强制结束。\n")
                self.process.kill()
            self.output_queue.put(None)

    # 以下方法必须由子类实现
    def _create_widgets(self): raise NotImplementedError
    def start_task(self): raise NotImplementedError
    def _update_ui_state(self, is_running=False): raise NotImplementedError

class DistributionTab(TaskExecutorTab):
    """任务分发功能的UI选项卡。"""
    def __init__(self, master):
        super().__init__(master, "distribute_tasks.py")
        self._create_widgets()
        super()._create_common_widgets()  # 先创建通用控件，包括 start_button
        self._update_ui_state()  # 然后再更新 UI 状态
        self.master.after(100, self.process_queue)

    def _create_widgets(self):
        # --- 1. 模型选择区 ---
        model_frame = ttk.LabelFrame(self, text="模型选择")
        model_frame.pack(fill="x", padx=5, pady=5)
        
        self.model_choice_var = tk.StringVar(value="single")
        self.single_model_radio = ttk.Radiobutton(model_frame, text="指定单个模型", variable=self.model_choice_var, value="single", command=self._update_ui_state)
        self.single_model_radio.pack(side="left", padx=5, pady=5)
        
        self.model_combobox_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(model_frame, textvariable=self.model_combobox_var, state="readonly", width=30)
        self.model_combobox.pack(side="left", padx=5, pady=5)
        self._populate_models()

        self.all_models_radio = ttk.Radiobutton(model_frame, text="使用所有已配置的模型", variable=self.model_choice_var, value="all", command=self._update_ui_state)
        self.all_models_radio.pack(side="left", padx=20, pady=5)

        # --- 2. ID来源选择区 ---
        id_source_frame = ttk.LabelFrame(self, text="ID来源选择")
        id_source_frame.pack(fill="x", padx=5, pady=5)

        # 使用Grid布局管理器
        self.id_source_var = tk.StringVar(value="file")
        
        # 第一行：单文件选择
        self.id_file_radio = ttk.Radiobutton(id_source_frame, text="指定单个ID文件", 
                                           variable=self.id_source_var, value="file", 
                                           command=self._update_ui_state)
        self.id_file_radio.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.id_file_path_var = tk.StringVar()
        self.id_file_entry = ttk.Entry(id_source_frame, textvariable=self.id_file_path_var)
        self.id_file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.id_file_browse_btn = ttk.Button(id_source_frame, text="浏览...", 
                                           command=self._browse_file)
        self.id_file_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # 第二行：目录选择
        self.id_dir_radio = ttk.Radiobutton(id_source_frame, text="指定ID文件目录", 
                                          variable=self.id_source_var, value="dir", 
                                          command=self._update_ui_state)
        self.id_dir_radio.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.id_dir_path_var = tk.StringVar()
        self.id_dir_entry = ttk.Entry(id_source_frame, textvariable=self.id_dir_path_var)
        self.id_dir_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.id_dir_browse_btn = ttk.Button(id_source_frame, text="浏览目录...", 
                                          command=self._browse_dir)
        self.id_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)

        # 配置列权重，使Entry控件能够自动扩展
        id_source_frame.columnconfigure(1, weight=1)

        # --- 3. 其他选项区 ---
        options_frame = ttk.LabelFrame(self, text="其他选项")
        options_frame.pack(fill="x", padx=5, pady=5)

        self.force_rerun_var = tk.BooleanVar()
        self.force_rerun_check = ttk.Checkbutton(options_frame, text="强制重跑", variable=self.force_rerun_var)
        self.force_rerun_check.pack(side="left", padx=10, pady=5)
        
        self.fresh_start_var = tk.BooleanVar()
        self.fresh_start_check = ttk.Checkbutton(options_frame, text="全新开始", variable=self.fresh_start_var)
        self.fresh_start_check.pack(side="left", padx=10, pady=5)
        
        ttk.Label(options_frame, text="批次大小:").pack(side="left", padx=(20, 5), pady=5)
        self.chunk_size_var = tk.StringVar(value="1000")
        self.chunk_size_entry = ttk.Entry(options_frame, textvariable=self.chunk_size_var, width=10)
        self.chunk_size_entry.pack(side="left", padx=5, pady=5)

    def _populate_models(self):
        try:
            models = config_manager.list_model_configs()
            if models:
                self.model_combobox['values'] = models
                self.model_combobox.set(models[0])
            else:
                self.model_combobox.set("无可用模型")
        except Exception as e:
            self.model_combobox.set("加载失败")
            self.log_message(f"错误: 加载模型配置失败: {e}\n")

    def _update_ui_state(self, is_running=False):
        state = "disabled" if is_running else "normal"
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"

        self.model_combobox['state'] = state if self.model_choice_var.get() == "single" else "disabled"
        self.id_file_entry['state'] = state if self.id_source_var.get() == "file" else "disabled"
        self.id_file_browse_btn['state'] = state if self.id_source_var.get() == "file" else "disabled"
        self.id_dir_entry['state'] = state if self.id_source_var.get() == "dir" else "disabled"
        self.id_dir_browse_btn['state'] = state if self.id_source_var.get() == "dir" else "disabled"

        for radio in [self.single_model_radio, self.all_models_radio, self.id_file_radio, self.id_dir_radio]:
            radio['state'] = state
        for widget in [self.force_rerun_check, self.fresh_start_check, self.chunk_size_entry]:
            widget['state'] = state

    def _browse_file(self):
        path = filedialog.askopenfilename(title="选择ID文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if path: self.id_file_path_var.set(path)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="选择ID文件所在目录", initialdir=os.path.dirname(self.id_dir_path_var.get()) if self.id_dir_path_var.get() else None)
        if path: 
            # 确保使用标准化的路径分隔符
            path = os.path.normpath(path)
            self.id_dir_path_var.set(path)

    def start_task(self):
        command = [sys.executable, self.script_path]
        
        if self.model_choice_var.get() == "single":
            model_name = self.model_combobox_var.get()
            if not model_name or "无" in model_name:
                self.log_message("错误: 请选择一个有效的模型。\n"); return
            command.extend(["--model", model_name])
        else:
            command.append("--all-models")

        if self.id_source_var.get() == "file":
            id_file = self.id_file_path_var.get()
            if not id_file: self.log_message("错误: 请指定一个ID文件路径。\n"); return
            command.extend(["--id-file", id_file])
        else:
            id_dir = self.id_dir_path_var.get()
            if not id_dir: self.log_message("错误: 请指定一个ID文件目录。\n"); return
            command.extend(["--id-dir", id_dir])

        if self.force_rerun_var.get(): command.append("--force-rerun")
        if self.fresh_start_var.get(): command.append("--fresh-start")
        
        chunk_size = self.chunk_size_var.get()
        if chunk_size.isdigit() and int(chunk_size) > 0:
            command.extend(["--chunk-size", chunk_size])
        else:
            self.log_message(f"警告: 批次大小 '{chunk_size}' 无效，将使用脚本默认值。\n")

        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        self.log_message(f"执行命令: {' '.join(command)}\n" + "="*80 + "\n")
        self._update_ui_state(is_running=True)
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()

class SamplingTab(TaskExecutorTab):
    """随机抽样功能的UI选项卡。"""
    def __init__(self, master):
        super().__init__(master, "random_sample.py")
        self._create_widgets()
        self.master.after(100, self.process_queue)

    def _create_widgets(self):
        # --- 1. 数据库和抽样数量 ---
        main_options_frame = ttk.LabelFrame(self, text="基本设置")
        main_options_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(main_options_frame, text="数据库文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.db_path_var = tk.StringVar(value="poetry.db")
        self.db_entry = ttk.Entry(main_options_frame, textvariable=self.db_path_var, width=50)
        self.db_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.db_browse_btn = ttk.Button(main_options_frame, text="浏览...", command=self._browse_db)
        self.db_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(main_options_frame, text="抽样数量:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.count_var = tk.StringVar(value="100")
        self.count_entry = ttk.Entry(main_options_frame, textvariable=self.count_var, width=15)
        self.count_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        main_options_frame.columnconfigure(1, weight=1)

        # --- 2. 排序方式 ---
        self.sort_frame = ttk.LabelFrame(self, text="排序方式")
        self.sort_frame.pack(fill="x", padx=5, pady=5)
        self.sort_choice_var = tk.StringVar(value="shuffle")
        # 将父控件也更新为 self.sort_frame (保持代码一致性)
        ttk.Radiobutton(self.sort_frame, text="随机排序 (默认)", variable=self.sort_choice_var, value="shuffle").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="按ID升序", variable=self.sort_choice_var, value="sort").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="不排序", variable=self.sort_choice_var, value="no-shuffle").pack(side="left", padx=10)



        # --- 3. 输出设置 ---
        output_frame = ttk.LabelFrame(self, text="输出设置")
        output_frame.pack(fill="x", padx=5, pady=5)
        self.output_mode_var = tk.StringVar(value="dir")
        
        # 目录输出模式
        self.dir_mode_radio = ttk.Radiobutton(output_frame, text="输出到目录", variable=self.output_mode_var, value="dir", command=self._update_ui_state)
        self.dir_mode_radio.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(output_frame, text="目录路径:").grid(row=1, column=0, padx=(25, 5), pady=5, sticky="w")
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.output_dir_browse_btn = ttk.Button(output_frame, text="浏览...", command=self._browse_output_dir)
        self.output_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(output_frame, text="分段文件数:").grid(row=2, column=0, padx=(25, 5), pady=5, sticky="w")
        self.num_files_var = tk.StringVar(value="1")
        self.num_files_entry = ttk.Entry(output_frame, textvariable=self.num_files_var, width=15)
        self.num_files_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 单文件输出模式
        self.file_mode_radio = ttk.Radiobutton(output_frame, text="输出到单个文件", variable=self.output_mode_var, value="file", command=self._update_ui_state)
        self.file_mode_radio.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10,5))
        ttk.Label(output_frame, text="文件路径:").grid(row=4, column=0, padx=(25, 5), pady=5, sticky="w")
        self.output_file_var = tk.StringVar()
        self.output_file_entry = ttk.Entry(output_frame, textvariable=self.output_file_var)
        self.output_file_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.output_file_browse_btn = ttk.Button(output_frame, text="另存为...", command=self._browse_save_file)
        self.output_file_browse_btn.grid(row=4, column=2, padx=5, pady=5)
        output_frame.columnconfigure(1, weight=1)

        super()._create_common_widgets()
        self.start_button.config(text="开始抽样")
        self.stop_button.config(text="停止抽样")
        self._update_ui_state()
    
    def _update_ui_state(self, is_running=False):
        state = "disabled" if is_running else "normal"
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"

        for widget in [self.db_entry, self.db_browse_btn, self.count_entry, self.dir_mode_radio, self.file_mode_radio]:
            widget['state'] = state
        # 使用isinstance检查控件类型
        for child in self.sort_frame.winfo_children():
            if isinstance(child, (ttk.Radiobutton, ttk.Button, ttk.Entry)):
                child.configure(state=state)

        output_mode = self.output_mode_var.get()
        dir_state = state if output_mode == 'dir' else 'disabled'
        for widget in [self.output_dir_entry, self.output_dir_browse_btn, self.num_files_entry]:
            widget['state'] = dir_state

        file_state = state if output_mode == 'file' else 'disabled'
        for widget in [self.output_file_entry, self.output_file_browse_btn]:
            widget['state'] = file_state

    def _browse_db(self):
        path = filedialog.askopenfilename(title="选择数据库文件", filetypes=[("SQLite数据库", "*.db"), ("所有文件", "*.*")])
        if path: self.db_path_var.set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path: self.output_dir_var.set(path)

    def _browse_save_file(self):
        path = filedialog.asksaveasfilename(title="保存到文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")], defaultextension=".txt")
        if path: self.output_file_var.set(path)

    def start_task(self):
        command = [sys.executable, self.script_path]

        db_path = self.db_path_var.get()
        if not db_path: self.log_message("错误: 请指定数据库文件路径。\n"); return
        command.extend(["--db", db_path])

        count = self.count_var.get()
        if not (count.isdigit() and int(count) > 0):
            self.log_message(f"错误: 抽样数量 '{count}' 必须为正整数。\n"); return
        command.extend(["-n", count])

        sort_mode = self.sort_choice_var.get()
        if sort_mode == 'sort': command.append("--sort")
        elif sort_mode == 'no-shuffle': command.append("--no-shuffle")

        if self.output_mode_var.get() == 'file':
            output_file = self.output_file_var.get()
            if not output_file: self.log_message("错误: 请指定输出文件路径。\n"); return
            command.extend(["--output-file", output_file])
        else: # dir mode
            output_dir = self.output_dir_var.get()
            if output_dir: command.extend(["--output-dir", output_dir])
            
            num_files = self.num_files_var.get()
            if not (num_files.isdigit() and int(num_files) > 0):
                self.log_message(f"错误: 分段文件数 '{num_files}' 必须为正整数。\n"); return
            command.extend(["--num-files", num_files])

        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        self.log_message(f"执行命令: {' '.join(command)}\n" + "="*80 + "\n")
        self._update_ui_state(is_running=True)
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()

class PoetryToolGUI(tk.Tk):
    """主应用程序窗口，包含所有功能选项卡。"""
    def __init__(self):
        super().__init__()
        self.title("诗词处理工具集")
        self.geometry("850x700")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        dist_tab = DistributionTab(notebook)
        sampling_tab = SamplingTab(notebook)

        notebook.add(dist_tab, text="  任务分发 (Task Distribution)  ")
        notebook.add(sampling_tab, text="  随机抽样 (Random Sampling)  ")

if __name__ == "__main__":
    app = PoetryToolGUI()
    app.mainloop()
