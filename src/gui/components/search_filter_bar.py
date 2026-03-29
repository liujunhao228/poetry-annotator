"""搜索过滤栏组件"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any, List, Dict, Callable

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..styles import get_colors, get_fonts


class SearchFilterBar(ttkb.Frame):
    """
    搜索过滤栏组件

    提供作者、标题、模型、状态等过滤条件。
    """

    def __init__(
        self,
        master: Any,
        models: Optional[List[str]] = None,
        on_search: Optional[Callable] = None
    ):
        """
        初始化搜索过滤栏

        Args:
            master: 父容器
            models: 模型列表
            on_search: 搜索回调函数，接收 (filters: Dict) 参数
        """
        super().__init__(master)

        self.models = models or []
        self.on_search = on_search

        # 存储过滤条件
        self._filters: Dict[str, Any] = {
            "id_start": "",
            "id_end": "",
            "author": "",
            "title": "",
            "model": "",
            "status": ""
        }

        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建组件"""
        # 主容器 - 卡片式布局
        from tkinter import ttk
        border_frame = ttk.LabelFrame(self, text="🔍 搜索过滤")
        border_frame.pack(fill="both", expand=True, padx=5, pady=5)
        border_frame.grid_columnconfigure(0, weight=1)
        border_frame.grid_columnconfigure(2, weight=1)
        
        # 内部容器添加间距
        main_frame = ttk.Frame(border_frame)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=1)

        # 第一行：ID 范围
        id_frame = ttkb.Frame(main_frame)
        id_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5)
        
        ttkb.Label(id_frame, text="ID 范围:", width=8, bootstyle="secondary").pack(side="left", padx=(0, 5))
        
        self.id_start_entry = ttkb.Entry(id_frame, width=10)
        self.id_start_entry.pack(side="left", padx=3)
        
        ttkb.Label(id_frame, text="-").pack(side="left", padx=3)
        
        self.id_end_entry = ttkb.Entry(id_frame, width=10)
        self.id_end_entry.pack(side="left", padx=3)

        # 第二行：作者和标题
        text_frame = ttkb.Frame(main_frame)
        text_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        text_frame.grid_columnconfigure(1, weight=1)
        text_frame.grid_columnconfigure(3, weight=1)
        
        ttkb.Label(text_frame, text="作者:", width=6, bootstyle="secondary").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.author_entry = ttkb.Entry(text_frame, width=15)
        self.author_entry.grid(row=0, column=1, padx=5, sticky="w")

        ttkb.Label(text_frame, text="标题:", width=6, bootstyle="secondary").grid(row=0, column=2, padx=(10, 5), sticky="w")
        self.title_entry = ttkb.Entry(text_frame, width=20)
        self.title_entry.grid(row=0, column=3, padx=5, sticky="ew")

        # 第三行：模型和状态
        filter_frame = ttkb.Frame(main_frame)
        filter_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)
        
        ttkb.Label(filter_frame, text="模型:", width=6, bootstyle="secondary").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.model_var = tk.StringVar()
        self.model_combo = ttkb.Combobox(
            filter_frame,
            textvariable=self.model_var,
            values=["全部"] + self.models,
            width=15,
            state="readonly"
        )
        self.model_combo.grid(row=0, column=1, padx=5, sticky="w")
        self.model_combo.set("全部")

        ttkb.Label(filter_frame, text="状态:", width=6, bootstyle="secondary").grid(row=0, column=2, padx=(10, 5), sticky="w")
        self.status_var = tk.StringVar()
        self.status_combo = ttkb.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=["全部", "已完成", "已失败", "未标注"],
            width=10,
            state="readonly"
        )
        self.status_combo.grid(row=0, column=3, padx=5, sticky="w")
        self.status_combo.set("全部")

        # 第四行：按钮
        button_frame = ttkb.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, sticky="e", pady=(10, 0))

        # 重置按钮
        self.reset_button = ttkb.Button(
            button_frame,
            text="↻ 重置",
            command=self._on_reset,
            bootstyle=OUTLINE,
            width=10
        )
        self.reset_button.pack(side="right", padx=5)

        # 搜索按钮
        self.search_button = ttkb.Button(
            button_frame,
            text="🔍 搜索",
            command=self._on_search,
            bootstyle=PRIMARY,
            width=10
        )
        self.search_button.pack(side="right", padx=5)

        # 绑定回车键搜索
        for entry in [self.id_start_entry, self.id_end_entry, self.author_entry, self.title_entry]:
            entry.bind("<Return>", lambda e: self._on_search())

    def _on_search(self) -> None:
        """处理搜索操作"""
        self._collect_filters()

        if self.on_search:
            self.on_search(self._filters.copy())

    def _on_reset(self) -> None:
        """处理重置操作"""
        # 清空输入框
        self.id_start_entry.delete(0, tk.END)
        self.id_end_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)

        # 重置下拉框
        self.model_combo.set("全部")
        self.status_combo.set("全部")

        # 重置过滤条件
        self._filters = {
            "id_start": "",
            "id_end": "",
            "author": "",
            "title": "",
            "model": "",
            "status": ""
        }

        # 触发搜索
        if self.on_search:
            self.on_search(self._filters.copy())

    def _collect_filters(self) -> None:
        """收集当前过滤条件"""
        # ID 范围
        id_start = self.id_start_entry.get().strip()
        id_end = self.id_end_entry.get().strip()

        # 文本过滤
        author = self.author_entry.get().strip()
        title = self.title_entry.get().strip()

        # 模型和状态
        model = self.model_var.get()
        if model == "全部":
            model = ""

        status = self.status_var.get()
        status_map = {"全部": "", "已完成": "completed", "已失败": "failed", "未标注": "unannotated"}
        status = status_map.get(status, "")

        self._filters = {
            "id_start": int(id_start) if id_start else None,
            "id_end": int(id_end) if id_end else None,
            "author": author,
            "title": title,
            "model": model,
            "status": status
        }

    def get_filters(self) -> Dict[str, Any]:
        """
        获取当前过滤条件

        Returns:
            过滤条件字典
        """
        self._collect_filters()
        return self._filters.copy()

    def set_filters(self, filters: Dict[str, Any]) -> None:
        """
        设置过滤条件

        Args:
            filters: 过滤条件字典
        """
        # ID 范围
        if filters.get("id_start") is not None:
            self.id_start_entry.delete(0, tk.END)
            self.id_start_entry.insert(0, str(filters["id_start"]))

        if filters.get("id_end") is not None:
            self.id_end_entry.delete(0, tk.END)
            self.id_end_entry.insert(0, str(filters["id_end"]))

        # 文本过滤
        if filters.get("author"):
            self.author_entry.delete(0, tk.END)
            self.author_entry.insert(0, filters["author"])

        if filters.get("title"):
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, filters["title"])

        # 模型
        model = filters.get("model", "")
        if model:
            self.model_combo.set(model)
        else:
            self.model_combo.set("全部")

        # 状态
        status = filters.get("status", "")
        status_map = {"": "全部", "completed": "已完成", "failed": "已失败", "unannotated": "未标注"}
        self.status_combo.set(status_map.get(status, "全部"))

    def update_models(self, models: List[str]) -> None:
        """
        更新模型列表

        Args:
            models: 新的模型列表
        """
        self.models = models
        self.model_combo.config(values=["全部"] + models)
