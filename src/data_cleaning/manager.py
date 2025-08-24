"""
清洗管理器，协调各个清洗组件。
"""

from typing import Optional, Dict, Any
from .rule_manager import CleaningRuleManager
from .cleaner import DataCleaner
from .report_generator import CleaningReportGenerator
from .preprocessing_plugin_adapter import PreprocessingPlugin


class DataCleaningManager(PreprocessingPlugin):
    """
    清洗管理器，协调各个清洗组件。
    """

    def __init__(self, global_config_path: str, project_config_path: Optional[str] = None):
        """
        初始化清洗管理器。

        Args:
            global_config_path: 全局配置文件路径。
            project_config_path: 项目配置文件路径（可选）。
        """
        # 调用父类初始化
        from src.config.schema import PluginConfig
        plugin_config = PluginConfig()
        plugin_config.settings = {"name": "DefaultDataCleaningManager", "description": "默认数据清洗管理器"}
        super().__init__(plugin_config)
        
        # 初始化规则管理器
        self.rule_manager = CleaningRuleManager(global_config_path, project_config_path)
        
        # 初始化数据清洗器
        self.cleaner = DataCleaner(self.rule_manager)
        
        # 初始化报告生成器
        self.report_generator = CleaningReportGenerator(self.rule_manager)

    def clean_data(self, db_name: str = "default", dry_run: bool = False):
        """
        清洗数据。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            清洗统计信息。
        """
        return self.cleaner.clean_poems_data(db_name, dry_run)

    def reset_data_status(self, db_name: str = "default", dry_run: bool = False):
        """
        重置数据状态。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            重置统计信息。
        """
        return self.cleaner.reset_data_status(db_name, dry_run)

    def generate_report(self, db_name: str = "default"):
        """
        生成清洗报告。

        Args:
            db_name: 数据库名称。

        Returns:
            清洗报告。
        """
        return self.report_generator.get_cleaning_report(db_name)

    def reload_config(self):
        """
        重新加载配置。
        """
        self.rule_manager.reload_config()
    
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作（实现预处理插件接口）
        
        Args:
            data: 输入数据
            **kwargs: 额外参数，包括：
                - db_name: 数据库名称（可选）
                - dry_run: 是否为试运行模式（可选）
                
        Returns:
            处理后的数据（包含清洗统计信息）
        """
        db_name = kwargs.get('db_name', 'default')
        dry_run = kwargs.get('dry_run', False)
        
        # 执行数据清洗
        result = self.clean_data(db_name, dry_run)
        
        # 将结果添加到数据中返回
        data['preprocessing_result'] = result
        return data