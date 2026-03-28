"""
GUI 应用主入口

提供 run_gui() 函数用于启动 GUI 应用。
"""

import sys
from pathlib import Path


def run_gui() -> None:
    """
    启动 GUI 应用
    
    此函数初始化并运行诗词处理工具图形界面。
    """
    # 确保项目根目录在 Python 路径中
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 导入并运行主窗口
    from .main_window import MainWindow
    
    app = MainWindow()
    app.mainloop()


def main() -> None:
    """
    命令行入口点
    
    可直接运行：python -m src.gui
    """
    run_gui()


if __name__ == "__main__":
    main()
