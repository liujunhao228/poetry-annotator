"""主窗口"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import configparser
from typing import Any, Optional

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from .services.config_service import ConfigService
from .tabs import DistributionTab, SamplingTab, RecoveryTab, AnnotationBrowserTab
from .models.config_manager import UnifiedConfigManager
from .di import Container, build_gui_container
from .styles import theme, get_colors, get_fonts, get_spacing


class MainWindow(ttkb.Window):
    """
    主应用程序窗口

    包含所有功能选项卡，管理项目上下文和配置服务。
    """

    def __init__(self):
        super().__init__(themename="litera")  # 使用 litera 主题

        self.title("诗词标注工具 - Poetry Annotator")

        # 响应式窗口尺寸 - 根据屏幕大小自适应
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 使用屏幕的 80% 宽度和 85% 高度
        width = int(screen_width * 0.80)
        height = int(screen_height * 0.85)
        
        # 居中显示
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(900, 650)  # 降低最小尺寸要求，适配笔记本屏幕

        # 项目上下文
        self.project: Optional[Any] = None
        self.config_service: Optional[ConfigService] = None

        # DI 容器和统一配置管理器
        self.container: Optional[Container] = None
        self.config_manager: Optional[UnifiedConfigManager] = None

        # 选项卡引用
        self.dist_tab: Optional[DistributionTab] = None
        self.sampling_tab: Optional[SamplingTab] = None
        self.recovery_tab: Optional[RecoveryTab] = None
        self.annotation_browser_tab: Optional[AnnotationBrowserTab] = None

        # 初始化
        self._init_project()
        self._init_di_container()
        
        # 应用主题（在创建 UI 之前）
        theme.apply_theme(self)
        
        # 创建 UI
        self._create_ui()

        # 应用保存的窗口状态
        self._apply_window_state()

        # 窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _init_project(self) -> None:
        """初始化项目上下文和配置服务"""
        try:
            from src.project import Project

            # 构建路径
            project_base = Path(__file__).parent.parent.parent
            global_config_path = project_base / "config" / "config.ini"

            # 从全局配置中获取激活的项目
            config = configparser.ConfigParser()
            config.read(str(global_config_path), encoding='utf-8')

            try:
                active_project_config = config.get('Project', 'active_project_config')
                # active_project_config 如 "projects/default_project/config.ini"
                project_name = Path(active_project_config).parent.name
            except (configparser.NoSectionError, configparser.NoOptionError):
                # 如果找不到项目配置，使用默认项目
                project_name = "default_project"

            # 创建项目上下文（复用主程序逻辑）
            self.project = Project(
                project_name=project_name,
                project_root_dir=project_base / "projects",
                global_config_path=global_config_path
            )

            # 创建配置服务（传入 Project 实例）
            self.config_service = ConfigService(self.project)

            # 设置项目日志
            self.project.setup_project_logging()

        except Exception as e:
            print(f"警告：初始化项目上下文失败：{e}")
            # 即使失败也创建一个空的配置服务，避免后续代码崩溃
            try:
                from src.config_manager import init_config_manager
                project_base = Path(__file__).parent.parent.parent
                global_config_path = project_base / "config" / "config.ini"
                config_manager = init_config_manager([str(global_config_path)])
                # 创建一个最小化的 Project 模拟对象
                class MockProject:
                    def __init__(self, config_manager, root_path):
                        self.config_manager = config_manager
                        self.root_path = root_path
                mock_project = MockProject(config_manager, project_base / "projects" / "default_project")
                self.project = mock_project
                self.config_service = ConfigService(mock_project)
            except Exception as e2:
                print(f"警告：创建模拟项目失败：{e2}")
                self.project = None
                self.config_service = None

    def _init_di_container(self) -> None:
        """初始化 DI 容器和统一配置管理器"""
        try:
            if self.project and self.config_service:
                # 构建 DI 容器
                self.container = build_gui_container(self.project, self.config_service)

                # 获取统一配置管理器
                self.config_manager = self.container.get_optional(UnifiedConfigManager)
            else:
                # 项目初始化失败时，创建最小化容器
                self.container = None
                self.config_manager = None
        except Exception as e:
            print(f"警告：初始化 DI 容器失败：{e}")
            self.container = None
            self.config_manager = None

    def _apply_window_state(self) -> None:
        """应用保存的窗口状态"""
        if self.config_manager:
            window_state = self.config_manager.window
            # 应用保存的尺寸和位置
            self.geometry(f"{window_state.width}x{window_state.height}")
            
            # 如果有保存位置信息，也应用
            if hasattr(window_state, 'x') and hasattr(window_state, 'y'):
                self.geometry(f"+{window_state.x}+{window_state.y}")

    def _save_window_state(self) -> None:
        """保存窗口状态"""
        if self.config_manager:
            # 更新窗口尺寸和位置
            self.config_manager.window.width = self.winfo_width()
            self.config_manager.window.height = self.winfo_height()
            self.config_manager.window.x = self.winfo_x()
            self.config_manager.window.y = self.winfo_y()

            # 保存配置
            self.config_manager.save()

    def _create_ui(self) -> None:
        """创建 UI"""
        # 配置主窗口网格布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 创建选项卡容器
        notebook = ttkb.Notebook(self, bootstyle=INFO)
        notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 添加任务分发选项卡
        self._add_distribution_tab(notebook)

        # 添加随机抽样选项卡
        self._add_sampling_tab(notebook)

        # 添加日志恢复选项卡
        self._add_recovery_tab(notebook)

        # 添加标注浏览选项卡
        self._add_annotation_browser_tab(notebook)
        
        # 绑定选项卡切换事件
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event) -> None:
        """选项卡切换事件处理"""
        # 可以在这里添加选项卡切换时的逻辑
        pass

    def _add_distribution_tab(self, notebook: ttkb.Notebook) -> None:
        """添加任务分发选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "distribute_tasks.py"

        if script_path.exists() and self.config_service:
            self.dist_tab = DistributionTab(
                notebook,
                self.config_service,
                self.config_manager
            )
            notebook.add(self.dist_tab, text="📤 任务分发")
        else:
            notebook.add(ttkb.Frame(notebook), text="📤 任务分发 (脚本缺失)", state="disabled")

    def _add_sampling_tab(self, notebook: ttkb.Notebook) -> None:
        """添加随机抽样选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "random_sample.py"

        if script_path.exists() and self.config_service:
            self.sampling_tab = SamplingTab(
                notebook,
                self.config_service,
                self.config_manager
            )
            notebook.add(self.sampling_tab, text="🎲 随机抽样")
        else:
            notebook.add(ttkb.Frame(notebook), text="🎲 随机抽样 (脚本缺失)", state="disabled")

    def _add_recovery_tab(self, notebook: ttkb.Notebook) -> None:
        """添加日志恢复选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "recover_from_log_v7.py"

        if script_path.exists() and self.config_service:
            self.recovery_tab = RecoveryTab(
                notebook,
                self.config_service,
                self.config_manager
            )
            notebook.add(self.recovery_tab, text="🔄 日志恢复")
        else:
            # 尝试使用 v6 版本
            script_path_v6 = project_root / "scripts" / "recover_from_log_v6.py"
            if script_path_v6.exists() and self.config_service:
                # 动态修改 RecoveryTab 的脚本名
                from .tabs.recovery_tab import RecoveryTab as RecoveryTabClass
                self.recovery_tab = RecoveryTabClass(
                    notebook,
                    self.config_service,
                    self.config_manager
                )
                self.recovery_tab.script_name = "recover_from_log_v6.py"
                notebook.add(self.recovery_tab, text="🔄 日志恢复")
            else:
                notebook.add(ttkb.Frame(notebook), text="🔄 日志恢复 (脚本缺失)", state="disabled")

    def _add_annotation_browser_tab(self, notebook: ttkb.Notebook) -> None:
        """添加标注浏览选项卡"""
        if self.config_service:
            self.annotation_browser_tab = AnnotationBrowserTab(notebook, self.config_service)
            notebook.add(self.annotation_browser_tab, text="📖 标注浏览")
        else:
            notebook.add(ttkb.Frame(notebook), text="📖 标注浏览 (配置缺失)", state="disabled")

    def on_closing(self) -> None:
        """窗口关闭前的处理"""
        # 保存窗口状态
        self._save_window_state()

        # 保存各选项卡配置
        if self.dist_tab:
            try:
                self.dist_tab.on_closing()
            except Exception as e:
                print(f"关闭时保存 Distribution 配置失败：{e}")

        if self.sampling_tab:
            try:
                self.sampling_tab.on_closing()
            except Exception as e:
                print(f"关闭时保存 Sampling 配置失败：{e}")

        if self.recovery_tab:
            try:
                self.recovery_tab.on_closing()
            except Exception as e:
                print(f"关闭时保存 Recovery 配置失败：{e}")

        self.destroy()
