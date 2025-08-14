#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import queue
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config_manager import config_manager
from src.data_manager import DataManager

class TaskExecutorTab(ttk.Frame):
    """
    一个抽象基类，为每个功能选项卡提供通用的任务执行逻辑。
    它处理子进程的启动、停止、日志输出等。
    """
    def __init__(self, master, script_name):
        super().__init__(master)
        self.script_name = script_name
        # 自动定位脚本路径 (更新为从项目根目录的 scripts 文件夹查找)
        project_root = Path(__file__).parent.parent.absolute()
        self.script_path = project_root / 'scripts' / self.script_name

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
        将消息放入队列，以便在主线程中安全地更新GUI。
        """
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
        return_code = self.process.returncode if self.process else -1
        final_message = "\n" + "="*80 + "\n"
        if return_code == 0:
            final_message += "任务执行成功完成。\n"
            self.status_bar['text'] = "状态: 已完成"
        else:
            final_message += f"任务执行结束，返回代码: {return_code} (0表示成功)。\n"
            self.status_bar['text'] = f"状态: 错误 (代码: {return_code})"
        
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
        self.config_file = Path('config') / 'gui_state.json'
        super().__init__(master, "distribute_tasks.py")
        self._create_widgets()
        super()._create_common_widgets()
        self.load_config()
        self._update_ui_state()
        self.master.after(100, self.process_queue)
    
    def save_config(self):
        config_data = {
            'console_log_level': self.console_log_level_var.get(),
            'file_log_level': self.file_log_level_var.get(),
            'model_choice': self.model_choice_var.get(),
            'selected_model': self.model_combobox_var.get(),
            'id_source': self.id_source_var.get(),
            'id_file_path': self.id_file_path_var.get(),
            'id_dir_path': self.id_dir_path_var.get(),
            'force_rerun': self.force_rerun_var.get(),
            'fresh_start': self.fresh_start_var.get(),
            'chunk_size': self.chunk_size_var.get(),
            'enable_file_log': self.enable_file_log_var.get(),
            'db_choice': self.db_choice_var.get(),
            'selected_db': self.db_combobox_var.get(),
        }
        try:
            config_dir = self.config_file.parent
            if config_dir and not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"GUI配置已成功保存到 {self.config_file}")
        except Exception as e:
            self.output_queue.put(f"错误: 保存GUI配置失败: {e}\n")
    
    def load_config(self):
        if not self.config_file.exists():
            print(f"未找到GUI配置文件 {self.config_file}，将使用默认值。")
            return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.console_log_level_var.set(config.get('console_log_level', self.console_log_level_var.get()))
            self.file_log_level_var.set(config.get('file_log_level', self.file_log_level_var.get()))
            self.model_choice_var.set(config.get('model_choice', self.model_choice_var.get()))
            selected_model = config.get('selected_model')
            if selected_model and selected_model in self.model_combobox['values']:
                self.model_combobox_var.set(selected_model)
            self.id_source_var.set(config.get('id_source', self.id_source_var.get()))
            self.id_file_path_var.set(config.get('id_file_path', ''))
            self.id_dir_path_var.set(config.get('id_dir_path', ''))
            self.force_rerun_var.set(config.get('force_rerun', False))
            self.fresh_start_var.set(config.get('fresh_start', False))
            self.chunk_size_var.set(config.get('chunk_size', self.chunk_size_var.get()))
            self.enable_file_log_var.set(config.get('enable_file_log', True))
            self.db_choice_var.set(config.get('db_choice', self.db_choice_var.get()))
            selected_db = config.get('selected_db')
            if selected_db and selected_db in self.db_combobox['values']:
                self.db_combobox_var.set(selected_db)
            print(f"GUI配置已从 {self.config_file} 加载。")
        except (json.JSONDecodeError, KeyError) as e:
            self.output_queue.put(f"警告: 加载GUI配置失败，文件可能已损坏。将使用默认值。\n错误: {e}\n")

    def _create_widgets(self):
        options_frame = ttk.LabelFrame(self, text="日志级别控制")
        options_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(options_frame, text="控制台日志级别:").pack(side="left", padx=(10, 5), pady=5)
        self.console_log_level_var = tk.StringVar(value="INFO")
        self.console_log_level_combo = ttk.Combobox(options_frame, textvariable=self.console_log_level_var, values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        self.console_log_level_combo.pack(side="left", padx=5, pady=5)
        ttk.Label(options_frame, text="文件日志级别:").pack(side="left", padx=(20, 5), pady=5)
        self.file_log_level_var = tk.StringVar(value="DEBUG")
        self.file_log_level_combo = ttk.Combobox(options_frame, textvariable=self.file_log_level_var, values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        self.file_log_level_combo.pack(side="left", padx=5, pady=5)
        
        # 数据库选择
        db_frame = ttk.LabelFrame(self, text="数据库选择")
        db_frame.pack(fill="x", padx=5, pady=5)
        self.db_choice_var = tk.StringVar(value="select")
        # 移除了"使用默认数据库"选项，直接显示数据库选择
        self.select_db_radio = ttk.Radiobutton(db_frame, text="选择数据库", variable=self.db_choice_var, value="select", command=self._update_ui_state)
        self.select_db_radio.pack(side="left", padx=5, pady=5)
        self.db_combobox_var = tk.StringVar()
        self.db_combobox = ttk.Combobox(db_frame, textvariable=self.db_combobox_var, state="readonly", width=30)
        self.db_combobox.pack(side="left", padx=5, pady=5)
        self._populate_databases()
        
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

        id_source_frame = ttk.LabelFrame(self, text="ID来源选择")
        id_source_frame.pack(fill="x", padx=5, pady=5)
        self.id_source_var = tk.StringVar(value="file")
        self.id_file_radio = ttk.Radiobutton(id_source_frame, text="指定单个ID文件", variable=self.id_source_var, value="file", command=self._update_ui_state)
        self.id_file_radio.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.id_file_path_var = tk.StringVar()
        self.id_file_entry = ttk.Entry(id_source_frame, textvariable=self.id_file_path_var)
        self.id_file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.id_file_browse_btn = ttk.Button(id_source_frame, text="浏览...", command=self._browse_file)
        self.id_file_browse_btn.grid(row=0, column=2, padx=5, pady=5)
        self.id_dir_radio = ttk.Radiobutton(id_source_frame, text="指定ID文件目录", variable=self.id_source_var, value="dir", command=self._update_ui_state)
        self.id_dir_radio.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.id_dir_path_var = tk.StringVar()
        self.id_dir_entry = ttk.Entry(id_source_frame, textvariable=self.id_dir_path_var)
        self.id_dir_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.id_dir_browse_btn = ttk.Button(id_source_frame, text="浏览目录...", command=self._browse_dir)
        self.id_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        id_source_frame.columnconfigure(1, weight=1)

        other_options_frame = ttk.LabelFrame(self, text="其他选项")
        other_options_frame.pack(fill="x", padx=5, pady=5)
        self.force_rerun_var = tk.BooleanVar(value=False)
        self.force_rerun_check = ttk.Checkbutton(other_options_frame, text="强制重跑", variable=self.force_rerun_var)
        self.force_rerun_check.pack(side="left", padx=10, pady=5)
        self.fresh_start_var = tk.BooleanVar(value=False)
        self.fresh_start_check = ttk.Checkbutton(other_options_frame, text="全新开始", variable=self.fresh_start_var)
        self.fresh_start_check.pack(side="left", padx=10, pady=5)
        ttk.Label(other_options_frame, text="批次大小:").pack(side="left", padx=(20, 5), pady=5)
        self.chunk_size_var = tk.StringVar(value="1000")
        self.chunk_size_entry = ttk.Entry(other_options_frame, textvariable=self.chunk_size_var, width=10)
        self.chunk_size_entry.pack(side="left", padx=5, pady=5)
        self.enable_file_log_var = tk.BooleanVar(value=True)
        self.enable_file_log_check = ttk.Checkbutton(other_options_frame, text="启用文件日志", variable=self.enable_file_log_var)
        self.enable_file_log_check.pack(side="left", padx=10, pady=5)

    def _populate_models(self):
        try:
            models = config_manager.list_model_configs()
            if models:
                self.model_combobox['values'] = models
                if not self.model_combobox_var.get():
                    self.model_combobox.set(models[0])
            else:
                self.model_combobox.set("无可用模型")
        except Exception as e:
            self.model_combobox.set("加载失败")
            self.output_queue.put(f"错误: 加载模型配置失败: {e}\n")

    def _populate_databases(self):
        try:
            db_config = config_manager.get_database_config()
            if 'db_paths' in db_config:
                db_names = list(db_config['db_paths'].keys())
                if db_names:
                    self.db_combobox['values'] = db_names
                    if not self.db_combobox_var.get():
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
            self.output_queue.put(f"错误: 加载数据库配置失败: {e}\n")

    def _update_ui_state(self, is_running=False):
        state = "disabled" if is_running else "normal"
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"
        self.console_log_level_combo['state'] = state
        self.file_log_level_combo['state'] = state
        is_select_db = self.db_choice_var.get() == "select"
        self.db_combobox['state'] = 'readonly' if state == 'normal' and is_select_db else 'disabled'
        is_single_model = self.model_choice_var.get() == "single"
        self.model_combobox['state'] = 'readonly' if state == 'normal' and is_single_model else 'disabled'
        is_file_source = self.id_source_var.get() == "file"
        self.id_file_entry['state'] = state if is_file_source else "disabled"
        self.id_file_browse_btn['state'] = state if is_file_source else "disabled"
        is_dir_source = self.id_source_var.get() == "dir"
        self.id_dir_entry['state'] = state if is_dir_source else "disabled"
        self.id_dir_browse_btn['state'] = state if is_dir_source else "disabled"
        for radio in [self.select_db_radio, self.single_model_radio, self.all_models_radio, self.id_file_radio, self.id_dir_radio]:
            radio['state'] = state
        for widget in [self.force_rerun_check, self.fresh_start_check, self.chunk_size_entry, self.enable_file_log_check]:
            widget['state'] = state

    def _browse_file(self):
        path = filedialog.askopenfilename(title="选择ID文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if path: self.id_file_path_var.set(path)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="选择ID文件所在目录", initialdir=Path(self.id_dir_path_var.get()).parent if self.id_dir_path_var.get() else None)
        if path: 
            self.id_dir_path_var.set(Path(path).resolve())

    def start_task(self):
        command = [sys.executable, self.script_path]
        command.extend(["--console-log-level", self.console_log_level_var.get()])
        command.extend(["--file-log-level", self.file_log_level_var.get()])
        if self.enable_file_log_var.get(): command.append("--enable-file-log")
        # 添加数据库选择
        db_name = self.db_combobox_var.get()
        if not db_name or "无" in db_name or "失败" in db_name:
            self.output_queue.put("错误: 请选择一个有效的数据库。\n"); return
        command.extend(["--db", db_name])
        if self.model_choice_var.get() == "single":
            model_name = self.model_combobox_var.get()
            if not model_name or "无" in model_name or "失败" in model_name:
                self.output_queue.put("错误: 请选择一个有效的模型。\n"); return
            command.extend(["--model", model_name])
        else:
            command.append("--all-models")
        if self.id_source_var.get() == "file":
            id_file = self.id_file_path_var.get()
            if not id_file: self.output_queue.put("错误: 请指定一个ID文件路径。\n"); return
            command.extend(["--id-file", id_file])
        else:
            id_dir = self.id_dir_path_var.get()
            if not id_dir: self.output_queue.put("错误: 请指定一个ID文件目录。\n"); return
            command.extend(["--id-dir", id_dir])
        if self.force_rerun_var.get(): command.append("--force-rerun")
        if self.fresh_start_var.get(): command.append("--fresh-start")
        chunk_size = self.chunk_size_var.get()
        if chunk_size.isdigit() and int(chunk_size) > 0:
            command.extend(["--chunk-size", chunk_size])
        else:
            self.output_queue.put(f"警告: 批次大小 '{chunk_size}' 无效，将使用脚本默认值。\n")
        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        display_command = ' '.join(f'"{str(arg)}"' if ' ' in str(arg) else str(arg) for arg in command)
        self.output_queue.put(f"执行命令: {display_command}\n" + "="*80 + "\n")
        self._update_ui_state(is_running=True)
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()

class SamplingTab(TaskExecutorTab):
    """随机抽样功能的UI选项卡。"""
    def __init__(self, master):
        super().__init__(master, "random_sample.py")
        self._create_widgets()
        super()._create_common_widgets()
        self.start_button.config(text="开始抽样")
        self.stop_button.config(text="停止抽样")
        self._update_ui_state()
        self.master.after(100, self.process_queue)
    def _create_widgets(self):
        # 数据库选择 (复用通用组件)
        db_frame = ttk.LabelFrame(self, text="数据库选择")
        db_frame.pack(fill="x", padx=5, pady=5)
        self.db_choice_var = tk.StringVar(value="select")
        # 移除了"使用默认数据库"选项，直接显示数据库选择
        self.select_db_radio = ttk.Radiobutton(db_frame, text="选择数据库", variable=self.db_choice_var, value="select", command=self._update_ui_state)
        self.select_db_radio.pack(side="left", padx=5, pady=5)
        self.db_combobox_var = tk.StringVar()
        self.db_combobox = ttk.Combobox(db_frame, textvariable=self.db_combobox_var, state="readonly", width=30)
        self.db_combobox.pack(side="left", padx=5, pady=5)
        self._populate_databases()
        
        main_options_frame = ttk.LabelFrame(self, text="基本设置")
        main_options_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(main_options_frame, text="抽样数量:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.count_var = tk.StringVar(value="100")
        self.count_entry = ttk.Entry(main_options_frame, textvariable=self.count_var, width=15)
        self.count_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.filter_missing_var = tk.BooleanVar(value=False)
        self.filter_missing_check = ttk.Checkbutton(main_options_frame, text="过滤缺虚号 (排除任何含'□'的诗词)", variable=self.filter_missing_var)
        self.filter_missing_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # 新增：排除已标注选项
        self.exclude_annotated_frame = ttk.LabelFrame(main_options_frame, text="排除已标注")
        self.exclude_annotated_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.exclude_annotated_var = tk.BooleanVar(value=False)
        self.exclude_annotated_check = ttk.Checkbutton(self.exclude_annotated_frame, text="排除已标注的诗词", variable=self.exclude_annotated_var, command=self._update_ui_state)
        self.exclude_annotated_check.pack(side="left", padx=5, pady=5)
        ttk.Label(self.exclude_annotated_frame, text="模型标识符:").pack(side="left", padx=(10, 5), pady=5)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(self.exclude_annotated_frame, textvariable=self.model_var, state="readonly", width=20)
        self.model_combobox.pack(side="left", padx=5, pady=5)
        self._populate_models()
        
        main_options_frame.columnconfigure(1, weight=1)
        self.sort_frame = ttk.LabelFrame(self, text="排序方式")
        self.sort_frame.pack(fill="x", padx=5, pady=5)
        self.sort_choice_var = tk.StringVar(value="shuffle")
        ttk.Radiobutton(self.sort_frame, text="随机排序 (默认)", variable=self.sort_choice_var, value="shuffle").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="按ID升序", variable=self.sort_choice_var, value="sort").pack(side="left", padx=10)
        ttk.Radiobutton(self.sort_frame, text="不排序", variable=self.sort_choice_var, value="no-shuffle").pack(side="left", padx=10)
        output_frame = ttk.LabelFrame(self, text="输出设置")
        output_frame.pack(fill="x", padx=5, pady=5)
        self.output_mode_var = tk.StringVar(value="dir")
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
        self.file_mode_radio = ttk.Radiobutton(output_frame, text="输出到单个文件", variable=self.output_mode_var, value="file", command=self._update_ui_state)
        self.file_mode_radio.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10,5))
        ttk.Label(output_frame, text="文件路径:").grid(row=4, column=0, padx=(25, 5), pady=5, sticky="w")
        self.output_file_var = tk.StringVar()
        self.output_file_entry = ttk.Entry(output_frame, textvariable=self.output_file_var)
        self.output_file_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.output_file_browse_btn = ttk.Button(output_frame, text="另存为...", command=self._browse_save_file)
        self.output_file_browse_btn.grid(row=4, column=2, padx=5, pady=5)
        output_frame.columnconfigure(1, weight=1)

    def _populate_models(self):
        """填充模型下拉框"""
        try:
            models = config_manager.list_model_configs()
            if models:
                # 在模型列表前添加"全部模型"选项
                all_models = ["全部模型"] + models
                self.model_combobox['values'] = all_models
                if not self.model_var.get():
                    self.model_combobox.set(all_models[0])  # 默认选择"全部模型"
            else:
                self.model_combobox.set("无可用模型")
        except Exception as e:
            self.model_combobox.set("加载失败")
            self.output_queue.put(f"错误: 加载模型配置失败: {e}\n")
            
    def _populate_databases(self):
        try:
            db_config = config_manager.get_database_config()
            if 'db_paths' in db_config:
                db_names = list(db_config['db_paths'].keys())
                if db_names:
                    self.db_combobox['values'] = db_names
                    if not self.db_combobox_var.get():
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
            self.output_queue.put(f"错误: 加载数据库配置失败: {e}\n")
            
    def _update_ui_state(self, is_running=False):
        state = "disabled" if is_running else "normal"
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"
        
        # 更新数据库选择相关控件 (复用通用逻辑)
        is_select_db = self.db_choice_var.get() == "select"
        self.db_combobox['state'] = 'readonly' if state == 'normal' and is_select_db else 'disabled'
        
        for widget in [self.count_entry, self.filter_missing_check, self.dir_mode_radio, self.file_mode_radio]: widget['state'] = state
        for child in self.sort_frame.winfo_children():
            if isinstance(child, (ttk.Radiobutton, ttk.Button, ttk.Entry)): child.configure(state=state)
        output_mode = self.output_mode_var.get()
        dir_state = state if output_mode == 'dir' else 'disabled'
        for widget in [self.output_dir_entry, self.output_dir_browse_btn, self.num_files_entry]: widget['state'] = dir_state
        file_state = state if output_mode == 'file' else 'disabled'
        for widget in [self.output_file_entry, self.output_file_browse_btn]: widget['state'] = file_state
        
        # 更新排除已标注相关控件
        self.exclude_annotated_check['state'] = state
        model_state = state if self.exclude_annotated_var.get() else 'disabled'
        self.model_combobox['state'] = 'readonly' if model_state == 'normal' else 'disabled'
        
        # 更新数据库选择的单选按钮
        for radio in [self.select_db_radio]:
            radio['state'] = state
        
    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path: self.output_dir_var.set(path)
    def _browse_save_file(self):
        path = filedialog.asksaveasfilename(title="保存到文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")], defaultextension=".txt")
        if path: self.output_file_var.set(path)
    def start_task(self):
        command = [sys.executable, self.script_path]
        
        # 添加数据库选择 (复用通用逻辑)
        db_name = self.db_combobox_var.get()
        if not db_name or "无" in db_name or "失败" in db_name:
            self.output_queue.put("错误: 请选择一个有效的数据库。\n")
            return
            
        # 获取完整的数据库路径并传递给脚本
        try:
            db_config = config_manager.get_database_config()
            if 'db_paths' in db_config and db_name in db_config['db_paths']:
                db_path = db_config['db_paths'][db_name]
            elif 'db_path' in db_config and db_name == "default":
                db_path = db_config['db_path']
            else:
                self.output_queue.put(f"错误: 无法找到数据库 '{db_name}' 的配置。\n")
                return
            # 确保使用绝对路径
            db_path = os.path.abspath(db_path)
            command.extend(["--db", db_path])
        except Exception as e:
            self.output_queue.put(f"错误: 获取数据库路径失败: {e}\n")
            return
            
        count = self.count_var.get()
        if not (count.isdigit() and int(count) > 0): self.output_queue.put(f"错误: 抽样数量 '{count}' 必须为正整数。\n"); return
        command.extend(["-n", count])
        if self.filter_missing_var.get(): command.append("--filter-missing")
        
        # 添加排除已标注的选项
        if self.exclude_annotated_var.get():
            command.append("--exclude-annotated")
            model_name = self.model_var.get()
            # 如果选择了"全部模型"，则不指定具体的模型标识符
            if model_name == "全部模型":
                pass  # 不添加 --model 参数
            elif not model_name or "无" in model_name or "失败" in model_name:
                self.output_queue.put("错误: 请选择一个有效的模型。\n")
                return
            else:
                command.extend(["--model", model_name])
        
        sort_mode = self.sort_choice_var.get()
        if sort_mode == 'sort': command.append("--sort")
        elif sort_mode == 'no-shuffle': command.append("--no-shuffle")
        if self.output_mode_var.get() == 'file':
            output_file = self.output_file_var.get()
            if not output_file: self.output_queue.put("错误: 请指定输出文件路径。\n"); return
            # 确保输出文件路径使用绝对路径
            output_file = os.path.abspath(output_file)
            command.extend(["--output-file", output_file])
        else:
            output_dir = self.output_dir_var.get()
            if output_dir: 
                # 确保输出目录路径使用绝对路径
                output_dir = os.path.abspath(output_dir)
                command.extend(["--output-dir", output_dir])
            num_files = self.num_files_var.get()
            if not (num_files.isdigit() and int(num_files) > 0): self.output_queue.put(f"错误: 分段文件数 '{num_files}' 必须为正整数。\n"); return
            command.extend(["--num-files", num_files])
        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        display_command = ' '.join(f'"{str(arg)}"' if ' ' in str(arg) else str(arg) for arg in command)
        self.output_queue.put(f"执行命令: {display_command}\n" + "="*80 + "\n")
        self._update_ui_state(is_running=True)
        self.task_thread = threading.Thread(target=self._run_task_thread, args=(command,), daemon=True)
        self.task_thread.start()

# 【新增】日志恢复功能的UI选项卡
class RecoveryTab(TaskExecutorTab):
    """从日志恢复数据的UI选项卡。"""
    def __init__(self, master):
        # 直接调用 recover_from_log_v7.py 脚本
        super().__init__(master, "recover_from_log_v7.py")
        self._create_widgets()
        super()._create_common_widgets()
        self.start_button.config(text="开始恢复")
        self.stop_button.config(text="停止恢复")
        self._update_ui_state()
        self.master.after(100, self.process_queue)

    def _create_widgets(self):
        """为恢复任务创建特定的控件。"""
        options_frame = ttk.LabelFrame(self, text="恢复选项")
        options_frame.pack(fill="x", padx=5, pady=5)

        # 日志路径输入
        ttk.Label(options_frame, text="日志文件或目录路径:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.log_path_var = tk.StringVar()
        self.log_path_entry = ttk.Entry(options_frame, textvariable=self.log_path_var, width=60)
        self.log_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # 浏览按钮的容器
        browse_buttons_frame = ttk.Frame(options_frame)
        browse_buttons_frame.grid(row=0, column=2, padx=5, pady=5)
        
        self.browse_file_btn = ttk.Button(browse_buttons_frame, text="浏览文件...", command=self._browse_file)
        self.browse_file_btn.pack(side="left", padx=(0, 2))
        
        self.browse_dir_btn = ttk.Button(browse_buttons_frame, text="浏览目录...", command=self._browse_dir)
        self.browse_dir_btn.pack(side="left")

        options_frame.columnconfigure(1, weight=1)

        # Dry Run (试运行) 选项
        self.dry_run_var = tk.BooleanVar(value=True)  # 默认勾选，更安全
        self.dry_run_check = ttk.Checkbutton(options_frame, text="试运行 (Dry Run) - 仅分析日志，不写入数据库", variable=self.dry_run_var)
        self.dry_run_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # 数据库路径输入
        ttk.Label(options_frame, text="数据库路径 (可选):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(options_frame, textvariable=self.db_path_var, width=60)
        self.db_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.browse_db_btn = ttk.Button(options_frame, text="浏览数据库...", command=self._browse_db)
        self.browse_db_btn.grid(row=2, column=2, padx=5, pady=5)

    def _browse_file(self):
        """打开文件选择对话框。"""
        path = filedialog.askopenfilename(title="选择日志文件", filetypes=[("日志文件", "*.log"), ("所有文件", "*.*")])
        if path:
            self.log_path_var.set(path)
            
    def _browse_dir(self):
        """打开目录选择对话框。"""
        path = filedialog.askdirectory(title="选择日志目录")
        if path:
            self.log_path_var.set(os.path.normpath(path))
            
    def _browse_db(self):
        """打开数据库文件选择对话框。"""
        path = filedialog.askopenfilename(title="选择数据库文件", filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")])
        if path:
            self.db_path_var.set(path)

    def _update_ui_state(self, is_running=False):
        """根据任务运行状态更新UI控件。"""
        state = "disabled" if is_running else "normal"
        self.start_button['state'] = 'disabled' if is_running else 'normal'
        self.stop_button['state'] = 'normal' if is_running else 'disabled'
        self.status_bar['text'] = "状态: 运行中..." if is_running else "状态: 空闲"

        # 更新此选项卡的特定控件状态
        for widget in [self.log_path_entry, self.browse_file_btn, self.browse_dir_btn, self.dry_run_check, 
                       self.db_path_entry, self.browse_db_btn]:
            widget['state'] = state
            
    def start_task(self):
        """开始日志恢复任务。"""
        log_path = self.log_path_var.get()
        if not log_path:
            self.output_queue.put("错误: 请指定日志文件或目录路径。\n")
            return

        # 直接调用 recover_from_log_v7.py 脚本
        command = [
            sys.executable, 
            self.script_path  # 指向 recover_from_log_v7.py
        ]
        
        # 判断是文件还是目录
        if os.path.isfile(log_path):
            command.extend(["--file", log_path])
        elif os.path.isdir(log_path):
            command.extend(["--dir", log_path])
        else:
            self.output_queue.put("错误: 指定的路径既不是文件也不是目录。\n")
            return
            
        # 添加数据库路径参数（如果提供了）
        db_path = self.db_path_var.get()
        if db_path:
            command.extend(["--db-path", db_path])
        
        # Dry run 选项 - 注意脚本默认是 dry run，需要 --write 才会实际写入
        if not self.dry_run_var.get():  # 如果用户取消了 dry run 选项
            command.append("--write")   # 则添加 --write 标志
        
        # 清空日志区域并显示执行的命令
        self.log_text.config(state="normal"); self.log_text.delete(1.0, tk.END); self.log_text.config(state="disabled")
        display_command = ' '.join(f'"{str(arg)}"' if ' ' in str(arg) else str(arg) for arg in command)
        self.output_queue.put(f"执行命令: {display_command}\n" + "="*80 + "\n")
        
        # 更新UI状态并启动线程
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

        # 【修改】保存对 DistributionTab 实例的引用
        self.dist_tab = None 
        dist_tab_script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "distribute_tasks.py")
        if os.path.exists(dist_tab_script_path):
            self.dist_tab = DistributionTab(notebook)
            notebook.add(self.dist_tab, text="  任务分发 (Distribution)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  任务分发 (脚本缺失)  ", state="disabled")

        sampling_tab_script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "random_sample.py")
        if os.path.exists(sampling_tab_script_path):
            sampling_tab = SamplingTab(notebook)
            notebook.add(sampling_tab, text="  随机抽样 (Sampling)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  随机抽样 (脚本缺失)  ", state="disabled")
            
        # 日志恢复选项卡
        # 这个功能由 main.py 提供
        recovery_tab_script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        if os.path.exists(recovery_tab_script_path):
            recovery_tab = RecoveryTab(notebook)
            notebook.add(recovery_tab, text="  日志恢复 (Recovery)  ")
        else:
            # 如果 main.py 找不到，则禁用此选项卡
            notebook.add(ttk.Frame(notebook), text="  日志恢复 (脚本缺失)  ", state="disabled")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """在关闭窗口前，保存配置。"""
        if self.dist_tab:
            try:
                self.dist_tab.save_config()
            except Exception as e:
                print(f"关闭时保存配置失败: {e}") 
        
        self.destroy()

if __name__ == "__main__":
    app = PoetryToolGUI()
    app.mainloop()