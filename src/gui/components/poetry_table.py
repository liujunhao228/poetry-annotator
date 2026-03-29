"""诗词表格组件"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, List, Dict, Callable

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..styles import get_colors, get_fonts


class PoetryTable(ttkb.Frame):
    """
    可复用的诗词表格组件

    使用 Treeview 展示诗词数据，支持排序、分页、行高亮等功能。
    """

    def __init__(
        self,
        master: Any,
        columns: Optional[List[str]] = None,
        display_columns: Optional[List[str]] = None,
        height: int = 15,
        show_pagination: bool = True
    ):
        """
        初始化诗词表格

        Args:
            master: 父容器
            columns: 列名列表
            display_columns: 显示的列（不含 hidden）
            height: 表格高度（行数）
            show_pagination: 是否显示分页控制
        """
        super().__init__(master)

        self.columns = columns or ["id", "title", "author", "model", "status"]
        self.display_columns = display_columns or self.columns
        self.height = height
        self.show_pagination = show_pagination

        # 数据存储
        self._data: List[Dict[str, Any]] = []
        self._item_map: Dict[str, Dict[str, Any]] = {}  # iid -> data

        # 分页状态
        self._current_page = 1
        self._total_pages = 0
        self._page_size = 20
        self._filtered_data: List[Dict[str, Any]] = []

        # 回调函数
        self._on_row_double_click: Optional[Callable] = None

        # 颜色配置
        self._colors = get_colors()

        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建组件"""
        # 表格框架 - 使用边框样式
        table_frame = ttkb.Frame(self, bootstyle="light")
        table_frame.pack(fill="both", expand=True)

        # 创建 Treeview 容器（带边框）
        container = ttk.LabelFrame(
            table_frame,
            text="数据列表"
        )
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # 创建 Treeview
        self.tree = ttk.Treeview(
            container,
            columns=self.columns,
            height=self.height,
            show="headings"
        )

        # 设置列标题和宽度
        column_widths = {
            "id": 60,
            "poem_id": 70,
            "title": 180,
            "author": 80,
            "model": 140,
            "status": 90,
            "annotation_result": 200,
        }

        for col in self.columns:
            self.tree.heading(
                col, 
                text=self._get_column_header(col), 
                command=lambda c=col: self._sort_by_column(c)
            )
            width = column_widths.get(col, 100)
            self.tree.column(col, width=width, minwidth=60, anchor="w")

        # 添加滚动条
        y_scrollbar = ttkb.Scrollbar(
            container, 
            orient="vertical", 
            command=self.tree.yview,
            bootstyle="light-round"
        )
        x_scrollbar = ttkb.Scrollbar(
            container, 
            orient="horizontal", 
            command=self.tree.xview,
            bootstyle="light-round"
        )
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        # 绑定双击事件
        self.tree.bind("<Double-1>", self._on_double_click)

        # 绑定键盘导航事件
        self.tree.bind("<Down>", self._on_key_down)
        self.tree.bind("<Up>", self._on_key_up)
        self.tree.bind("<Home>", self._on_key_home)
        self.tree.bind("<End>", self._on_key_end)
        self.tree.bind("<Return>", self._on_key_enter)
        self.tree.bind("<space>", self._on_key_space)

        # 绑定悬停效果
        self._bind_hover_effects()

        # 分页控制
        if self.show_pagination:
            self._create_pagination_control()

    def _bind_hover_effects(self) -> None:
        """绑定悬停效果"""
        # 设置行悬停高亮
        self._hover_item = None
        
        def on_enter(event):
            widget = event.widget
            item = widget.identify_row(event.y)
            if item and item != self._hover_item:
                if self._hover_item:
                    widget.item(self._hover_item, tags=())
                self._hover_item = item
                widget.item(item, tags=("hover",))
        
        def on_leave(event):
            if self._hover_item:
                event.widget.item(self._hover_item, tags=())
                self._hover_item = None
        
        self.tree.bind("<Motion>", on_enter)
        self.tree.bind("<Leave>", on_leave)

    def _on_key_down(self, event) -> None:
        """向下选择"""
        current = self.tree.focus()
        if current:
            next_item = self.tree.next(current)
            if next_item:
                self.tree.selection_set(next_item)
                self.tree.focus(next_item)
                self.tree.see(next_item)
        return "break"

    def _on_key_up(self, event) -> None:
        """向上选择"""
        current = self.tree.focus()
        if current:
            prev_item = self.tree.prev(current)
            if prev_item:
                self.tree.selection_set(prev_item)
                self.tree.focus(prev_item)
                self.tree.see(prev_item)
        return "break"

    def _on_key_home(self, event) -> None:
        """跳转到第一项"""
        items = self.tree.get_children()
        if items:
            first = items[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.tree.see(first)
        return "break"

    def _on_key_end(self, event) -> None:
        """跳转到最后一项"""
        items = self.tree.get_children()
        if items:
            last = items[-1]
            self.tree.selection_set(last)
            self.tree.focus(last)
            self.tree.see(last)
        return "break"

    def _on_key_enter(self, event) -> None:
        """回车触发双击事件"""
        self._on_double_click(event)
        return "break"

    def _on_key_space(self, event) -> None:
        """空格键触发双击事件"""
        self._on_double_click(event)
        return "break"

    def _create_pagination_control(self) -> None:
        """创建分页控制栏"""
        page_frame = ttkb.Frame(self, bootstyle="light")
        page_frame.pack(fill="x", pady=(5, 0))

        # 左侧：页码信息
        self.page_label = ttkb.Label(
            page_frame, 
            text="第 0/0 页",
            bootstyle="secondary"
        )
        self.page_label.pack(side="left", padx=5)

        # 中间：上一页/下一页按钮
        self.prev_button = ttkb.Button(
            page_frame, 
            text="◀ 上一页", 
            command=self._prev_page,
            bootstyle=OUTLINE,
            width=10
        )
        self.prev_button.pack(side="left", padx=2)

        self.next_button = ttkb.Button(
            page_frame, 
            text="下一页 ▶", 
            command=self._next_page,
            bootstyle=OUTLINE,
            width=10
        )
        self.next_button.pack(side="left", padx=2)

        # 右侧：每页数量选择
        ttkb.Label(page_frame, text="每页:", bootstyle="secondary").pack(side="left", padx=(30, 5))

        self.per_page_var = tk.StringVar(value="20")
        per_page_combo = ttkb.Combobox(
            page_frame,
            textvariable=self.per_page_var,
            values=["10", "20", "50", "100"],
            width=5,
            state="readonly"
        )
        per_page_combo.pack(side="left")
        per_page_combo.bind("<<ComboboxSelected>>", self._on_per_page_change)

        # 右侧：总记录数
        self.total_label = ttkb.Label(
            page_frame, 
            text="共 0 条",
            bootstyle="info"
        )
        self.total_label.pack(side="right", padx=5)

    def _get_column_header(self, column: str) -> str:
        """获取列标题"""
        headers = {
            "id": "ID",
            "poem_id": "诗词 ID",
            "title": "标题",
            "author": "作者",
            "model": "标注模型",
            "status": "状态",
            "annotation_result": "标注结果",
        }
        return headers.get(column, column)

    def _on_double_click(self, event: Any) -> None:
        """处理双击事件"""
        selection = self.tree.selection()
        if not selection:
            return

        iid = selection[0]
        if iid in self._item_map:
            if self._on_row_double_click:
                self._on_row_double_click(self._item_map[iid], iid)

    def _sort_by_column(self, column: str) -> None:
        """按列排序"""
        # 获取当前排序方向
        current_header = self.tree.heading(column)["text"]
        reverse = current_header.endswith(" ▼")

        # 切换排序方向
        new_header = current_header.rstrip(" ▲▼")
        new_header += " ▼" if not reverse else " ▲"

        # 设置新标题
        for col in self.columns:
            header = self.tree.heading(col)["text"]
            self.tree.heading(col, text=header.rstrip(" ▲▼"))
        self.tree.heading(column, text=new_header)

        # 排序数据
        try:
            self._data.sort(
                key=lambda x: x.get(column, ""),
                reverse=not reverse
            )
        except TypeError:
            # 不同类型无法比较，转换为字符串
            self._data.sort(
                key=lambda x: str(x.get(column, "")),
                reverse=not reverse
            )

        # 刷新显示
        self._refresh_display()

    def _refresh_display(self) -> None:
        """刷新显示（支持分页）"""
        self.tree.delete(*self.tree.get_children())
        self._item_map.clear()

        # 配置标签样式 - 斑马纹和状态高亮
        self.tree.tag_configure("odd", background=self._colors.TABLE_ROW_ALT)
        self.tree.tag_configure("hover", background=self._colors.TABLE_ROW_HOVER)
        self.tree.tag_configure("failed", background=self._colors.DANGER_LIGHT)
        self.tree.tag_configure("completed", background=self._colors.SUCCESS_LIGHT)

        # 计算当前页数据
        start_idx = (self._current_page - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, len(self._filtered_data))
        page_data = self._filtered_data[start_idx:end_idx]

        for i, item in enumerate(page_data):
            iid = f"item_{item.get('poem_id', item.get('id'))}_{item.get('model_identifier', '')}"
            values = [item.get(col, "") for col in self.columns]

            # 格式化状态显示
            status = item.get("status", "")
            if status == "completed":
                status_display = "✓ 已完成"
            elif status == "failed":
                status_display = "✗ 已失败"
            else:
                status_display = status

            # 替换状态值
            if "status" in self.columns:
                idx = self.columns.index("status")
                values[idx] = status_display

            iid = self.tree.insert("", "end", iid=iid, values=values)
            self._item_map[iid] = item

            # 根据状态设置行样式
            global_idx = start_idx + i
            if status == "failed":
                self.tree.item(iid, tags=("failed",))
            elif status == "completed":
                self.tree.item(iid, tags=("completed",))
            elif global_idx % 2 == 1:
                self.tree.item(iid, tags=("odd",))

        self._update_pagination_display()

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """
        设置表格数据

        Args:
            data: 数据列表
        """
        self._data = data.copy()
        self._filtered_data = data.copy()
        self._total_pages = (len(self._filtered_data) + self._page_size - 1) // self._page_size
        self._current_page = 1 if self._total_pages > 0 else 0
        self._refresh_display()

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """获取选中的行数据"""
        selection = self.tree.selection()
        if not selection:
            return None

        iid = selection[0]
        return self._item_map.get(iid)

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """获取所有选中的行数据"""
        selection = self.tree.selection()
        return [self._item_map[iid] for iid in selection if iid in self._item_map]

    def clear(self) -> None:
        """清空表格"""
        self._data = []
        self._item_map.clear()
        self.tree.delete(*self.tree.get_children())

        if self.show_pagination:
            self.page_label.config(text="第 0/0 页")
            self.total_label.config(text="共 0 条")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")

    def set_on_row_double_click(self, callback: Callable) -> None:
        """
        设置双击回调函数

        Args:
            callback: 回调函数，接收 (data: Dict, iid: str) 参数
        """
        self._on_row_double_click = callback

    # 分页相关方法
    def _prev_page(self) -> None:
        """上一页"""
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_display()

    def _next_page(self) -> None:
        """下一页"""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._refresh_display()

    def _on_per_page_change(self, event: Any) -> None:
        """每页数量变化"""
        try:
            self._page_size = int(self.per_page_var.get())
            self._total_pages = (len(self._filtered_data) + self._page_size - 1) // self._page_size
            self._current_page = 1
            self._refresh_display()
        except ValueError:
            pass

    def _update_pagination_display(self) -> None:
        """更新分页显示"""
        if not self.show_pagination:
            return

        total_items = len(self._filtered_data)
        self.page_label.config(text=f"第 {self._current_page}/{max(1, self._total_pages)} 页")
        self.total_label.config(text=f"共 {total_items} 条")

        self.prev_button.config(state="normal" if self._current_page > 1 else "disabled")
        self.next_button.config(state="normal" if self._current_page < self._total_pages else "disabled")

    def update_pagination(self, current_page: int, total_pages: int, total_items: int) -> None:
        """
        更新分页显示（公共方法，供外部调用）

        Args:
            current_page: 当前页码
            total_pages: 总页数
            total_items: 总记录数
        """
        if not self.show_pagination:
            return

        self._current_page = current_page
        self._total_pages = total_pages

        self.page_label.config(text=f"第 {current_page}/{max(1, total_pages)} 页")
        self.total_label.config(text=f"共 {total_items} 条")

        self.prev_button.config(state="normal" if current_page > 1 else "disabled")
        self.next_button.config(state="normal" if current_page < total_pages else "disabled")

    def get_per_page(self) -> int:
        """获取每页数量"""
        try:
            return int(self.per_page_var.get())
        except ValueError:
            return 20
