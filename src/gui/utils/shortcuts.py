"""
全局快捷键管理器

提供全局快捷键绑定和右键菜单功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, Dict, Callable, List
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *


class ShortcutManager:
    """
    全局快捷键管理器
    
    管理应用程序级别的快捷键绑定。
    """
    
    _instance: Optional["ShortcutManager"] = None
    
    def __new__(cls) -> "ShortcutManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._shortcuts: Dict[str, Callable] = {}
        self._root: Optional[tk.Tk] = None
    
    def init(self, root: tk.Tk) -> None:
        """
        初始化快捷键管理器
        
        Args:
            root: 根窗口实例
        """
        self._root = root
        self._bind_default_shortcuts()
    
    def _bind_default_shortcuts(self) -> None:
        """绑定默认快捷键"""
        if not self._root:
            return
        
        # Ctrl+S - 保存配置
        self._root.bind("<Control-s>", self._on_save_config)
        self._root.bind("<Control-S>", self._on_save_config)
        
        # Ctrl+R - 刷新
        self._root.bind("<Control-r>", self._on_refresh)
        self._root.bind("<Control-R>", self._on_refresh)
        
        # Ctrl+F - 打开搜索
        self._root.bind("<Control-f>", self._on_find)
        self._root.bind("<Control-F>", self._on_find)
        
        # F5 - 重新加载
        self._root.bind("<F5>", self._on_reload)
        
        # Escape - 取消/关闭对话框
        self._root.bind("<Escape>", self._on_escape)
    
    def register(self, key_combination: str, callback: Callable) -> None:
        """
        注册自定义快捷键
        
        Args:
            key_combination: 快捷键组合，如 "<Control-Shift-N>"
            callback: 回调函数
        """
        if self._root:
            self._root.bind(key_combination, callback)
            self._shortcuts[key_combination] = callback
    
    def unregister(self, key_combination: str) -> None:
        """
        注销快捷键
        
        Args:
            key_combination: 快捷键组合
        """
        if self._root and key_combination in self._shortcuts:
            self._root.unbind(key_combination)
            del self._shortcuts[key_combination]
    
    # 默认快捷键处理
    def _on_save_config(self, event=None) -> None:
        """保存配置"""
        # 通知当前活动选项卡保存配置
        if self._root:
            self._root.event_generate("<<SaveConfig>>", when="tail")
    
    def _on_refresh(self, event=None) -> None:
        """刷新数据"""
        if self._root:
            self._root.event_generate("<<Refresh>>", when="tail")
    
    def _on_find(self, event=None) -> None:
        """打开搜索"""
        if self._root:
            self._root.event_generate("<<Find>>", when="tail")
    
    def _on_reload(self, event=None) -> None:
        """重新加载"""
        if self._root:
            self._root.event_generate("<<Reload>>", when="tail")
    
    def _on_escape(self, event=None) -> None:
        """取消/关闭对话框"""
        if self._root:
            self._root.event_generate("<<Escape>>", when="tail")


class ContextMenu:
    """
    右键菜单工具类
    
    提供便捷的右键菜单创建和显示功能。
    """
    
    @staticmethod
    def create(
        parent: Any,
        items: List[Dict[str, Any]]
    ) -> tk.Menu:
        """
        创建右键菜单
        
        Args:
            parent: 父组件
            items: 菜单项列表，每项包含：
                - label: 菜单项文本
                - command: 点击回调
                - separator: 是否分隔符 (bool)
                - accelerator: 快捷键提示 (可选)
                - disabled: 是否禁用 (可选)
        
        Returns:
            创建的菜单对象
        """
        menu = tk.Menu(parent, tearoff=0)
        
        for item in items:
            if item.get("separator"):
                menu.add_separator()
            else:
                label = item.get("label", "")
                command = item.get("command")
                accelerator = item.get("accelerator", "")
                disabled = item.get("disabled", False)
                
                menu_item = menu.add_command(
                    label=label,
                    command=command,
                    accelerator=accelerator
                )
                
                if disabled:
                    menu.entryconfig(menu_item, state="disabled")
        
        return menu
    
    @staticmethod
    def show(menu: tk.Menu, event: tk.Event) -> None:
        """
        显示右键菜单
        
        Args:
            menu: 菜单对象
            event: 触发事件
        """
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    @staticmethod
    def create_table_context(
        parent: Any,
        on_copy_id: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_view_log: Optional[Callable] = None,
        on_delete: Optional[Callable] = None
    ) -> tk.Menu:
        """
        创建表格右键菜单
        
        Args:
            parent: 父组件
            on_copy_id: 复制 ID 回调
            on_edit: 编辑标注回调
            on_view_log: 查看日志回调
            on_delete: 删除回调
        
        Returns:
            菜单对象
        """
        items = [
            {"label": "复制 ID", "command": on_copy_id, "accelerator": "Ctrl+C"},
            {"label": "编辑标注", "command": on_edit, "accelerator": "Enter"},
            {"separator": True},
            {"label": "查看日志", "command": on_view_log},
            {"separator": True},
            {"label": "删除", "command": on_delete, "disabled": True},
        ]
        
        return ContextMenu.create(parent, items)
    
    @staticmethod
    def create_log_context(
        parent: Any,
        on_copy: Optional[Callable] = None,
        on_clear: Optional[Callable] = None,
        on_export: Optional[Callable] = None
    ) -> tk.Menu:
        """
        创建日志区域右键菜单
        
        Args:
            parent: 父组件
            on_copy: 复制回调
            on_clear: 清空回调
            on_export: 导出回调
        
        Returns:
            菜单对象
        """
        items = [
            {"label": "复制选中内容", "command": on_copy, "accelerator": "Ctrl+C"},
            {"separator": True},
            {"label": "清空日志", "command": on_clear},
            {"label": "导出日志", "command": on_export, "accelerator": "Ctrl+E"},
        ]
        
        return ContextMenu.create(parent, items)


# 全局实例
shortcut_manager = ShortcutManager()


def get_shortcut_manager() -> ShortcutManager:
    """获取全局快捷键管理器实例"""
    return shortcut_manager
