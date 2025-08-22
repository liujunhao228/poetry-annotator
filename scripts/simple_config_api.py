"""
为scripts/目录下的脚本提供简单、统一的配置API封装
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入配置管理器
try:
    from src.config import config_manager, project_config_manager
except ImportError:
    print("错误: 无法导入配置管理器，请检查项目结构")
    sys.exit(1)

# 导入数据管理器
try:
    from src.data import get_data_manager
except ImportError:
    print("错误: 无法导入数据管理器，请检查项目结构")
    sys.exit(1)


class SimpleConfigAPI:
    """为脚本提供简单、统一的配置与数据访问API"""
    
    def __init__(self):
        """初始化API实例"""
        self._config_manager = config_manager
        self._project_config_manager = project_config_manager
        self._data_managers = {}
    
    # --- 配置获取方法 ---
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config_manager.get_effective_database_config()
    
    def get_data_config(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return self._config_manager.get_effective_data_config()
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._config_manager.get_effective_logging_config()
    
    def get_prompt_config(self) -> Dict[str, str]:
        """获取提示词配置"""
        return self._config_manager.get_effective_prompt_config()
    
    def get_model_configs(self) -> List[Dict[str, Any]]:
        """获取所有生效的模型配置"""
        return self._config_manager.get_effective_model_configs()
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取指定模型的详细配置
        
        Args:
            model_name: 模型配置别名
            
        Returns:
            包含该模型所有配置项的字典
        """
        return self._config_manager.get_model_config(model_name)
    
    def get_model_prompt_config(self, model_name: str) -> Dict[str, str]:
        """
        获取指定模型的提示词模板配置
        
        Args:
            model_name: 模型配置别名
            
        Returns:
            包含模型特定提示词模板配置的字典
        """
        return self._config_manager.get_model_prompt_config(model_name)
    
    def get_visualizer_config(self) -> Dict[str, Any]:
        """获取数据可视化配置"""
        return self._config_manager.get_effective_visualizer_config()
    
    def get_validation_ruleset_name(self) -> str:
        """获取生效的校验规则集名称"""
        return self._config_manager.get_effective_validation_ruleset_name()
    
    def get_preprocessing_ruleset_name(self) -> str:
        """获取生效的预处理规则集名称"""
        return self._config_manager.get_effective_preprocessing_ruleset_name()
    
    def get_cleaning_ruleset_name(self) -> str:
        """获取生效的清洗规则集名称"""
        return self._config_manager.get_effective_cleaning_ruleset_name()
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM相关配置"""
        return self._config_manager.get_llm_config()
    
    def get_categories_config(self) -> Dict[str, str]:
        """获取情感分类配置（保持向后兼容）"""
        return self._config_manager.get_categories_config()
    
    # --- 项目管理方法 ---
    
    def switch_project_config(self, project_name: str) -> bool:
        """
        切换到指定的项目配置
        
        Args:
            project_name: 要切换到的项目配置文件名
            
        Returns:
            bool: 切换是否成功
        """
        return self._config_manager.switch_project_config(project_name)
    
    def get_available_project_configs(self) -> List[str]:
        """
        获取所有可用的项目配置文件列表
        
        Returns:
            List[str]: 可用的项目配置文件名列表
        """
        return self._config_manager.get_available_project_configs()
    
    def get_active_project_config(self) -> str:
        """
        获取当前激活的项目配置文件名
        
        Returns:
            str: 当前激活的项目配置文件名
        """
        return self._config_manager.get_active_project_config()
    
    # --- 数据访问方法 ---
    
    def get_data_manager(self, db_name: str = "default"):
        """
        获取数据管理器实例
        
        Args:
            db_name: 数据库名称
            
        Returns:
            DataManager实例
        """
        if db_name not in self._data_managers:
            self._data_managers[db_name] = get_data_manager(db_name)
        return self._data_managers[db_name]
    
    # --- 旧版本API兼容接口 ---
    
    def get_raw_items(self, section: str) -> List[tuple[str, str]]:
        """获取指定节下的所有原始键值对。"""
        return self._config_manager.get_raw_items(section)
    
    def list_model_configs(self) -> List[str]:
        """
        列出所有已定义的模型配置别名，顺序与配置文件中的顺序一致。

        Returns:
            一个包含所有模型别名的列表
        """
        return self._config_manager.list_model_configs()


# 全局API实例
simple_config_api = SimpleConfigAPI()