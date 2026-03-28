"""数据库选择器组件"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Callable, Any


class DatabaseSelector(ttk.Frame):
    """
    可复用的数据库选择组件
    
    提供数据库名称下拉选择，支持获取选中数据库的完整路径。
    """
    
    def __init__(
        self, 
        master: Any, 
        config_manager: Any,
        on_change: Optional[Callable] = None,
        label_text: str = "数据库选择"
    ):
        """
        初始化数据库选择器
        
        Args:
            master: 父容器
            config_manager: 配置管理器实例
            on_change: 选择变化时的回调函数
            label_text: 分组框标签文本
        """
        super().__init__(master)
        self.config_manager = config_manager
        self.on_change = on_change
        
        self.selected_db = tk.StringVar()
        self._db_paths: dict[str, str] = {}  # 存储数据库名称到路径的映射
        self._current_db_path: str = ""  # 当前选中数据库的路径
        
        self._create_widgets(label_text)
        self._populate_databases()
    
    def _create_widgets(self, label_text: str) -> None:
        """创建组件内的 widgets"""
        # 分组框
        frame = ttk.LabelFrame(self, text=label_text)
        frame.pack(fill="x", padx=5, pady=5)
        
        # 选择模式单选按钮
        self.select_radio = ttk.Radiobutton(
            frame, 
            text="选择数据库", 
            variable=tk.StringVar(value="select"),
            value="select"
        )
        self.select_radio.pack(side="left", padx=5, pady=5)
        
        # 数据库下拉框
        self.combobox = ttk.Combobox(
            frame, 
            textvariable=self.selected_db, 
            state="readonly", 
            width=30
        )
        self.combobox.pack(side="left", padx=5, pady=5)
        self.combobox.bind("<<ComboboxSelected>>", self._on_selection_change)
        
        # 数据库路径显示标签
        self.path_label = ttk.Label(frame, text="", foreground="gray")
        self.path_label.pack(side="left", padx=(10, 5), pady=5)
    
    def _populate_databases(self) -> None:
        """填充数据库列表"""
        try:
            db_config = self.config_manager.get_database_config()
            
            if 'db_paths' in db_config:
                # 多数据库模式
                self._db_paths = db_config['db_paths']
                db_names = list(self._db_paths.keys())
                if db_names:
                    self.combobox['values'] = db_names
                    self.combobox.set(db_names[0])
                    self._update_path_label()
                else:
                    self.combobox.set("无可用数据库")
                    
            elif 'db_path' in db_config:
                # 单数据库模式
                db_path = db_config['db_path']
                self._db_paths = {"default": db_path}
                
                # 尝试获取项目名称
                project_name = self._get_project_name()
                display_name = f"{project_name} · {db_path}"
                self.combobox['values'] = [display_name]
                self.combobox.set(display_name)
                self._current_db_path = db_path
                self._update_path_label(db_path)
            else:
                self.combobox.set("无数据库配置")
                
        except Exception as e:
            self.combobox.set("加载失败")
            print(f"错误：加载数据库配置失败：{e}")
    
    def _get_project_name(self) -> str:
        """从配置路径推断项目名称"""
        try:
            config_paths = getattr(self.config_manager, 'config_paths', [])
            for p in config_paths:
                if 'project' in p.lower() or 'projects' in p.lower():
                    parts = Path(p).parts
                    for i, part in enumerate(parts):
                        if part == 'projects' and i + 1 < len(parts):
                            return parts[i + 1]
        except:
            pass
        return "default"
    
    def _on_selection_change(self, event: Optional[tk.Event] = None) -> None:
        """处理选择变化"""
        self._update_path_label()
        if self.on_change:
            self.on_change(self.get_selected_name(), self.get_db_path())
    
    def _update_path_label(self, path: Optional[str] = None) -> None:
        """更新路径显示标签"""
        if path is None:
            path = self.get_db_path()
        self.path_label.config(text=path if path else "")
    
    def get_selected_name(self) -> str:
        """获取选中的数据库名称"""
        return self.selected_db.get()
    
    def get_db_path(self) -> str:
        """获取选中数据库的完整路径"""
        db_name = self.selected_db.get()
        
        if "无" in db_name or "失败" in db_name:
            return ""
        
        # 如果是单数据库模式显示的名称格式
        if " · " in db_name:
            return self._current_db_path
        
        # 多数据库模式
        if db_name in self._db_paths:
            return self._db_paths[db_name]
        
        # 默认情况
        if db_name == "default" and "default" in self._db_paths:
            return self._db_paths["default"]
        
        return ""
    
    def set_enabled(self, enabled: bool) -> None:
        """设置组件启用状态"""
        state = "normal" if enabled else "disabled"
        self.select_radio['state'] = state
        self.combobox['state'] = 'readonly' if enabled else 'disabled'
    
    def clear_selection(self) -> None:
        """清空选择"""
        self.selected_db.set("")
        self.path_label.config(text="")
