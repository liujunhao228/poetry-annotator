#!/usr/bin/env python3
"""
LLM诗词情感标注工具
主入口文件
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.main import cli

if __name__ == '__main__':
    cli() 