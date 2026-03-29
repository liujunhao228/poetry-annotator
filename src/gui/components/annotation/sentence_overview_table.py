"""句子概览表格组件 - 双视图模式的概览部分"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any, List, Dict, Callable

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ...styles import get_colors, get_fonts


class SentenceOverviewTable(ttkb.Frame):
    """
    句子概览表格组件
    
    以紧凑的表格形式展示所有句子的标注状态，支持：
    - 键盘上下键选择
    - 双击进入编辑
    - 选中行高亮
    - 状态标签展示
    
    使用示例:
        table = SentenceOverviewTable(parent)
        table.set_data([
            {"sentence_id": "S1", "sentence_text": "白日依山尽", 
             "primary_emotion": "喜", "secondary_emotions_display": "壮阔，豪迈"},
        ])
        table.set_on_select_callback(lambda iid: print(f"选中：{iid}"))
        table.set_on_double_click_callback(lambda iid: print(f"双击：{iid}"))
    """
    
    def __init__(
        self,
        master: Any,
        height: int = 8,
        columns: Optional[List[str]] = None,
    ):
        """
        初始化概览表格

        Args:
            master: 父容器
            height: 表格高度（行数）
            columns: 列名列表（可选，默认使用传统列）
        """
        super().__init__(master)

        self._height = height
        # 支持动态列
        self._columns = columns or ["sentence_id", "sentence_text", "relationship_action", "emotional_strategy"]
        self._data: List[Dict[str, Any]] = []
        self._item_map: Dict[str, Dict[str, Any]] = {}  # iid -> data
        self._selected_iid: Optional[str] = None

        self._colors = get_colors()
        self._fonts = get_fonts()

        # 回调
        self._on_select_callback: Optional[Callable[[str], None]] = None
        self._on_double_click_callback: Optional[Callable[[str], None]] = None

        self._create_widgets()
        self._bind_events()

    def _create_widgets(self) -> None:
        """创建组件"""
        # 创建 Treeview（不再嵌套 LabelFrame，避免双重边框）
        self.tree = ttk.Treeview(
            self,
            columns=self._columns,
            height=self._height,
            show="headings",
            selectmode="browse",
        )

        # 设置列 - 动态生成
        column_settings = {
            "sentence_id": {"text": "ID", "width": 50, "anchor": "center"},
            "sentence_text": {"text": "句子", "width": 250, "anchor": "w"},
            "relationship_action": {"text": "关系行为", "width": 80, "anchor": "center"},
            "emotional_strategy": {"text": "情感策略", "width": 80, "anchor": "center"},
            "communication_scene": {"text": "传播场景", "width": 80, "anchor": "center"},
            "risk_level": {"text": "风险等级", "width": 80, "anchor": "center"},
        }
        
        for col in self._columns:
            settings = column_settings.get(col, {"text": col, "width": 80, "anchor": "center"})
            self.tree.heading(col, text=settings["text"])
            self.tree.column(col, width=settings["width"], anchor=settings["anchor"], minwidth=60)

        # 滚动条
        y_scrollbar = ttkb.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="light-round"
        )
        self.tree.configure(yscrollcommand=y_scrollbar.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")

        # 配置行列权重
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 配置标签样式
        self._configure_tags()
    
    def _configure_tags(self) -> None:
        """配置标签样式"""
        self.tree.tag_configure("selected", background=self._colors.TABLE_SELECTED)
        self.tree.tag_configure("odd", background=self._colors.TABLE_ROW_ALT)
        self.tree.tag_configure("hover", background=self._colors.TABLE_ROW_HOVER)
        self.tree.tag_configure("annotated", foreground=self._colors.SUCCESS)
        self.tree.tag_configure("unannotated", foreground=self._colors.TEXT_DISABLED)
    
    def _bind_events(self) -> None:
        """绑定事件"""
        # 双击事件
        self.tree.bind("<Double-1>", self._on_double_click)

        # 鼠标点击选择
        self.tree.bind("<Button-1>", self._on_mouse_click)

        # 键盘导航
        self.tree.bind("<Down>", self._on_key_down)
        self.tree.bind("<Up>", self._on_key_up)
        self.tree.bind("<Return>", self._on_key_enter)
        self.tree.bind("<space>", self._on_key_space)

        # 悬停效果
        self._bind_hover()
        # 注意：不绑定 <<TreeviewSelect>> 事件，由外部通过回调控制
        # 这样可以避免键盘导航时频繁触发回调

    def _on_mouse_click(self, event: tk.Event) -> None:
        """处理鼠标点击事件"""
        # 延迟触发，让 Treeview 先完成选择
        self.after(10, self._on_click_delayed)

    def _on_click_delayed(self) -> None:
        """延迟执行的点击处理"""
        selection = self.tree.selection()
        if selection:
            iid = selection[0]
            self._trigger_select_callback(iid)
    
    def _bind_hover(self) -> None:
        """绑定悬停效果"""
        self._hover_item = None
        
        def on_motion(event):
            widget = event.widget
            item = widget.identify_row(event.y)
            if item and item != self._hover_item:
                if self._hover_item:
                    widget.item(self._hover_item, tags=self._get_tags_for_item(self._hover_item))
                self._hover_item = item
                widget.item(item, tags=("hover",))
        
        def on_leave(event):
            if self._hover_item:
                event.widget.item(self._hover_item, tags=self._get_tags_for_item(self._hover_item))
                self._hover_item = None
        
        self.tree.bind("<Motion>", on_motion)
        self.tree.bind("<Leave>", on_leave)

    def _trigger_select_callback(self, iid: str) -> None:
        """触发选择回调（内部方法）"""
        self._selected_iid = iid
        self._refresh_styles()
        if self._on_select_callback:
            self._on_select_callback(iid)

    def _get_tags_for_item(self, iid: str) -> tuple:
        """获取项目的标签 - 注意顺序：后面的标签优先级更高"""
        tags = []

        # 斑马纹（最低优先级）
        idx = self.tree.index(iid)
        if idx % 2 == 1:
            tags.append("odd")

        # 标注状态
        data = self._item_map.get(iid, {})
        if data.get("relationship_action") and data["relationship_action"] != "-":
            tags.append("annotated")
        else:
            tags.append("unannotated")

        # 选中状态（最高优先级，最后应用）
        if iid == self._selected_iid:
            tags.append("selected")

        return tuple(tags)

    def _on_double_click(self, event: tk.Event) -> None:
        """处理双击事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        iid = selection[0]
        if self._on_double_click_callback:
            self._on_double_click_callback(iid)
    
    def _on_key_down(self, event: tk.Event) -> None:
        """向下选择"""
        current = self.tree.focus()
        if current:
            next_item = self.tree.next(current)
            if next_item:
                self.tree.selection_set(next_item)
                self.tree.focus(next_item)
                self.tree.see(next_item)
                self._trigger_select_callback(next_item)
        return "break"

    def _on_key_up(self, event: tk.Event) -> None:
        """向上选择"""
        current = self.tree.focus()
        if current:
            prev_item = self.tree.prev(current)
            if prev_item:
                self.tree.selection_set(prev_item)
                self.tree.focus(prev_item)
                self.tree.see(prev_item)
                self._trigger_select_callback(prev_item)
        return "break"
    
    def _on_key_enter(self, event: tk.Event) -> None:
        """回车触发双击事件"""
        self._on_double_click(event)
        return "break"
    
    def _on_key_space(self, event: tk.Event) -> None:
        """空格触发双击事件"""
        self._on_double_click(event)
        return "break"
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """
        设置表格数据

        Args:
            data: 数据列表，每个元素包含 sentence_id, sentence_text,
                  以及所有 Schema 字段的值
        """
        self._data = data.copy()
        self._item_map.clear()
        self.tree.delete(*self.tree.get_children())

        for i, item in enumerate(data):
            iid = item.get("sentence_id", f"item_{i}")
            # 动态生成 values，按照 columns 顺序
            values = [item.get(col, "-") or "-" for col in self._columns]

            self.tree.insert("", "end", iid=iid, values=values)
            self._item_map[iid] = item

        # 选中指定的行
        selected_id = next((item.get("sentence_id") for item in data if item.get("is_selected")), None)
        if selected_id and selected_id in self._item_map:
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)
            self.tree.see(selected_id)

        self._refresh_styles()
    
    def _refresh_styles(self) -> None:
        """刷新样式"""
        for iid in self.tree.get_children():
            tags = self._get_tags_for_item(iid)
            self.tree.item(iid, tags=tags)
    
    def select_sentence(self, sentence_id: str) -> bool:
        """
        选择指定句子
        
        Args:
            sentence_id: 句子 ID
            
        Returns:
            是否成功选择
        """
        if sentence_id not in self._item_map:
            return False
        
        self.tree.selection_set(sentence_id)
        self.tree.focus(sentence_id)
        self.tree.see(sentence_id)
        return True
    
    def get_selected_sentence_id(self) -> Optional[str]:
        """获取当前选中的句子 ID"""
        selection = self.tree.selection()
        if not selection:
            return None
        return selection[0]
    
    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        """获取当前选中的行数据"""
        iid = self.get_selected_sentence_id()
        if not iid:
            return None
        return self._item_map.get(iid)
    
    def set_on_select_callback(self, callback: Callable[[str], None]) -> None:
        """设置选择变化回调"""
        self._on_select_callback = callback
    
    def set_on_double_click_callback(self, callback: Callable[[str], None]) -> None:
        """设置双击回调"""
        self._on_double_click_callback = callback
    
    def clear(self) -> None:
        """清空表格"""
        self._data = []
        self._item_map.clear()
        self.tree.delete(*self.tree.get_children())
        self._selected_iid = None
