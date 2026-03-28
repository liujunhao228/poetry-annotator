"""主窗口"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import configparser
from typing import Any, Optional

from .services.config_service import ConfigService
from .tabs import DistributionTab, SamplingTab, RecoveryTab


class MainWindow(tk.Tk):
    """
    主应用程序窗口
    
    包含所有功能选项卡，管理配置管理器和全局状态。
    """
    
    def __init__(self):
        super().__init__()
        
        self.title("诗词处理工具集")
        self.geometry("850x700")
        
        # 配置管理器
        self.config_manager: Optional[Any] = None
        self.config_service: Optional[ConfigService] = None
        
        # 选项卡引用
        self.dist_tab: Optional[DistributionTab] = None
        self.sampling_tab: Optional[SamplingTab] = None
        self.recovery_tab: Optional[RecoveryTab] = None
        
        # 初始化
        self._init_config_manager()
        self._create_ui()
        
        # 窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _init_config_manager(self) -> None:
        """初始化配置管理器"""
        try:
            from src.config_manager import init_config_manager
            
            # 构建配置文件路径
            project_root = Path(__file__).parent.parent.parent
            global_config_path = project_root / "config" / "config.ini"
            
            # 从全局配置中获取激活项目
            temp_config = configparser.ConfigParser()
            temp_config.read(global_config_path, encoding='utf-8')
            
            try:
                active_project_config = temp_config.get('Project', 'active_project_config')
                project_config_path = project_root / active_project_config
                config_paths = [str(global_config_path), str(project_config_path)]
            except (configparser.NoSectionError, configparser.NoOptionError):
                # 如果找不到项目配置，只使用全局配置
                config_paths = [str(global_config_path)]
            
            # 初始化配置管理器
            self.config_manager = init_config_manager(config_paths)
            
            # 创建配置服务
            self.config_service = ConfigService(self.config_manager)
            
        except Exception as e:
            print(f"警告：初始化配置管理器失败：{e}")
            # 即使失败也创建一个空的配置管理器，避免后续代码崩溃
            try:
                from src.config_manager import init_config_manager
                project_root = Path(__file__).parent.parent.parent
                global_config_path = project_root / "config" / "config.ini"
                self.config_manager = init_config_manager([str(global_config_path)])
                self.config_service = ConfigService(self.config_manager)
            except:
                self.config_manager = None
                self.config_service = None
    
    def _create_ui(self) -> None:
        """创建 UI"""
        # 创建选项卡容器
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加任务分发选项卡
        self._add_distribution_tab(notebook)
        
        # 添加随机抽样选项卡
        self._add_sampling_tab(notebook)
        
        # 添加日志恢复选项卡
        self._add_recovery_tab(notebook)
    
    def _add_distribution_tab(self, notebook: ttk.Notebook) -> None:
        """添加任务分发选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "distribute_tasks.py"
        
        if script_path.exists() and self.config_service:
            self.dist_tab = DistributionTab(notebook, self.config_service)
            notebook.add(self.dist_tab, text="  任务分发 (Distribution)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  任务分发 (脚本缺失)  ", state="disabled")
    
    def _add_sampling_tab(self, notebook: ttk.Notebook) -> None:
        """添加随机抽样选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "random_sample.py"
        
        if script_path.exists() and self.config_service:
            self.sampling_tab = SamplingTab(notebook, self.config_service)
            notebook.add(self.sampling_tab, text="  随机抽样 (Sampling)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  随机抽样 (脚本缺失)  ", state="disabled")
    
    def _add_recovery_tab(self, notebook: ttk.Notebook) -> None:
        """添加日志恢复选项卡"""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "recover_from_log_v7.py"
        
        if script_path.exists() and self.config_service:
            self.recovery_tab = RecoveryTab(notebook, self.config_service)
            notebook.add(self.recovery_tab, text="  日志恢复 (Recovery)  ")
        else:
            # 尝试使用 v6 版本
            script_path_v6 = project_root / "scripts" / "recover_from_log_v6.py"
            if script_path_v6.exists() and self.config_service:
                # 动态修改 RecoveryTab 的脚本名
                from .tabs.recovery_tab import RecoveryTab as RecoveryTabClass
                self.recovery_tab = RecoveryTabClass(notebook, self.config_service)
                self.recovery_tab.script_name = "recover_from_log_v6.py"
                notebook.add(self.recovery_tab, text="  日志恢复 (Recovery)  ")
            else:
                notebook.add(ttk.Frame(notebook), text="  日志恢复 (脚本缺失)  ", state="disabled")
    
    def on_closing(self) -> None:
        """窗口关闭前的处理"""
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
