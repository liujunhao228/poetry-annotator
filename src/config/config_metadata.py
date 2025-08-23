"""
配置元数据加载模块
"""

import json
import os
from typing import Dict, Any


def load_config_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    加载配置元数据
    
    Args:
        metadata_path: 配置元数据文件路径
        
    Returns:
        包含配置元数据的字典
    """
    if not os.path.exists(metadata_path):
        # 如果元数据文件不存在，返回默认配置
        return {
            "global_config_file": "config/global/config.ini",
            "active_project_config_file": "config/system/active_project.json"
        }
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)