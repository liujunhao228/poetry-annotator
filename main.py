#!/usr/bin/env python3
"""
LLM诗词情感标注工具
主入口文件
"""

import sys
import os
from pathlib import Path
import argparse

# 添加项目根目录到Python路径，确保能正确导入src下的模块
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 使用绝对导入方式
from src.main import cli

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="LLM诗词情感标注工具")
    parser.add_argument(
        "--mode",
        choices=["cli", "gui", "gui-review", "visualizer"],
        default="cli",
        help="启动模式: cli(命令行模式)、gui(功能工具集GUI模式)、gui-review(标注校对GUI模式) 或 visualizer(数据可视化模式) (默认: cli)"
    )
    
    # 解析参数
    args, unknown = parser.parse_known_args()
    
    if args.mode == "gui":
        # 启动GUI模式 (使用scripts/gui_launcher.py)
        gui_script_path = Path(__file__).parent / "scripts" / "gui_launcher.py"
        if gui_script_path.exists():
            # 直接运行GUI脚本
            os.system(f"{sys.executable} {gui_script_path}")
        else:
            print("错误: 找不到GUI启动器脚本 (scripts/gui_launcher.py)")
            sys.exit(1)
    elif args.mode == "gui-review":
        # 启动标注校对GUI模式 (使用src/gui.py)
        try:
            # 直接导入并运行标注校对GUI模块
            from src.gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"错误: 无法导入标注校对GUI模块 - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"错误: 启动标注校对GUI模式时出现问题 - {e}")
            sys.exit(1)
    elif args.mode == "visualizer":
        # 启动数据可视化模式
        # 设置数据可视化模块路径
        visualizer_path = project_root / "poetry-annotator-data-visualizer"
        if str(visualizer_path) not in sys.path:
            sys.path.insert(0, str(visualizer_path))
        
        # 检查是否安装了streamlit
        try:
            import streamlit
        except ImportError:
            print("错误: 未安装streamlit。请运行 'pip install streamlit' 后重试。")
            sys.exit(1)
            
        # 在启动可视化之前，先运行数据迁移脚本
        db_setup_script_path = visualizer_path / "data_visualizer" / "db_setup.py"
        if db_setup_script_path.exists():
            print("正在更新标注结果数据库...")
            # 使用subprocess运行数据迁移脚本，确保它在正确的环境中执行
            import subprocess
            # 构造PYTHONPATH环境变量，包含数据可视化模块路径
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{visualizer_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
            result = subprocess.run([sys.executable, str(db_setup_script_path)], cwd=str(visualizer_path), env=env)
            if result.returncode != 0:
                print("警告: 数据库更新脚本执行失败。将继续启动可视化应用。")
            else:
                print("标注结果数据库更新完成。")
        else:
            print("警告: 找不到数据库更新脚本 (poetry-annotator-data-visualizer/data_visualizer/db_setup.py)。将继续启动可视化应用。")
            
        # 运行数据可视化应用
        visualizer_script_path = visualizer_path / "main.py"
        if visualizer_script_path.exists():
            # 使用streamlit运行可视化应用
            os.system(f"{sys.executable} -m streamlit run {visualizer_script_path}")
        else:
            print("错误: 找不到数据可视化启动脚本 (poetry-annotator-data-visualizer/main.py)")
            sys.exit(1)
    else:
        # 启动CLI模式
        # 将未知参数传递给click
        sys.argv[1:] = unknown
        cli()

if __name__ == '__main__':
    main() 