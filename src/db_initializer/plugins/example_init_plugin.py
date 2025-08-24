"""
示例数据库初始化插件
展示如何使用源数据路径和数据库路径参数
"""

from typing import Dict, Any
from src.db_initializer.plugin_interface import DatabaseInitPlugin
from src.config.schema import PluginConfig
from src.data.separate_databases import SeparateDatabaseManager


class ExampleInitPlugin(DatabaseInitPlugin):
    """示例数据库初始化插件"""
    
    def __init__(self, config: PluginConfig = None, 
                 separate_db_manager: SeparateDatabaseManager = None):
        super().__init__(config, separate_db_manager)
        self.name = "example_db_init"
        self.description = "示例数据库初始化插件"
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self.name
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self.description
    
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库
        
        Args:
            db_name: 数据库名称
            clear_existing: 是否清空现有数据
            
        Returns:
            初始化结果字典
        """
        result = {
            "status": "success",
            "message": f"示例插件初始化数据库 {db_name} 成功",
            "source_dir": self.source_dir,
            "db_paths": self.db_paths
        }
        
        # 在这里可以使用 source_dir 和 db_paths 参数进行实际的数据库初始化操作
        # 例如：
        # 1. 从 source_dir 读取源数据
        # 2. 根据 db_paths 中的路径初始化对应的数据库
        
        print(f"使用源数据路径: {self.source_dir}")
        print(f"使用数据库路径配置: {self.db_paths}")
        
        return result