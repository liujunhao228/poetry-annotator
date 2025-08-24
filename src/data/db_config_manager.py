"""
统一数据库配置管理模块
提供统一的数据库配置获取和管理功能
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config_manager
config_manager = get_config_manager()


def get_database_paths() -> Dict[str, Any]:
    """
    获取统一的数据库路径配置
    
    Returns:
        Dict[str, Any]: 包含数据库路径配置的字典
    """
    # 获取生效的数据库配置
    db_config = config_manager.get_effective_database_config()
    
    # 只支持新的多数据库配置格式
    if 'db_paths' in db_config:
        return {
            'type': 'multi',
            'paths': db_config['db_paths']
        }
    else:
        # 默认配置
        return {
            'type': 'default',
            'paths': {
                'default': {
                    'raw_data': 'data/default/raw_data.db',
                    'annotation': 'data/default/annotation.db',
                    'emotion': 'data/default/emotion.db'
                }
            }
        }


def get_separate_database_paths(main_db_name: str = "default") -> Dict[str, str]:
    """
    获取分离数据库路径配置
    
    Args:
        main_db_name: 主数据库名称
        
    Returns:
        Dict[str, str]: 分离数据库路径配置
    """
    # 获取生效的数据库配置
    db_config = config_manager.get_effective_database_config()
    
    # 处理分离数据库配置
    if 'separate_db_paths' in db_config:
        separate_paths = db_config['separate_db_paths']
        # 解析占位符
        resolved_paths = {}
        for name, path in separate_paths.items():
            # 替换主数据库名称占位符
            path = path.replace('{main_db_name}', main_db_name)
            # 转换为绝对路径
            if not Path(path).is_absolute():
                resolved_paths[name] = str(Path(path).resolve())
            else:
                resolved_paths[name] = path
        return resolved_paths
    else:
        # 使用默认路径配置
        return {
            'raw_data': f'data/{main_db_name}/raw_data.db',
            'annotation': f'data/{main_db_name}/annotation.db',
            'emotion': f'data/{main_db_name}/emotion.db'
        }


def ensure_database_directory_exists(db_path: str) -> None:
    """
    确保数据库目录存在
    
    Args:
        db_path: 数据库文件路径
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_main_database_names() -> list:
    """
    获取所有主数据库名称
    
    Returns:
        list: 主数据库名称列表
    """
    db_config = config_manager.get_effective_database_config()
    
    # 只支持新的多数据库配置格式
    if 'db_paths' in db_config:
        return list(db_config['db_paths'].keys())
    else:
        # 如果没有主数据库配置，返回默认名称
        return ["default"]