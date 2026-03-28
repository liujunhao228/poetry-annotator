#!/usr/bin/env python3
"""
LLM 诗词情感标注工具 - 主入口文件
"""

import sys
import os
from pathlib import Path
import argparse
import subprocess

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 从新包导入 CLI
from poetry_annotator.cli import cli as poetry_cli


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="LLM 诗词情感标注工具")

    # 创建子解析器
    subparsers = parser.add_subparsers(dest="command", help="可用的命令")

    # CLI 模式子命令
    cli_parser = subparsers.add_parser("cli", help="启动命令行标注工具")

    # GUI 模式子命令
    gui_parser = subparsers.add_parser("gui", help="启动图形界面模式")

    # Visualizer 模式子命令
    visualizer_parser = subparsers.add_parser("visualizer", help="启动数据可视化模式")

    # Setup 模式子命令
    setup_parser = subparsers.add_parser("setup", help="初始化或检查当前激活项目的环境")
    setup_parser.add_argument("--init-db", action="store_true", help="初始化数据库（从 JSON 文件加载数据）")
    setup_parser.add_argument("--clear-existing", action="store_true", help='清空现有数据后重新初始化')

    # 解析参数
    args, unknown = parser.parse_known_args()

    if args.command == "gui":
        # 启动 GUI 模式
        from poetry_annotator.launcher import launch_gui
        launch_gui()
    elif args.command == "visualizer":
        # 启动数据可视化模式
        from poetry_annotator.launcher import launch_visualizer
        launch_visualizer(project_root)
    elif args.command == "setup":
        # 启动 Setup 模式
        sys.argv[1:] = unknown + ["setup"]
        if args.init_db:
            sys.argv.append("--init-db")
        if args.clear_existing:
            sys.argv.append("--clear-existing")
        poetry_cli()
    else:
        # 启动 CLI 模式 (默认或显式指定 "cli")
        sys.argv[1:] = unknown
        poetry_cli()


if __name__ == '__main__':
    main()
