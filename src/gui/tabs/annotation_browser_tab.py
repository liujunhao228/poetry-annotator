"""标注浏览选项卡"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, List, Dict
from pathlib import Path
import json

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from .base_tab import BaseTab
from ..components.poetry_table import PoetryTable
from ..components.annotation_editor import AnnotationEditorDialog
from ..components.search_filter_bar import SearchFilterBar
from ..utils.shortcuts import ContextMenu, get_shortcut_manager
from ..styles import get_colors, get_fonts


class AnnotationBrowserTab(ttkb.Frame):
    """
    标注浏览选项卡

    提供标注数据的浏览、搜索和编辑功能。
    """

    def __init__(
        self,
        master: Any,
        config_service: Any
    ):
        """
        初始化标注浏览选项卡

        Args:
            master: 父容器（Notebook）
            config_service: 配置服务实例
        """
        super().__init__(master)
        self.master = master
        self.config_service = config_service

        # 数据状态
        self._current_page = 1
        self._total_pages = 0
        self._total_items = 0
        self._current_filters: Dict[str, Any] = {}
        self._colors = get_colors()

        # 组件引用
        self.filter_bar: Optional[SearchFilterBar] = None
        self.poetry_table: Optional[PoetryTable] = None
        self.status_label: Optional[ttkb.Label] = None
        
        # 右键菜单
        self._context_menu: Optional[tk.Menu] = None

        # 获取模型列表
        self._models = self.config_service.list_models()

        # 创建 UI
        self._create_ui()
        
        # 初始化快捷键
        self._init_shortcuts()

        # 初始加载数据
        self.after(100, self._load_data)

    def _create_ui(self) -> None:
        """创建 UI"""
        self.pack(fill="both", expand=True, padx=12, pady=12)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. 搜索过滤栏
        self._create_filter_bar()

        # 2. 数据表格
        self._create_table()

        # 3. 状态栏
        self._create_status_bar()

    def _create_filter_bar(self) -> None:
        """创建搜索过滤栏"""
        self.filter_bar = SearchFilterBar(
            self,
            models=self._models,
            on_search=self._on_search
        )
        self.filter_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    def _create_table(self) -> None:
        """创建数据表格"""
        columns = ["poem_id", "title", "author", "model_identifier", "status"]

        self.poetry_table = PoetryTable(
            self,
            columns=columns,
            height=18,
            show_pagination=True
        )
        self.poetry_table.grid(row=1, column=0, sticky="nsew")

        # 绑定双击事件
        self.poetry_table.set_on_row_double_click(self._on_row_double_click)

        # 绑定分页事件
        self._bind_pagination_events()
        
        # 绑定右键菜单
        self._bind_context_menu()
        
        # 绑定键盘事件
        self._bind_keyboard_events()

    def _bind_pagination_events(self) -> None:
        """绑定分页控件事件"""
        if self.poetry_table:
            # 上一页
            self.poetry_table.prev_button.config(command=self._prev_page)
            # 下一页
            self.poetry_table.next_button.config(command=self._next_page)
            # 每页数量变化
            self.poetry_table.per_page_var.trace_add(
                "write",
                lambda *args: self._on_per_page_change()
            )

    def _bind_context_menu(self) -> None:
        """绑定右键菜单"""
        if self.poetry_table:
            self.poetry_table.tree.bind("<Button-3>", self._show_context_menu)

    def _bind_keyboard_events(self) -> None:
        """绑定键盘事件"""
        if self.poetry_table:
            self.poetry_table.tree.bind("<Return>", self._on_enter_key)
            self.poetry_table.tree.bind("<Control-c>", self._on_copy_id)
            self.poetry_table.tree.bind("<Delete>", self._on_delete_key)

    def _create_status_bar(self) -> None:
        """创建状态栏"""
        status_frame = ttkb.Frame(self, bootstyle="light")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.status_label = ttkb.Label(
            status_frame,
            text="状态：就绪",
            bootstyle="success"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # 刷新按钮
        refresh_button = ttkb.Button(
            status_frame,
            text="⟳ 刷新",
            command=self._load_data,
            bootstyle=OUTLINE,
            width=8
        )
        refresh_button.pack(side="right", padx=5)

    def _init_shortcuts(self) -> None:
        """初始化快捷键"""
        shortcut_mgr = get_shortcut_manager()
        if not shortcut_mgr._root:
            shortcut_mgr.init(self.winfo_toplevel())
        
        # 注册本选项卡的快捷键
        shortcut_mgr.register("<Control-Shift-R>", lambda e: self._load_data())

    def _on_search(self, filters: Dict[str, Any]) -> None:
        """
        处理搜索操作

        Args:
            filters: 过滤条件
        """
        self._current_filters = filters
        self._current_page = 1
        self._load_data()

    def _on_row_double_click(self, data: Dict[str, Any], iid: str) -> None:
        """
        处理行双击事件

        Args:
            data: 行数据
            iid: 行 ID
        """
        self._open_editor(data)

    def _on_enter_key(self, event=None) -> None:
        """回车键打开编辑器"""
        selection = self.poetry_table.tree.selection()
        if selection:
            iid = selection[0]
            if iid in self.poetry_table._item_map:
                self._open_editor(self.poetry_table._item_map[iid])

    def _on_copy_id(self, event=None) -> None:
        """复制选中的诗词 ID"""
        selection = self.poetry_table.tree.selection()
        if selection:
            iid = selection[0]
            if iid in self.poetry_table._item_map:
                data = self.poetry_table._item_map[iid]
                poem_id = data.get("poem_id", "")
                self.clipboard_clear()
                self.clipboard_append(str(poem_id))
                self._show_toast(f"已复制 ID: {poem_id}")

    def _on_delete_key(self, event=None) -> None:
        """删除键处理（暂不支持）"""
        messagebox.showinfo("提示", "删除功能暂不支持")

    def _show_context_menu(self, event: tk.Event) -> None:
        """显示右键菜单"""
        # 选中点击的行
        item = self.poetry_table.tree.identify_row(event.y)
        if item:
            self.poetry_table.tree.selection_set(item)
        
        # 获取选中的数据
        selection = self.poetry_table.tree.selection()
        if not selection:
            return
        
        iid = selection[0]
        if iid not in self.poetry_table._item_map:
            return
        
        data = self.poetry_table._item_map[iid]
        
        # 创建菜单
        menu = ContextMenu.create_table_context(
            self,
            on_copy_id=lambda: self._on_copy_id(),
            on_edit=lambda: self._open_editor(data),
            on_view_log=lambda: self._view_log(data),
        )
        
        ContextMenu.show(menu, event)

    def _open_editor(self, data: Dict[str, Any]) -> None:
        """
        打开标注编辑器

        Args:
            data: 诗词标注数据
        """
        # 获取项目 Schema（Schema 驱动版本）
        project_schema = self.config_service.get_project_schema()

        # 创建编辑器 - 使用 Schema 驱动版本
        editor = AnnotationEditorDialog(
            self,
            title=f"编辑标注 - ID: {data.get('poem_id')}",
            poem_data=data,
            project_schema=project_schema,
            on_save=self._on_annotation_save
        )

        # 等待窗口创建完成后再居中
        editor.wait_visibility()
        editor.deiconify()

    def _view_log(self, data: Dict[str, Any]) -> None:
        """查看日志"""
        poem_id = data.get("poem_id", "")
        messagebox.showinfo("查看日志", f"查看诗词 ID {poem_id} 的处理日志\n\n此功能开发中...")

    def _get_project_root(self) -> Path:
        """从配置服务获取项目根目录"""
        return self.config_service.get_project_root()

    def _on_annotation_save(
        self,
        poem_id: int,
        model_identifier: str,
        annotation_result: List[Dict[str, Any]]
    ) -> bool:
        """
        处理标注保存

        Args:
            poem_id: 诗词 ID
            model_identifier: 模型标识符
            annotation_result: 标注结果

        Returns:
            是否保存成功
        """
        try:
            from src.data_manager import DataManager

            # 获取项目根目录
            project_root = self._get_project_root()

            # 获取数据库路径
            db_path = self.config_service.get_database_path()

            # 获取数据路径
            data_paths = self.config_service.get_data_paths()

            # 创建 DataManager（不传 label_parser，使用默认）
            data_manager = DataManager(
                db_path=str(db_path),
                source_dir=str(data_paths['source_dir']),
                output_dir=str(data_paths['output_dir']),
            )

            # 保存标注
            success = data_manager.update_annotation_result(
                poem_id=poem_id,
                model_identifier=model_identifier,
                annotation_result=annotation_result
            )

            data_manager.close()

            if success:
                # 刷新数据
                self._load_data()
                self._show_toast("标注已保存")

            return success

        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
            return False

    def _show_toast(self, message: str) -> None:
        """显示提示消息"""
        if self.status_label:
            self.status_label.config(text=message, bootstyle="info")
            # 2 秒后恢复状态
            self.after(2000, lambda: self.status_label.config(
                text=f"状态：就绪 | 显示 {len(self.poetry_table._data) if self.poetry_table else 0} 条，共 {self._total_items} 条",
                bootstyle="success"
            ))

    def _load_data(self) -> None:
        """加载数据"""
        if self.status_label:
            self.status_label.config(text="状态：加载中...", bootstyle="warning")

        try:
            from src.data_manager import DataManager
            from src.label_parser import LabelParser

            # 获取项目根目录
            project_root = self._get_project_root()

            # 获取数据库路径
            db_path = self.config_service.get_database_path()

            # 获取过滤条件
            filters = self._current_filters
            per_page = self.poetry_table.get_per_page() if self.poetry_table else 20

            # 处理状态过滤
            status = filters.get("status")
            if status == "unannotated":
                # 未标注的需要特殊处理
                self._load_unannotated_data(filters, per_page)
                return

            # 从配置服务获取情感分类文件路径
            categories_paths = self.config_service.get_categories_paths()

            # 创建 LabelParser
            label_parser = LabelParser(
                xml_path=categories_paths.get('xml_path'),
                md_path=categories_paths.get('md_path')
            )

            # 获取数据路径
            data_paths = self.config_service.get_data_paths()

            # 创建 DataManager
            data_manager = DataManager(
                db_path=str(db_path),
                source_dir=str(data_paths['source_dir']),
                output_dir=str(data_paths['output_dir']),
                label_parser=label_parser
            )

            # 获取数据
            result = data_manager.get_annotations_with_poems(
                model_identifier=filters.get("model") if filters.get("model") else None,
                status=filters.get("status") if filters.get("status") else None,
                author=filters.get("author") if filters.get("author") else None,
                title=filters.get("title") if filters.get("title") else None,
                page=self._current_page,
                per_page=per_page
            )

            data_manager.close()

            # 更新表格
            items = result.get("items", [])
            if self.poetry_table:
                self.poetry_table.set_data(items)
                self.poetry_table.update_pagination(
                    current_page=self._current_page,
                    total_pages=result.get("pages", 0),
                    total_items=result.get("total", 0)
                )

            self._total_pages = result.get("pages", 0)
            self._total_items = result.get("total", 0)

            if self.status_label:
                self.status_label.config(
                    text=f"状态：就绪 | 显示 {len(items)} 条，共 {self._total_items} 条",
                    bootstyle="success"
                )

        except Exception as e:
            if self.status_label:
                self.status_label.config(text=f"状态：错误 - {str(e)}", bootstyle="danger")
            messagebox.showerror("错误", f"加载数据失败：{str(e)}")

    def _load_unannotated_data(self, filters: Dict[str, Any], per_page: int) -> None:
        """
        加载未标注的数据

        Args:
            filters: 过滤条件
            per_page: 每页数量
        """
        # 未标注的数据需要特殊查询
        # 这里简化处理
        if self.poetry_table:
            self.poetry_table.set_data([])
            self.poetry_table.update_pagination(
                current_page=self._current_page,
                total_pages=0,
                total_items=0
            )

        self._total_pages = 0
        self._total_items = 0

        if self.status_label:
            self.status_label.config(text="状态：就绪 | 未标注数据查询暂不支持", bootstyle="warning")

    def _prev_page(self) -> None:
        """上一页"""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()

    def _next_page(self) -> None:
        """下一页"""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_data()

    def _on_per_page_change(self) -> None:
        """每页数量变化"""
        self._current_page = 1
        self._load_data()
