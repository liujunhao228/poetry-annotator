"""随机抽样功能选项卡"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Any, Optional

from .base_tab import BaseTab
from ..components import DatabaseSelector
from ..models.config import SamplingConfig


class SamplingTab(BaseTab):
    """随机抽样功能选项卡"""
    
    def __init__(self, master: Any, config_service: Any):
        self.config_service = config_service
        self.config_file = Path('config') / 'gui_sampling.json'
        
        # 配置对象
        self.config = SamplingConfig.load(self.config_file)
        
        super().__init__(
            master=master,
            title="随机抽样",
            script_name="random_sample.py",
            config_service=config_service
        )
        
        # 修改按钮文本
        if self.start_button:
            self.start_button.config(text="开始抽样")
        if self.stop_button:
            self.stop_button.config(text="停止抽样")
        
        # 启动日志队列处理
        if self.log_panel:
            self.log_panel.start_processing()
    
    def _create_options_panel(self) -> None:
        """创建选项配置面板"""
        # 1. 数据库选择
        self._create_database_selector()
        
        # 2. 基本设置
        self._create_main_options_frame()
        
        # 3. 排序方式
        self._create_sort_frame()
        
        # 4. 输出设置
        self._create_output_frame()
        
        # 加载配置到 UI
        self._load_config_to_ui()
    
    def _create_database_selector(self) -> None:
        """创建数据库选择器"""
        self.db_selector = DatabaseSelector(
            self,
            config_manager=self.config_service.config_manager,
            label_text="数据库选择"
        )
        self.db_selector.pack(fill="x", padx=5, pady=5)
    
    def _create_main_options_frame(self) -> None:
        """创建基本设置框"""
        frame = ttk.LabelFrame(self, text="基本设置")
        frame.pack(fill="x", padx=5, pady=5)
        self.options_frame = frame
        
        # 抽样数量
        ttk.Label(frame, text="抽样数量:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.count_var = tk.StringVar(value="100")
        self.count_entry = ttk.Entry(frame, textvariable=self.count_var, width=15)
        self.count_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 过滤缺虚号
        self.filter_missing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, 
            text="过滤缺虚号 (排除任何含'□'的诗词)", 
            variable=self.filter_missing_var
        ).grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # 排除已标注
        self._create_exclude_annotated_frame(frame)
        
        frame.columnconfigure(1, weight=1)
    
    def _create_exclude_annotated_frame(self, parent: ttk.Frame) -> None:
        """创建排除已标注选项框"""
        exclude_frame = ttk.LabelFrame(parent, text="排除已标注")
        exclude_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.exclude_annotated_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            exclude_frame, 
            text="排除已标注的诗词", 
            variable=self.exclude_annotated_var,
            command=self._update_exclude_annotated_state
        ).pack(side="left", padx=5, pady=5)
        
        ttk.Label(exclude_frame, text="模型标识符:").pack(side="left", padx=(10, 5), pady=5)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(exclude_frame, textvariable=self.model_var, state="readonly", width=20)
        self.model_combobox.pack(side="left", padx=5, pady=5)
        
        self._populate_models()
        
        self.exclude_annotated_widgets = [self.model_combobox]
    
    def _populate_models(self) -> None:
        """填充模型列表"""
        try:
            models = self.config_service.list_models()
            if models:
                # 添加"全部模型"选项
                all_models = ["全部模型"] + models
                self.model_combobox['values'] = all_models
                self.model_combobox.set(all_models[0])
            else:
                self.model_combobox.set("无可用模型")
        except Exception as e:
            self.model_combobox.set("加载失败")
            self._log(f"错误：加载模型配置失败：{e}\n")
    
    def _create_sort_frame(self) -> None:
        """创建排序方式框"""
        frame = ttk.LabelFrame(self, text="排序方式")
        frame.pack(fill="x", padx=5, pady=5)
        
        self.sort_choice_var = tk.StringVar(value="shuffle")
        
        ttk.Radiobutton(
            frame, 
            text="随机排序 (默认)", 
            variable=self.sort_choice_var, 
            value="shuffle"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            frame, 
            text="按 ID 升序", 
            variable=self.sort_choice_var, 
            value="sort"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            frame, 
            text="不排序", 
            variable=self.sort_choice_var, 
            value="no-shuffle"
        ).pack(side="left", padx=10)
        
        self.sort_widgets = list(frame.winfo_children())
    
    def _create_output_frame(self) -> None:
        """创建输出设置框"""
        frame = ttk.LabelFrame(self, text="输出设置")
        frame.pack(fill="x", padx=5, pady=5)
        
        self.output_mode_var = tk.StringVar(value="dir")
        
        # 目录模式
        self.dir_mode_radio = ttk.Radiobutton(
            frame, 
            text="输出到目录", 
            variable=self.output_mode_var, 
            value="dir",
            command=self._update_output_state
        )
        self.dir_mode_radio.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="目录路径:").grid(row=1, column=0, padx=(25, 5), pady=5, sticky="w")
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.output_dir_browse_btn = ttk.Button(
            frame, 
            text="浏览...", 
            command=self._browse_output_dir
        )
        self.output_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # 分段文件数
        ttk.Label(frame, text="分段文件数:").grid(row=2, column=0, padx=(25, 5), pady=5, sticky="w")
        self.num_files_var = tk.StringVar(value="1")
        self.num_files_entry = ttk.Entry(frame, textvariable=self.num_files_var, width=15)
        self.num_files_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 文件模式
        self.file_mode_radio = ttk.Radiobutton(
            frame, 
            text="输出到单个文件", 
            variable=self.output_mode_var, 
            value="file",
            command=self._update_output_state
        )
        self.file_mode_radio.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))
        
        ttk.Label(frame, text="文件路径:").grid(row=4, column=0, padx=(25, 5), pady=5, sticky="w")
        self.output_file_var = tk.StringVar()
        self.output_file_entry = ttk.Entry(frame, textvariable=self.output_file_var, width=50)
        self.output_file_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        self.output_file_browse_btn = ttk.Button(
            frame, 
            text="另存为...", 
            command=self._browse_save_file
        )
        self.output_file_browse_btn.grid(row=4, column=2, padx=5, pady=5)
        
        frame.columnconfigure(1, weight=1)
        
        self.output_widgets = [
            self.dir_mode_radio, self.file_mode_radio,
            self.output_dir_entry, self.output_dir_browse_btn,
            self.output_file_entry, self.output_file_browse_btn,
            self.num_files_entry
        ]
    
    def _update_exclude_annotated_state(self) -> None:
        """更新排除已标注控件状态"""
        is_enabled = self.exclude_annotated_var.get()
        state = 'readonly' if is_enabled else 'disabled'
        self.model_combobox['state'] = state
    
    def _update_output_state(self) -> None:
        """更新输出控件状态"""
        is_dir_mode = self.output_mode_var.get() == "dir"
        
        dir_state = 'normal' if is_dir_mode else 'disabled'
        self.output_dir_entry['state'] = dir_state
        self.output_dir_browse_btn['state'] = dir_state
        self.num_files_entry['state'] = dir_state
        
        file_state = 'normal' if not is_dir_mode else 'disabled'
        self.output_file_entry['state'] = file_state
        self.output_file_browse_btn['state'] = file_state
    
    def _browse_output_dir(self) -> None:
        """浏览输出目录"""
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)
    
    def _browse_save_file(self) -> None:
        """浏览保存文件"""
        path = filedialog.asksaveasfilename(
            title="保存到文件", 
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")], 
            defaultextension=".txt"
        )
        if path:
            self.output_file_var.set(path)
    
    def _load_config_to_ui(self) -> None:
        """加载配置到 UI"""
        self.count_var.set(str(self.config.sample_count))
        self.filter_missing_var.set(self.config.filter_missing)
        self.exclude_annotated_var.set(self.config.exclude_annotated)
        if self.config.model_identifier:
            self.model_var.set(self.config.model_identifier)
        self.sort_choice_var.set(self.config.sort_mode)
        self.output_mode_var.set(self.config.output_mode)
        if self.config.output_dir:
            self.output_dir_var.set(self.config.output_dir)
        if self.config.output_file:
            self.output_file_var.set(self.config.output_file)
        self.num_files_var.set(str(self.config.num_files))
        
        self._update_exclude_annotated_state()
        self._update_output_state()
    
    def _save_config_from_ui(self) -> None:
        """从 UI 保存配置"""
        self.config.sample_count = int(self.count_var.get()) if self.count_var.get().isdigit() else 100
        self.config.filter_missing = self.filter_missing_var.get()
        self.config.exclude_annotated = self.exclude_annotated_var.get()
        
        model_name = self.model_var.get()
        self.config.model_identifier = "" if model_name == "全部模型" else model_name
        
        self.config.sort_mode = self.sort_choice_var.get()
        self.config.output_mode = self.output_mode_var.get()
        self.config.output_dir = self.output_dir_var.get()
        self.config.output_file = self.output_file_var.get()
        self.config.num_files = int(self.num_files_var.get()) if self.num_files_var.get().isdigit() else 1
        
        self.config.save(self.config_file)
    
    def _update_options_state(self, enabled: bool) -> None:
        """更新选项控件状态"""
        state = 'normal' if enabled else 'disabled'
        
        # 数据库选择器
        self.db_selector.set_enabled(enabled)
        
        # 基本设置
        self.count_entry['state'] = state
        self.filter_missing_var.set(self.filter_missing_var.get())  # 保持值但禁用
        
        # 排除已标注
        self.exclude_annotated_var.set(self.exclude_annotated_var.get())
        if enabled:
            self._update_exclude_annotated_state()
        else:
            self.model_combobox['state'] = 'disabled'
        
        # 排序方式
        for widget in self.sort_widgets:
            if isinstance(widget, (ttk.Radiobutton, ttk.Button, ttk.Entry)):
                widget.configure(state=state)
        
        # 输出设置
        if enabled:
            self._update_output_state()
        else:
            for widget in self.output_widgets:
                widget['state'] = 'disabled'
    
    def start_task(self) -> None:
        """开始任务"""
        # 验证数据库
        db_name = self.db_selector.get_selected_name()
        if not self.config_service.validate_database(db_name):
            self._log("错误：请选择一个有效的数据库\n")
            return
        
        # 获取数据库路径
        db_path = self.config_service.get_database_path(db_name)
        if not db_path:
            self._log("错误：无法获取数据库路径\n")
            return
        
        # 构建命令参数
        args = []
        
        # 数据库路径
        args.extend(["--db", db_path])
        
        # 抽样数量
        count = self.count_var.get()
        if not (count.isdigit() and int(count) > 0):
            self._log(f"错误：抽样数量 '{count}' 必须为正整数\n")
            return
        args.extend(["-n", count])
        
        # 过滤缺虚号
        if self.filter_missing_var.get():
            args.append("--filter-missing")
        
        # 排除已标注
        if self.exclude_annotated_var.get():
            args.append("--exclude-annotated")
            model_name = self.model_var.get()
            if model_name != "全部模型" and model_name:
                if not self.config_service.validate_model(model_name):
                    self._log("错误：请选择一个有效的模型\n")
                    return
                args.extend(["--model", model_name])
        
        # 排序方式
        sort_mode = self.sort_choice_var.get()
        if sort_mode == 'sort':
            args.append("--sort")
        elif sort_mode == 'no-shuffle':
            args.append("--no-shuffle")
        
        # 输出设置
        if self.output_mode_var.get() == 'file':
            output_file = self.output_file_var.get()
            if not output_file:
                self._log("错误：请指定输出文件路径\n")
                return
            args.extend(["--output-file", output_file])
        else:
            output_dir = self.output_dir_var.get()
            if output_dir:
                args.extend(["--output-dir", output_dir])
            
            num_files = self.num_files_var.get()
            if not (num_files.isdigit() and int(num_files) > 0):
                self._log(f"错误：分段文件数 '{num_files}' 必须为正整数\n")
                return
            args.extend(["--num-files", num_files])
        
        # 清空日志并启动任务
        self.clear_log()
        
        if self._execute_script(args):
            self._update_ui_state(is_running=True)
            self._save_config_from_ui()
    
    def on_closing(self) -> None:
        """窗口关闭前的处理"""
        self._save_config_from_ui()
