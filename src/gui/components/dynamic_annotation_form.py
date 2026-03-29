"""动态标注表单组件 - 根据 Schema 自动生成 UI"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any, List, Dict, Callable

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..styles import get_colors, get_fonts
from ..models.schema_definition import ProjectSchema, SchemaField


class DynamicAnnotationForm(ttkb.Frame):
    """
    动态标注表单 - 根据 Schema 自动生成 UI
    
    支持字段类型：
    - single_select: 单选下拉框
    - multi_select: 多选（复选框组）
    - text: 文本输入
    - number: 数字输入
    
    使用示例:
        schema = ProjectSchema.from_project_type("social_analysis")
        form = DynamicAnnotationForm(parent, schema=schema)
        form.set_values({"relationship_action": "RA03", "emotional_strategy": "ES02"})
        form.set_on_change_callback(lambda field_id, value: print(f"{field_id} = {value}"))
    """
    
    def __init__(
        self,
        master: Any,
        schema: Optional[ProjectSchema] = None,
        on_change: Optional[Callable[[str, Any], None]] = None,
        height: int = 10,
    ):
        """
        初始化动态表单
        
        Args:
            master: 父容器
            schema: 项目 Schema 定义
            on_change: 字段值变化回调，接收 (field_id, value) 参数
            height: 表单高度（行数）
        """
        super().__init__(master)
        
        self._schema = schema
        self._on_change = on_change
        self._height = height
        
        self._colors = get_colors()
        self._fonts = get_fonts()
        
        # 字段值存储
        self._values: Dict[str, Any] = {}
        
        # 字段控件存储
        self._field_widgets: Dict[str, Dict[str, Any]] = {}
        
        # 变量存储
        self._string_vars: Dict[str, tk.StringVar] = {}
        self._boolean_vars: Dict[str, tk.BooleanVar] = {}
        self._int_vars: Dict[str, tk.IntVar] = {}
        
        # 防止循环更新
        self._updating = False
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """创建 UI"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 创建滚动容器
        self._create_scrollable_container()
    
    def _create_scrollable_container(self) -> None:
        """创建可滚动的容器"""
        container_frame = ttk.LabelFrame(self, text="📝 标注编辑")
        container_frame.grid(row=0, column=0, sticky="nsew")
        container_frame.grid_rowconfigure(0, weight=1)
        container_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas 和滚动条
        canvas = tk.Canvas(container_frame, highlightthickness=0)
        scrollbar = ttkb.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttkb.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 调整宽度
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 创建字段控件
        self._create_field_widgets()
    
    def _create_field_widgets(self) -> None:
        """根据 Schema 创建字段控件"""
        if not self._schema:
            ttkb.Label(
                self.scrollable_frame,
                text="⚠️ 未加载项目 Schema",
                bootstyle=WARNING
            ).pack(pady=20)
            return
        
        if not self._schema.fields:
            ttkb.Label(
                self.scrollable_frame,
                text="ℹ️ 该项目类型没有定义标注字段",
                bootstyle=INFO
            ).pack(pady=20)
            return
        
        # 为每个字段创建控件
        for field_id, field_def in self._schema.fields.items():
            self._create_field_widget(field_id, field_def)
    
    def _create_field_widget(self, field_id: str, field_def: SchemaField) -> None:
        """创建单个字段的控件"""
        field_frame = ttkb.Frame(self.scrollable_frame)
        field_frame.pack(fill="x", pady=8, padx=12)
        
        # 字段标签
        label_frame = ttkb.Frame(field_frame)
        label_frame.pack(fill="x", pady=(0, 5))
        
        ttkb.Label(
            label_frame,
            text=f"{field_def.name_zh}:",
            font=(self._fonts.FAMILY, self._fonts.SIZE_NORMAL, "bold"),
            width=15
        ).pack(side="left")
        
        # 字段描述（如果有）
        if field_def.description:
            ttkb.Label(
                label_frame,
                text=field_def.description,
                font=(self._fonts.FAMILY, self._fonts.SIZE_SMALL),
                bootstyle="secondary"
            ).pack(side="left", padx=10)
        
        # 根据字段类型创建控件
        if field_def.field_type == "single_select":
            self._create_single_select(field_id, field_def, field_frame)
        elif field_def.field_type == "multi_select":
            self._create_multi_select(field_id, field_def, field_frame)
        elif field_def.field_type == "text":
            self._create_text_input(field_id, field_def, field_frame)
        elif field_def.field_type == "number":
            self._create_number_input(field_id, field_def, field_frame)
        else:
            # 默认使用单选
            self._create_single_select(field_id, field_def, field_frame)
    
    def _create_single_select(
        self, 
        field_id: str, 
        field_def: SchemaField, 
        parent: Any
    ) -> None:
        """创建单选下拉框"""
        var = tk.StringVar()
        self._string_vars[field_id] = var
        
        options = [cat["id"] for cat in field_def.categories]
        combo = ttkb.Combobox(
            parent,
            textvariable=var,
            values=options,
            width=25,
            state="readonly",
            font=(self._fonts.FAMILY, self._fonts.SIZE_NORMAL)
        )
        combo.pack(side="left", fill="x", expand=True)
        
        # 绑定事件
        def on_change(*args):
            if not self._updating:
                self._values[field_id] = var.get()
                if self._on_change:
                    self._on_change(field_id, var.get())
        
        var.trace_add("write", on_change)
        
        self._field_widgets[field_id] = {
            "type": "single_select",
            "widget": combo,
            "var": var,
        }
    
    def _create_multi_select(
        self, 
        field_id: str, 
        field_def: SchemaField, 
        parent: Any
    ) -> None:
        """创建多选复选框组"""
        container = ttkb.Frame(parent)
        container.pack(fill="x")
        
        self._boolean_vars[field_id] = {}
        values = []
        
        # 创建复选框（每行 4 个）
        row_frame = None
        for i, category in enumerate(field_def.categories):
            if i % 4 == 0:
                row_frame = ttkb.Frame(container)
                row_frame.pack(fill="x", pady=2)
            
            var = tk.BooleanVar(value=False)
            cat_id = category["id"]
            self._boolean_vars[field_id][cat_id] = var
            
            cb = ttkb.Checkbutton(
                row_frame,
                text=f"{cat_id} ({category.get('name_zh', '')})",
                variable=var,
                width=20,
                command=lambda fid=field_id: self._on_multi_change(fid)
            )
            cb.pack(side="left", padx=5)
        
        self._field_widgets[field_id] = {
            "type": "multi_select",
            "widget": container,
            "categories": field_def.categories,
        }
    
    def _create_text_input(
        self, 
        field_id: str, 
        field_def: SchemaField, 
        parent: Any
    ) -> None:
        """创建文本输入框"""
        var = tk.StringVar()
        self._string_vars[field_id] = var
        
        entry = ttkb.Entry(
            parent,
            textvariable=var,
            width=30,
            font=(self._fonts.FAMILY, self._fonts.SIZE_NORMAL)
        )
        entry.pack(side="left", fill="x", expand=True)
        
        # 绑定事件
        def on_change(*args):
            if not self._updating:
                self._values[field_id] = var.get()
                if self._on_change:
                    self._on_change(field_id, var.get())
        
        var.trace_add("write", on_change)
        
        self._field_widgets[field_id] = {
            "type": "text",
            "widget": entry,
            "var": var,
        }
    
    def _create_number_input(
        self, 
        field_id: str, 
        field_def: SchemaField, 
        parent: Any
    ) -> None:
        """创建数字输入框"""
        var = tk.IntVar()
        self._int_vars[field_id] = var
        
        spinbox = ttkb.Spinbox(
            parent,
            from_=0,
            to=999,
            textvariable=var,
            width=10,
            font=(self._fonts.FAMILY, self._fonts.SIZE_NORMAL)
        )
        spinbox.pack(side="left")
        
        # 绑定事件
        def on_change(*args):
            if not self._updating:
                self._values[field_id] = var.get()
                if self._on_change:
                    self._on_change(field_id, var.get())
        
        var.trace_add("write", on_change)
        
        self._field_widgets[field_id] = {
            "type": "number",
            "widget": spinbox,
            "var": var,
        }
    
    def _on_multi_change(self, field_id: str) -> None:
        """处理多选值变化"""
        if not self._updating:
            values = []
            for cat_id, var in self._boolean_vars.get(field_id, {}).items():
                if var.get():
                    values.append(cat_id)
            
            self._values[field_id] = values
            
            if self._on_change:
                self._on_change(field_id, values)
    
    # ==================== 数据方法 ====================
    
    def set_values(self, values: Dict[str, Any]) -> None:
        """
        批量设置字段值
        
        Args:
            values: 字段值字典 {field_id: value}
        """
        self._updating = True
        try:
            for field_id, value in values.items():
                self.set_value(field_id, value, notify=False)
        finally:
            self._updating = False
    
    def set_value(self, field_id: str, value: Any, notify: bool = True) -> bool:
        """
        设置单个字段值
        
        Args:
            field_id: 字段 ID
            value: 字段值
            notify: 是否触发回调
            
        Returns:
            是否成功设置
        """
        widget_info = self._field_widgets.get(field_id)
        if not widget_info:
            return False
        
        widget_type = widget_info["type"]
        
        self._updating = True
        try:
            if widget_type == "single_select":
                var = self._string_vars.get(field_id)
                if var:
                    var.set(value or "")
                    self._values[field_id] = value
                    
            elif widget_type == "multi_select":
                # value 应该是列表
                if not isinstance(value, list):
                    value = [value] if value else []
                
                bool_vars = self._boolean_vars.get(field_id, {})
                for cat_id, var in bool_vars.items():
                    var.set(cat_id in value)
                self._values[field_id] = value
                
            elif widget_type == "text":
                var = self._string_vars.get(field_id)
                if var:
                    var.set(value or "")
                    self._values[field_id] = value
                    
            elif widget_type == "number":
                var = self._int_vars.get(field_id)
                if var:
                    try:
                        var.set(int(value) if value is not None else 0)
                        self._values[field_id] = var.get()
                    except (ValueError, TypeError):
                        var.set(0)
                        self._values[field_id] = 0
        finally:
            self._updating = False
        
        if notify and self._on_change:
            self._on_change(field_id, value)
        
        return True
    
    def get_value(self, field_id: str) -> Any:
        """获取字段值"""
        widget_info = self._field_widgets.get(field_id)
        if not widget_info:
            return None
        
        widget_type = widget_info["type"]
        
        if widget_type == "single_select":
            var = self._string_vars.get(field_id)
            return var.get() if var else None
        
        elif widget_type == "multi_select":
            values = []
            for cat_id, var in self._boolean_vars.get(field_id, {}).items():
                if var.get():
                    values.append(cat_id)
            return values
        
        elif widget_type == "text":
            var = self._string_vars.get(field_id)
            return var.get() if var else None
        
        elif widget_type == "number":
            var = self._int_vars.get(field_id)
            return var.get() if var else 0
        
        return None
    
    def get_all_values(self) -> Dict[str, Any]:
        """获取所有字段值"""
        values = {}
        for field_id in self._field_widgets.keys():
            values[field_id] = self.get_value(field_id)
        return values
    
    def clear(self) -> None:
        """清空所有字段"""
        self._updating = True
        try:
            for field_id in self._field_widgets.keys():
                widget_type = self._field_widgets[field_id]["type"]
                
                if widget_type == "single_select":
                    var = self._string_vars.get(field_id)
                    if var:
                        var.set("")
                elif widget_type == "multi_select":
                    for var in self._boolean_vars.get(field_id, {}).values():
                        var.set(False)
                elif widget_type == "text":
                    var = self._string_vars.get(field_id)
                    if var:
                        var.set("")
                elif widget_type == "number":
                    var = self._int_vars.get(field_id)
                    if var:
                        var.set(0)
                
                self._values[field_id] = None
        finally:
            self._updating = False
    
    def set_schema(self, schema: ProjectSchema) -> None:
        """
        动态设置 Schema（重新创建表单）
        
        Args:
            schema: 项目 Schema 定义
        """
        self._schema = schema
        
        # 清空现有控件
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self._field_widgets.clear()
        self._string_vars.clear()
        self._boolean_vars.clear()
        self._int_vars.clear()
        self._values.clear()
        
        # 重新创建
        self._create_field_widgets()
    
    def set_on_change_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置字段值变化回调"""
        self._on_change = callback
    
    def enable_field(self, field_id: str) -> None:
        """启用字段"""
        widget_info = self._field_widgets.get(field_id)
        if widget_info:
            widget = widget_info.get("widget")
            if widget and hasattr(widget, "config"):
                widget.config(state="normal")
    
    def disable_field(self, field_id: str) -> None:
        """禁用字段"""
        widget_info = self._field_widgets.get(field_id)
        if widget_info:
            widget = widget_info.get("widget")
            if widget and hasattr(widget, "config"):
                widget.config(state="disabled")
