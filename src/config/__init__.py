"""
配置管理包初始化文件
"""

# 从 config/metadata/config_metadata.json 读取配置文件路径
import os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_metadata_path = os.path.join(root_dir, 'config', 'metadata', 'config_metadata.json')

# 注意：这里我们不直接传入全局和项目配置路径，
# 而是让 ConfigManager 从 config_metadata.json 中读取
from .config_manager import config_manager

__all__ = ['config_manager']