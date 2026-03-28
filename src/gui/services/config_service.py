"""配置服务"""

import configparser
from pathlib import Path
from typing import Optional, Any, Dict, List


class ConfigService:
    """
    GUI 配置服务
    
    负责管理 GUI 应用所需的配置信息，包括模型配置、数据库配置等。
    封装对 ConfigManager 的调用，提供更适合 GUI 使用的接口。
    """
    
    def __init__(self, config_manager: Any):
        """
        初始化配置服务
        
        Args:
            config_manager: 项目配置管理器实例
        """
        self.config_manager = config_manager
        self._models_cache: Optional[List[str]] = None
        self._db_config_cache: Optional[Dict] = None
    
    def list_models(self, refresh: bool = False) -> List[str]:
        """
        获取已配置的模型列表
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            模型配置名称列表
        """
        if self._models_cache is None or refresh:
            try:
                self._models_cache = self.config_manager.list_model_configs()
            except Exception as e:
                print(f"错误：加载模型配置失败：{e}")
                self._models_cache = []
        return self._models_cache
    
    def get_database_config(self, refresh: bool = False) -> Dict:
        """
        获取数据库配置
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            数据库配置字典
        """
        if self._db_config_cache is None or refresh:
            try:
                self._db_config_cache = self.config_manager.get_database_config()
            except Exception as e:
                print(f"错误：加载数据库配置失败：{e}")
                self._db_config_cache = {}
        return self._db_config_cache
    
    def get_database_names(self) -> List[str]:
        """
        获取所有数据库名称
        
        Returns:
            数据库名称列表
        """
        db_config = self.get_database_config()
        
        if 'db_paths' in db_config:
            return list(db_config['db_paths'].keys())
        elif 'db_path' in db_config:
            # 单数据库模式，返回默认名称
            try:
                project_name = self._get_project_name()
                return [f"{project_name} · {db_config['db_path']}"]
            except:
                return ["default"]
        return []
    
    def get_database_path(self, db_name: str) -> str:
        """
        根据数据库名称获取完整路径
        
        Args:
            db_name: 数据库名称
            
        Returns:
            数据库文件路径
        """
        db_config = self.get_database_config()
        
        # 处理显示名称格式
        if " · " in db_name:
            # 单数据库模式的显示格式
            return db_config.get('db_path', '')
        
        if 'db_paths' in db_config:
            return db_config['db_paths'].get(db_name, '')
        elif 'db_path' in db_config and db_name == "default":
            return db_config['db_path']
        
        return ''
    
    def _get_project_name(self) -> str:
        """从配置路径推断项目名称"""
        try:
            config_paths = getattr(self.config_manager, 'config_paths', [])
            for p in config_paths:
                if 'project' in p.lower() or 'projects' in p.lower():
                    parts = Path(p).parts
                    for i, part in enumerate(parts):
                        if part == 'projects' and i + 1 < len(parts):
                            return parts[i + 1]
        except:
            pass
        return "default"
    
    def get_model_display_name(self, model_name: str) -> str:
        """
        获取模型的显示名称（包含 provider 信息）
        
        Args:
            model_name: 模型配置名称
            
        Returns:
            格式化后的显示名称
        """
        try:
            # 尝试获取模型详细信息
            models = self.config_manager.list_model_configs()
            if model_name in models:
                # 可以扩展为返回更详细的信息
                return model_name
        except:
            pass
        return model_name
    
    def validate_model(self, model_name: str) -> bool:
        """
        验证模型名称是否有效
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否有效
        """
        if not model_name or "无" in model_name or "失败" in model_name:
            return False
        return model_name in self.list_models()
    
    def validate_database(self, db_name: str) -> bool:
        """
        验证数据库名称是否有效
        
        Args:
            db_name: 数据库名称
            
        Returns:
            是否有效
        """
        if not db_name or "无" in db_name or "失败" in db_name:
            return False
        
        db_config = self.get_database_config()
        
        if 'db_paths' in db_config:
            return db_name in db_config['db_paths']
        elif 'db_path' in db_config:
            # 单数据库模式，检查显示名称
            project_name = self._get_project_name()
            expected_name = f"{project_name} · {db_config['db_path']}"
            return db_name == expected_name or db_name == "default"
        
        return False
