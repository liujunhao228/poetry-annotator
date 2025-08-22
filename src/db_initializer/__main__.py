"""
数据库初始化模块主入口文件
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db_initializer.cli import main

if __name__ == "__main__":
    main()