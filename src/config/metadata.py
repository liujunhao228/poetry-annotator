"""
配置元数据加载器，已弃用。
"""

import json
import os
from typing import Dict, Any


def load_config_metadata(config_metadata_path: str) -> Dict[str, Any]:
    """加载配置元数据文件（已弃用）"""
    print("警告: load_config_metadata 已弃用，不应再使用。")
    return {}