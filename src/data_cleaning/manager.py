"""
清洗管理器，协调各个清洗组件。
使用插件系统替代原有的规则集配置。
"""

from typing import Optional, Dict, Any
from .preprocessing_plugin_adapter import PreprocessingPlugin
from src.plugin_system.manager import get_plugin_manager


class DataCleaningManager(PreprocessingPlugin):
    """
    清洗管理器，协调各个清洗组件。
    使用插件系统替代原有的规则集配置。
    """

    def __init__(self, global_config_path: str = None, project_config_path: Optional[str] = None):
        """
        初始化清洗管理器。

        Args:
            global_config_path: 全局配置文件路径（已废弃，仅为了保持接口兼容性）。
            project_config_path: 项目配置文件路径（已废弃，仅为了保持接口兼容性）。
        """
        # 调用父类初始化
        from src.config.schema import PluginConfig
        plugin_config = PluginConfig()
        plugin_config.settings = {"name": "DefaultDataCleaningManager", "description": "默认数据清洗管理器"}
        super().__init__(plugin_config)
        
        # 获取插件管理器
        self.plugin_manager = get_plugin_manager()
        
        # 获取数据清洗插件
        self.cleaning_plugin = self.plugin_manager.get_plugin("default_data_cleaning")
        if self.cleaning_plugin is None:
            raise ValueError("未找到数据清洗插件")

    def clean_data(self, db_name: str = "default", dry_run: bool = False):
        """
        清洗数据。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            清洗统计信息。
        """
        return self.cleaning_plugin.clean_data(db_name, dry_run)

    def reset_data_status(self, db_name: str = "default", dry_run: bool = False):
        """
        重置数据状态。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            重置统计信息。
        """
        return self.cleaning_plugin.reset_data_status(db_name, dry_run)

    def generate_report(self, db_name: str = "default"):
        """
        生成清洗报告。

        Args:
            db_name: 数据库名称。

        Returns:
            清洗报告。
        """
        return self.cleaning_plugin.generate_report(db_name)
    
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作（实现预处理插件接口）
        
        Args:
            data: 输入数据
            **kwargs: 额外参数，包括：
                - db_name: 数据库名称（可选）
                - dry_run: 是否为试运行模式（可选）
                - action: 操作类型（'clean', 'reset', 'report'）
                
        Returns:
            处理后的数据（包含清洗统计信息）
        """
        db_name = kwargs.get('db_name', 'default')
        dry_run = kwargs.get('dry_run', False)
        action = kwargs.get('action', 'clean')
        
        if action == 'clean':
            result = self.clean_data(db_name, dry_run)
        elif action == 'reset':
            result = self.reset_data_status(db_name, dry_run)
        elif action == 'report':
            result = self.generate_report(db_name)
        else:
            raise ValueError(f"不支持的操作类型: {action}")
        
        # 将结果添加到数据中返回
        data['preprocessing_result'] = result
        return data