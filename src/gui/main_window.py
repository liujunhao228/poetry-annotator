#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path

# 确保Tkinter界面使用正确的编码
# 这对于Tkinter正确显示中文字符很重要
if sys.platform.startswith('win'):
    # 在Windows上设置Tkinter的默认字体，以更好地支持中文显示
    # Arial Unicode MS 是一个包含广泛字符集的字体
    os.environ['TK_DEFAULT_FONT'] = 'Arial Unicode MS'

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
# 作为模块导入时，__file__ 是当前文件的路径
# project_root = Path(__file__).parent.parent.parent.absolute()
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))
# 注意：通常入口脚本会处理路径添加，这里可以省略或保留注释作为提醒
    
# 从拆分后的模块导入
from .distribution_tab import DistributionTab
from .sampling_tab import SamplingTab
from .recovery_tab import RecoveryTab
from .annotation_review_tab import AnnotationReviewerTab


class PoetryToolGUI(tk.Tk):
    """主应用程序窗口，包含所有功能选项卡。"""
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self.title("诗词处理工具集")
        self.geometry("850x700")

        # 设置Notebook的权重以确保正确填充
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # 【修改】保存对 DistributionTab 实例的引用
        self.dist_tab = None 
        dist_tab_script_path = self.project_root / "scripts" / "distribute_tasks.py"
        if dist_tab_script_path.exists():
            self.dist_tab = DistributionTab(notebook)
            notebook.add(self.dist_tab, text="  任务分发 (Distribution)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  任务分发 (脚本缺失)  ", state="disabled")

        sampling_tab_script_path = self.project_root / "scripts" / "random_sample.py"
        if sampling_tab_script_path.exists():
            sampling_tab = SamplingTab(notebook)
            notebook.add(sampling_tab, text="  随机抽样 (Sampling)  ")
        else:
            notebook.add(ttk.Frame(notebook), text="  随机抽样 (脚本缺失)  ", state="disabled")
            
        # 日志恢复选项卡
        # 这个功能由 recover_from_log_v7.py 脚本提供
        recovery_tab_script_path = self.project_root / "scripts" / "recover_from_log_v7.py"
        if recovery_tab_script_path.exists():
            recovery_tab = RecoveryTab(notebook)
            notebook.add(recovery_tab, text="  日志恢复 (Recovery)  ")
        else:
            # 如果脚本找不到，则禁用此选项卡
            notebook.add(ttk.Frame(notebook), text="  日志恢复 (脚本缺失)  ", state="disabled")

        # 诗词标注校对选项卡
        annotation_review_tab = AnnotationReviewerTab(notebook)
        notebook.add(annotation_review_tab, text="  标注校对 (Review)  ")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """在关闭窗口前，保存配置。"""
        if self.dist_tab:
            try:
                self.dist_tab.save_config()
            except Exception as e:
                print(f"关闭时保存配置失败: {e}") 
        
        self.destroy()


def main(project_root: Path):
    """应用程序入口点函数。
    
    Args:
        project_root (Path): 项目的根目录路径。
    """
    app = PoetryToolGUI(project_root)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n应用程序被用户中断。")
        app.destroy()
    except Exception as e:
        print(f"应用程序发生未处理的错误: {e}")
        app.destroy()


if __name__ == "__main__":
    # 如果这个模块被直接运行（虽然不太可能，因为入口在scripts/gui_launcher.py）
    # 为了完整性，我们还是加上
    project_root = Path(__file__).parent.parent.parent.absolute()
    main(project_root)