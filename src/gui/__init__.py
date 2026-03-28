"""
GUI 模块 - 诗词处理工具图形界面

提供任务分发、随机抽样、日志恢复等功能的图形化操作界面。

使用示例:
    from src.gui import run_gui
    run_gui()

或者在命令行运行:
    python -m src.gui
"""

from .app import run_gui, main

__all__ = ["run_gui", "main"]
