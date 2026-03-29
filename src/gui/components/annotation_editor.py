"""标注编辑器对话框 - Schema 驱动版本

核心特性：
1. Schema 驱动 - 根据项目类型动态生成 UI
2. 概览 + 详情双视图 - 默认显示精简概览，点击句子展开详情编辑
3. 批量操作支持 - 复制/粘贴标注，统一设置情感
4. 键盘快捷键 - 上下键切换句子，Enter 编辑，Ctrl+S 保存
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, List, Dict, Callable

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from ..styles import get_colors, get_fonts
from ..viewmodels.annotation_editor_vm import AnnotationEditorViewModel
from ..models.schema_definition import ProjectSchema
from ..components.annotation import SentenceOverviewTable
from ..components.dynamic_annotation_form import DynamicAnnotationForm


class AnnotationEditorDialog(tk.Toplevel):
    """
    标注编辑器对话框 - Schema 驱动版本

    允许用户查看和编辑诗词的标注结果。

    核心特性：
    - Schema 驱动：根据项目类型自动加载对应的标注维度
    - 概览视图：紧凑表格展示所有句子标注状态
    - 详情视图：使用动态表单编辑选中句子的所有标注字段
    - 批量操作：复制/粘贴标注，统一设置字段值
    - 键盘导航：上下键切换句子，Enter 编辑，Ctrl+S 保存
    """

    def __init__(
        self,
        parent: Any,
        title: str = "编辑标注",
        poem_data: Optional[Dict[str, Any]] = None,
        project_schema: Optional[ProjectSchema] = None,
        on_save: Optional[Callable[[int, str, List[Dict[str, Any]]], bool]] = None,
    ):
        """
        初始化标注编辑器

        Args:
            parent: 父窗口
            title: 窗口标题
            poem_data: 诗词数据（包含 annotation_result）
            project_schema: 项目 Schema 定义（可选，不传则从项目上下文加载）
            on_save: 保存回调函数，接收 (poem_id, model_identifier, annotation_result) 参数
        """
        super().__init__(parent)

        self.title(title)
        self.geometry("1000x850")
        self.minsize(900, 750)

        self.poem_data = poem_data or {}
        self.on_save = on_save
        self._colors = get_colors()
        self._fonts = get_fonts()

        # 加载或接收 Schema
        self._schema: Optional[ProjectSchema] = project_schema
        if self._schema is None:
            self._schema = self._load_project_schema()

        # 创建 ViewModel（先不加载数据）
        self._vm: Optional[AnnotationEditorViewModel] = None
        self._create_viewmodel()

        # 防止循环更新标志
        self._updating_ui = False

        # 设置窗口模态
        self.transient(parent)
        self.grab_set()

        # 居中显示
        self._center_window()

        # 创建 UI
        self._create_ui()

        # UI 创建完成后才加载数据，避免回调访问未创建的组件
        self._vm.load_poem_data(self.poem_data)
        
        # 更新诗词信息区
        self._update_poem_info()

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # 聚焦到对话框
        self.focus_set()

        # 应用主题
        from ..styles import theme
        theme.apply_theme(self)

    def _load_project_schema(self) -> Optional[ProjectSchema]:
        """从项目上下文加载 Schema"""
        try:
            # 尝试从父窗口获取 project_schema
            if hasattr(self.master, 'config_service'):
                config_service = self.master.config_service
                if config_service and hasattr(config_service, 'get_project_schema'):
                    return config_service.get_project_schema()
            
            # 如果父窗口没有，尝试从项目加载
            from src.project import Project
            # 这里需要一个方式来获取当前项目
            # 暂时返回 None，由 ViewModel 处理
        except Exception as e:
            print(f"加载 Schema 失败：{e}")
        
        return None

    def _center_window(self) -> None:
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def _create_viewmodel(self) -> None:
        """创建 ViewModel"""
        self._vm = AnnotationEditorViewModel(
            project_schema=self._schema,
            on_state_change=self._on_vm_state_change,
        )
        # 注意：不在这里加载数据，等 UI 创建完成后再加载

    def _on_vm_state_change(self) -> None:
        """ViewModel 状态变化回调 - 选择性更新，避免闪烁"""
        if self._updating_ui:
            return
        # 只更新概览和保存按钮，详情在句子选择时单独更新
        self._update_overview()
        self._update_save_button()

    def _create_ui(self) -> None:
        """创建 UI"""
        main_frame = ttkb.Frame(self)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. 诗词信息区
        self._create_poem_info_frame(main_frame)

        # 2. 概览视图
        self._create_overview_frame(main_frame)

        # 3. 详情编辑区（动态表单）
        self._create_detail_frame(main_frame)

        # 4. 批量操作栏
        self._create_batch_operation_frame(main_frame)

        # 5. 按钮区
        self._create_button_frame(main_frame)

        # 初始化显示
        self._update_overview()
        self._update_detail()

        # 绑定快捷键
        self._bind_shortcuts()

    def _create_poem_info_frame(self, parent: Any) -> None:
        """创建诗词信息区"""
        info_frame = ttk.LabelFrame(parent, text="📖 诗词信息")
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        inner = ttkb.Frame(info_frame)
        inner.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        inner.grid_columnconfigure(1, weight=1)

        # 标题栏
        title_frame = ttkb.Frame(inner)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttkb.Label(title_frame, text="标题:", width=6).grid(row=0, column=0, sticky="w")
        self.title_label = ttkb.Label(
            title_frame,
            text="",
            font=(self._fonts.FAMILY, self._fonts.SIZE_LARGE, "bold")
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=5)

        ttkb.Label(title_frame, text="作者:", width=6).grid(row=0, column=2, sticky="w")
        self.author_label = ttkb.Label(title_frame, text="", font=(self._fonts.FAMILY, self._fonts.SIZE_LARGE))
        self.author_label.grid(row=0, column=3, sticky="w", padx=5)

        # 标注模型信息
        model_frame = ttkb.Frame(inner)
        model_frame.grid(row=1, column=0, columnspan=2, sticky="w")

        ttkb.Label(model_frame, text="标注模型:", width=10).grid(row=0, column=0, sticky="w")
        self.model_label = ttkb.Label(model_frame, text="")
        self.model_label.grid(row=0, column=1, sticky="w", padx=5)

        ttkb.Label(model_frame, text="状态:", width=6).grid(row=0, column=2, sticky="w")
        self.status_label = ttkb.Label(model_frame, text="")
        self.status_label.grid(row=0, column=3, sticky="w", padx=5)

    def _create_overview_frame(self, parent: Any) -> None:
        """创建概览视图"""
        overview_frame = ttk.LabelFrame(
            parent, 
            text="📋 句子概览（点击选择，双击编辑）"
        )
        overview_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        overview_frame.grid_rowconfigure(0, weight=1)
        overview_frame.grid_columnconfigure(0, weight=1)

        # 动态生成列：ID + 句子文本 + 所有 Schema 字段
        columns = ["sentence_id", "sentence_text"]
        if self._schema:
            columns.extend(self._schema.field_ids)

        self.overview_table = SentenceOverviewTable(
            overview_frame,
            height=10,
            columns=columns,
        )
        self.overview_table.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 绑定事件
        self.overview_table.set_on_select_callback(self._on_overview_select)
        self.overview_table.set_on_double_click_callback(self._on_overview_double_click)

    def _create_detail_frame(self, parent: Any) -> None:
        """创建详情编辑区 - 使用动态表单"""
        self.detail_editor = DynamicAnnotationForm(
            parent,
            schema=self._schema,
            height=12,
            on_change=self._on_detail_change,
        )
        self.detail_editor.grid(row=2, column=0, sticky="nsew", pady=(0, 8), padx=12)

    def _create_batch_operation_frame(self, parent: Any) -> None:
        """创建批量操作栏 - Schema 驱动版本"""
        self.batch_op_bar = SchemaBatchOperationBar(
            parent,
            schema=self._schema,
        )
        self.batch_op_bar.grid(row=3, column=0, sticky="ew", pady=(0, 8), padx=12)

        # 绑定事件
        self.batch_op_bar.set_on_copy_callback(self._on_copy_annotation)
        self.batch_op_bar.set_on_paste_all_callback(self._on_paste_all_annotation)
        self.batch_op_bar.set_on_apply_to_all_callback(self._on_apply_field_value_to_all)

    def _create_button_frame(self, parent: Any) -> None:
        """创建按钮区"""
        button_frame = ttkb.Frame(parent)
        button_frame.grid(row=4, column=0, sticky="e", pady=(0, 10), padx=12)

        self.cancel_button = ttkb.Button(
            button_frame,
            text="取消 (Esc)",
            command=self._on_cancel,
            bootstyle=OUTLINE,
            width=12
        )
        self.cancel_button.pack(side="right", padx=5)

        self.save_button = ttkb.Button(
            button_frame,
            text="💾 保存 (Ctrl+S)",
            command=self._on_save,
            bootstyle=SUCCESS,
            width=12
        )
        self.save_button.pack(side="right", padx=5)

    def _bind_shortcuts(self) -> None:
        """绑定快捷键"""
        self.bind("<Control-s>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _update_poem_info(self) -> None:
        """更新诗词信息区"""
        if not self.poem_data:
            return
        
        # 更新标题
        title = self.poem_data.get("title", "")
        if hasattr(self, 'title_label'):
            self.title_label.config(text=title)
        
        # 更新作者
        author = self.poem_data.get("author", "")
        if hasattr(self, 'author_label'):
            self.author_label.config(text=author)
        
        # 更新标注模型
        model_identifier = self.poem_data.get("model_identifier", "")
        if hasattr(self, 'model_label'):
            self.model_label.config(text=model_identifier)
        
        # 更新状态
        status = self.poem_data.get("status", "unannotated")
        status_map = {
            "completed": ("✓ 已完成", "success"),
            "failed": ("✗ 已失败", "danger"),
            "unannotated": ("未标注", "secondary"),
            "processing": ("处理中", "warning"),
        }
        status_text, status_style = status_map.get(status, ("未知", "secondary"))
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status_text, bootstyle=status_style)

    def _update_overview(self) -> None:
        """更新概览视图"""
        if self._vm:
            data = self._vm.get_overview_data()
            self.overview_table.set_data(data)

    def _update_detail(self) -> None:
        """更新详情视图"""
        if self._vm:
            sentence = self._vm.get_current_sentence()
            if sentence:
                # 使用 annotations 字典设置所有字段值
                self.detail_editor.set_values(sentence.annotations)

    def _update_save_button(self) -> None:
        """更新保存按钮状态"""
        if self._vm and self._vm.is_dirty():
            self.save_button.config(text="💾 保存 *", bootstyle=WARNING)
        else:
            self.save_button.config(text="💾 保存 (Ctrl+S)", bootstyle=SUCCESS)

    # ==================== 事件处理 ====================

    def _on_overview_select(self, sentence_id: str) -> None:
        """概览表格选择变化"""
        if self._vm and not self._updating_ui:
            self._updating_ui = True
            try:
                self._vm.select_sentence(sentence_id)
                # 只在选择时更新详情视图
                self._update_detail()
            finally:
                self._updating_ui = False

    def _on_overview_double_click(self, sentence_id: str) -> None:
        """概览表格双击事件"""
        if self._vm:
            self._vm.select_sentence(sentence_id)
            # 聚焦到详情编辑区
            if hasattr(self, 'detail_editor') and self.detail_editor.winfo_exists():
                self.detail_editor.focus_set()

    def _on_detail_change(self, field_id: str, value: Any) -> None:
        """详情编辑器数据变化"""
        if not self._vm or self._updating_ui:
            return
        
        # 静默更新 ViewModel，不触发额外回调
        self._vm.set_annotation_value(field_id, value, notify=False)
        
        # 只更新保存按钮状态和概览表格中的当前行
        self._update_save_button()
        self._update_current_row_in_overview()

    def _update_current_row_in_overview(self) -> None:
        """更新概览表格中当前行的显示，避免全表刷新"""
        if not self._vm:
            return
        sentence = self._vm.get_current_sentence()
        if not sentence:
            return
        
        # 刷新整个表格（简化处理）
        self._update_overview()

    # ==================== 批量操作 ====================

    def _on_copy_annotation(self) -> Dict[str, Any]:
        """复制当前标注"""
        if self._vm:
            annotation = self._vm.copy_current_annotation()
            return annotation or {}
        return {}

    def _on_paste_all_annotation(self, annotation: Dict[str, Any]) -> int:
        """粘贴到全部句子"""
        if self._vm:
            # 保存当前选中的句子 ID
            selected_id = self._vm.get_selected_sentence_id()
            count = self._vm.paste_annotation(annotation)
            # 恢复选中状态
            if selected_id:
                self._vm.select_sentence(selected_id)
            return count
        return 0

    def _on_apply_field_value_to_all(self, field_id: str, value: Any) -> int:
        """统一设置字段值"""
        if self._vm:
            # 保存当前选中的句子 ID
            selected_id = self._vm.get_selected_sentence_id()
            count = self._vm.apply_field_value_to_all(field_id, value)
            # 恢复选中状态
            if selected_id:
                self._vm.select_sentence(selected_id)
            return count
        return 0

    # ==================== 保存/取消 ====================

    def _on_save(self) -> None:
        """处理保存操作"""
        if not self._vm:
            return

        # 验证
        errors = self._vm.validate()
        if errors:
            messagebox.showwarning(
                "验证失败",
                "以下句子标注不完整:\n\n" + "\n".join(errors[:5]) +
                ("\n..." if len(errors) > 5 else "")
            )
            return

        # 保存
        annotation_result = self._vm.get_annotation_result()
        if not annotation_result:
            messagebox.showerror("错误", "获取标注结果失败")
            return

        poem_id = self.poem_data.get("poem_id")
        model_identifier = self.poem_data.get("model_identifier")

        if not poem_id or not model_identifier:
            messagebox.showerror("错误", "缺少必要的诗词信息！")
            return

        if self.on_save:
            success = self.on_save(poem_id, model_identifier, annotation_result)
            if success:
                self._vm.mark_saved()
                messagebox.showinfo("成功", "标注已保存！")
                self.destroy()

    def _on_cancel(self) -> None:
        """处理取消操作"""
        if self._vm and self._vm.is_dirty():
            result = messagebox.askyesnocancel(
                "确认",
                "有未保存的修改，确定要取消吗？",
                icon=messagebox.WARNING
            )
            if result is False:  # No
                return
            elif result is None:  # Cancel
                return
        self.destroy()


class SchemaBatchOperationBar(ttkb.Frame):
    """
    Schema 驱动的批量操作栏
    
    根据 Schema 字段动态生成操作按钮
    """
    
    def __init__(
        self,
        master: Any,
        schema: Optional[ProjectSchema] = None,
    ):
        super().__init__(master)
        
        self._schema = schema
        self._colors = get_colors()
        self._fonts = get_fonts()
        
        # 回调
        self._on_copy_callback: Optional[Callable[[], Dict[str, Any]]] = None
        self._on_paste_all_callback: Optional[Callable[[Dict[str, Any]], int]] = None
        self._on_apply_to_all_callback: Optional[Callable[[str, Any], int]] = None
        
        # 剪贴板
        self._clipboard: Optional[Dict[str, Any]] = None
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """创建 UI"""
        container = ttk.LabelFrame(self, text="⚡ 批量操作")
        container.pack(fill="x")
        
        # 1. 复制/粘贴区
        self._create_copy_paste_section(container)
        
        # 2. 分隔线
        ttkb.Separator(self, orient="horizontal").pack(fill="x", pady=10)
        
        # 3. 统一设置区（根据 Schema 动态生成）
        self._create_apply_section(container)
    
    def _create_copy_paste_section(self, parent: Any) -> None:
        """创建复制/粘贴区域"""
        frame = ttkb.Frame(parent)
        frame.pack(fill="x", pady=5, padx=10)
        
        # 复制按钮
        self.copy_btn = ttkb.Button(
            frame,
            text="📋 复制当前标注",
            command=self._on_copy,
            bootstyle=INFO,
            width=15
        )
        self.copy_btn.pack(side="left", padx=5)
        
        # 粘贴按钮
        self.paste_btn = ttkb.Button(
            frame,
            text="📄 粘贴到全部句子",
            command=self._on_paste_all,
            bootstyle=SUCCESS,
            width=18,
            state="disabled"
        )
        self.paste_btn.pack(side="left", padx=5)
        
        # 状态标签
        self.clipboard_label = ttkb.Label(
            frame,
            text="剪贴板：空",
            bootstyle="secondary"
        )
        self.clipboard_label.pack(side="right", padx=10)
    
    def _create_apply_section(self, parent: Any) -> None:
        """创建统一设置区域 - Schema 驱动"""
        frame = ttkb.Frame(parent)
        frame.pack(fill="x", pady=5, padx=10)
        
        if not self._schema or not self._schema.fields:
            ttkb.Label(frame, text="无可用字段").pack(side="left", padx=5)
            return
        
        # 为第一个字段（通常是主要分类）创建快捷按钮
        primary_field_id = self._schema.field_ids[0] if self._schema.field_ids else None
        if primary_field_id:
            field_def = self._schema.get_field(primary_field_id)
            if field_def and field_def.field_type == "single_select":
                ttkb.Label(frame, text=f"统一设置 {field_def.name_zh}:").pack(side="left", padx=5)
                
                # 显示前 6 个选项
                for cat in field_def.categories[:6]:
                    btn = ttkb.Button(
                        frame,
                        text=cat["id"],
                        width=6,
                        command=lambda fid=primary_field_id, v=cat["id"]: self._on_apply_to_all(fid, v),
                        bootstyle=OUTLINE
                    )
                    btn.pack(side="left", padx=2)
    
    # ==================== 事件处理 ====================
    
    def _on_copy(self) -> None:
        """处理复制操作"""
        if self._on_copy_callback:
            try:
                self._clipboard = self._on_copy_callback()
                self.paste_btn.config(state="normal")
                fields_str = ", ".join(f"{k}={v}" for k, v in self._clipboard.items() if v)
                self.clipboard_label.config(
                    text=f"剪贴板：{fields_str or '空'}",
                    bootstyle="info"
                )
            except Exception as e:
                messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def _on_paste_all(self) -> None:
        """处理粘贴到全部操作"""
        if not self._clipboard:
            messagebox.showwarning("警告", "剪贴板为空，请先复制标注")
            return
        
        if self._on_paste_all_callback:
            try:
                count = self._on_paste_all_callback(self._clipboard)
                messagebox.showinfo("成功", f"已将标注粘贴到 {count} 个句子")
            except Exception as e:
                messagebox.showerror("错误", f"粘贴失败：{str(e)}")
    
    def _on_apply_to_all(self, field_id: str, value: Any) -> None:
        """处理统一设置操作"""
        if messagebox.askyesno("确认", f"确定要将所有句子的「{field_id}」设置为「{value}」吗？"):
            if self._on_apply_to_all_callback:
                try:
                    count = self._on_apply_to_all_callback(field_id, value)
                    messagebox.showinfo("成功", f"已将 {count} 个句子的 {field_id} 设置为「{value}」")
                except Exception as e:
                    messagebox.showerror("错误", f"设置失败：{str(e)}")
    
    # ==================== 回调设置 ====================
    
    def set_on_copy_callback(self, callback: Callable[[], Dict[str, Any]]) -> None:
        self._on_copy_callback = callback
    
    def set_on_paste_all_callback(self, callback: Callable[[Dict[str, Any]], int]) -> None:
        self._on_paste_all_callback = callback
    
    def set_on_apply_to_all_callback(self, callback: Callable[[str, Any], int]) -> None:
        self._on_apply_to_all_callback = callback
