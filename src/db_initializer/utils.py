"""
数据库初始化模块工具函数
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config_manager


def setup_module_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """设置模块专用日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent.absolute()


def resolve_path(path: str) -> str:
    """解析路径为绝对路径"""
    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)
    return str(get_project_root() / path)


def get_database_paths() -> Dict[str, str]:
    """获取分离数据库路径配置"""
    db_config = config_manager.get_effective_database_config()
    
    # 处理分离数据库配置
    if 'separate_db_paths' in db_config:
        separate_paths = db_config['separate_db_paths']
        # 确保使用绝对路径
        resolved_paths = {}
        for name, path in separate_paths.items():
            resolved_paths[name] = resolve_path(path)
        return resolved_paths
    else:
        # 使用默认路径配置
        return {
            'raw_data': resolve_path('data/default/raw_data.db'),
            'annotation': resolve_path('data/default/annotation.db'),
            'emotion': resolve_path('data/default/emotion.db')
        }


def ensure_directory_exists(path: str) -> None:
    """确保目录存在"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)