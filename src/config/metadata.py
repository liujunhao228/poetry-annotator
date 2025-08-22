"""
配置元数据加载器，负责加载 config_metadata.json 文件。
"""

import json
import os
from typing import Dict, Any


def load_config_metadata(config_metadata_path: str) -> Dict[str, Any]:
    """加载配置元数据文件"""
    if not os.path.exists(config_metadata_path):
        print(f"警告: 配置元数据文件不存在: {config_metadata_path}。将使用默认配置。")
        return {}
        
    try:
        with open(config_metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告: 读取配置元数据文件失败: {e}。将使用默认配置。")
        return {}