"""
启动器模块 - 负责启动 GUI 和 Visualizer 模式
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def launch_gui(project_name: Optional[str] = None):
    """启动 GUI 模式"""
    try:
        # 使用新的 GUI 模块
        from src.gui import run_gui
        
        # 如果有项目名称，设置环境变量
        if project_name:
            os.environ['POETRY_ANNOTATOR_PROJECT'] = project_name
        
        run_gui()
    except ImportError as e:
        print(f"错误：无法导入 GUI 模块：{e}")
        print("请确保已正确安装项目依赖")
        sys.exit(1)
    except Exception as e:
        print(f"错误：启动 GUI 失败：{e}")
        sys.exit(1)


def launch_visualizer(project_root: Path):
    """启动数据可视化模式"""
    visualizer_path = project_root / "poetry-annotator-data-visualizer"

    try:
        import streamlit
    except ImportError:
        print("错误：未安装 streamlit。请运行 'pip install streamlit' 后重试。")
        sys.exit(1)

    db_setup_script_path = visualizer_path / "data_visualizer" / "db_setup.py"
    if db_setup_script_path.exists():
        print("正在更新标注结果数据库...")
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{visualizer_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
        result = subprocess.run([sys.executable, str(db_setup_script_path)], cwd=str(visualizer_path), env=env)
        if result.returncode != 0:
            print("警告：数据库更新脚本执行失败。将继续启动可视化应用。")
        else:
            print("标注结果数据库更新完成。")
    else:
        print("警告：找不到数据库更新脚本。")

    visualizer_script_path = visualizer_path / "main.py"
    if visualizer_script_path.exists():
        os.system(f"{sys.executable} -m streamlit run {visualizer_script_path}")
    else:
        print("错误：找不到数据可视化启动脚本")
        sys.exit(1)
