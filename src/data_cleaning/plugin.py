"""
数据清洗插件接口定义
"""

from abc import abstractmethod
from typing import Dict, Any, List
from src.plugin_system.interfaces import PreprocessingPlugin


class DataCleaningPlugin(PreprocessingPlugin):
    """数据清洗插件基类"""
    
    @abstractmethod
    def clean_data(self, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        清洗数据
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            清洗统计信息
        """
        pass
    
    @abstractmethod
    def reset_data_status(self, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        重置数据状态
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            重置统计信息
        """
        pass
    
    @abstractmethod
    def generate_report(self, db_name: str = "default") -> Dict[str, Any]:
        """
        生成清洗报告
        
        Args:
            db_name: 数据库名称
            
        Returns:
            清洗报告
        """
        pass