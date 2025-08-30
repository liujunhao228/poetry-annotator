"""
统一数据库配置管理模块
提供统一的数据库配置获取和管理功能
"""

import os
import sys
from typing import Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config_manager
config_manager = get_config_manager()


def get_database_paths() -> Dict[str, Any]:
    """
    获取分离数据库路径配置
    
    Returns:
        Dict[str, Any]: 包含数据库路径配置的字典
    """
    # 始终返回分离数据库配置
    return {
        'type': 'separate',
        'paths': get_separate_database_paths()
    }


def get_separate_database_paths() -> Dict[str, str]:
    """
    获取分离数据库路径配置
    
    Returns:
        Dict[str, str]: 分离数据库路径配置
    """
    # 获取生效的数据库配置
    db_config = config_manager.get_effective_database_config()
    
    # 处理分离数据库配置
    if 'separate_db_paths' in db_config:
        separate_paths = db_config['separate_db_paths']
        # 解析占位符并转换为绝对路径
        resolved_paths = {}
        for name, path in separate_paths.items():
            # 转换为绝对路径
            if not Path(path).is_absolute():
                resolved_paths[name] = str(Path(path).resolve())
            else:
                resolved_paths[name] = path
        return resolved_paths
    else:
        # 使用默认路径配置
        return {
            'raw_data': 'data/default/raw_data.db',
            'annotation': 'data/default/annotation.db',
            'emotion': 'data/default/emotion.db'
        }


def ensure_database_directory_exists(db_path: str) -> None:
    """
    确保数据库目录存在
    
    Args:
        db_path: 数据库文件路径
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)