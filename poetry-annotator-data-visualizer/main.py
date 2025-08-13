import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加数据可视化模块到Python路径
visualizer_path = Path(__file__).parent
if str(visualizer_path) not in sys.path:
    sys.path.insert(0, str(visualizer_path))

# 初始化日志系统
try:
    from src.logging_config import setup_default_logging
    setup_default_logging()
except ImportError:
    pass  # 如果无法导入主项目的日志配置，则使用默认配置

from data_visualizer.app.main_app import run_app
from data_visualizer.config import APP_TITLE, DB_PATHS
from data_visualizer.utils import logger

if __name__ == '__main__':
    logger.info(f"启动 {APP_TITLE} Streamlit 应用...")
    logger.info(f"使用的数据库路径: {DB_PATHS}")
    run_app()
