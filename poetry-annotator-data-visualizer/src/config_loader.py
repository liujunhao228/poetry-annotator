"""
配置加载器
负责加载和管理应用配置
"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional

from data_visualizer.utils import logger


class ConfigLoader:
    """
    配置加载器
    
    加载顺序：
    1. default.yaml - 默认配置
    2. local.yaml - 本地覆盖配置（可选，不被 git 跟踪）
    3. 环境变量覆盖
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置加载器
        
        :param config_dir: 配置文件目录，默认为 config/
        """
        if config_dir is None:
            from data_visualizer.config import visualizer_project_root
            config_dir = str(visualizer_project_root / "config")
        
        self.config_dir = Path(config_dir)
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 1. 加载默认配置
        default_config_path = self.config_dir / "default.yaml"
        if default_config_path.exists():
            with open(default_config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"已加载默认配置：{default_config_path}")
        else:
            logger.warning(f"默认配置文件不存在：{default_config_path}")
            self.config = {}
        
        # 2. 加载本地覆盖配置（如果存在）
        local_config_path = self.config_dir / "local.yaml"
        if local_config_path.exists():
            with open(local_config_path, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
            self._merge_config(local_config)
            logger.info(f"已加载本地配置：{local_config_path}")
        
        # 3. 环境变量覆盖（可选）
        self._apply_env_overrides()
    
    def _merge_config(self, override_config: dict):
        """合并配置（递归深度合并）"""
        for key, value in override_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self._merge_config_dict(self.config[key], value)
            else:
                self.config[key] = value
    
    def _merge_config_dict(self, base: dict, override: dict):
        """递归合并两个字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_dict(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # 例如：VISUALIZER_DATABASE_PATHS 可以覆盖数据库路径配置
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        :param key: 配置键（支持点分隔，如 'database.paths'）
        :param default: 默认值
        :return: 配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_paths(self, project_root: Optional[Path] = None) -> dict:
        """
        获取数据库路径（解析为绝对路径）
        
        :param project_root: 项目根目录
        :return: 数据库路径字典
        """
        if project_root is None:
            from data_visualizer.config import project_root as main_project_root
            project_root = main_project_root
        
        db_paths_config = self.get('database.paths', {})
        db_paths = {}
        
        for name, path in db_paths_config.items():
            if not os.path.isabs(path):
                db_paths[name] = str(project_root / path)
            else:
                db_paths[name] = path
        
        return db_paths
    
    def get_cache_config(self) -> dict:
        """获取缓存配置"""
        return self.get('cache', {})
    
    def get_ui_config(self) -> dict:
        """获取 UI 配置"""
        return self.get('ui', {})
    
    def get_apriori_config(self) -> dict:
        """获取 Apriori 配置"""
        return self.get('apriori', {})


# 全局单例实例
_config_loader_instance: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器单例实例"""
    global _config_loader_instance
    if _config_loader_instance is None:
        _config_loader_instance = ConfigLoader()
    return _config_loader_instance
