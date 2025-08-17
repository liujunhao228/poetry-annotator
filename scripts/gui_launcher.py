#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 从新的模块导入主窗口类并启动GUI
try:
    from src.gui.main_window import main
    main(project_root)
except Exception as e:
    print(f"启动GUI时发生错误: {e}")
    sys.exit(1)