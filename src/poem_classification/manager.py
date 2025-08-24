"""
诗词预处理分类管理器，协调各个分类组件。
"""

from typing import Optional
from pathlib import Path

from src.poem_classification import PoemClassificationPlugin
from src.component_system import PluginConfig


class PoemClassificationManager(PoemClassificationPlugin):
    """
    诗词预处理分类管理器，协调各个分类组件。
    """

    def __init__(self, project_root: str, config_path: Optional[str] = None):
        """
        初始化诗词预处理分类管理器。

        Args:
            project_root: 项目根目录路径。
            config_path: 配置文件路径（可选）。
        """
        # 创建插件配置
        plugin_config = PluginConfig()
        plugin_config.settings = {
            "name": "DefaultPoemClassificationManager",
            "description": "默认诗词预处理分类管理器",
            "project_root": project_root,
        }
        
        if config_path:
            plugin_config.settings["config_path"] = config_path
            
        # 调用父类初始化
        super().__init__(plugin_config)
        
    def classify_data(self, db_name: str = "default", dry_run: bool = False):
        """
        对诗词数据进行预处理分类。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            分类统计信息。
        """
        return self.classify_poems_data(db_name, dry_run)

    def reset_data_classification(self, db_name: str = "default", dry_run: bool = False):
        """
        重置数据分类。

        Args:
            db_name: 数据库名称。
            dry_run: 是否为试运行模式。

        Returns:
            重置统计信息。
        """
        return self.reset_pre_classification(db_name, dry_run)

    def generate_classification_report(self, db_name: str = "default"):
        """
        生成分类报告。

        Args:
            db_name: 数据库名称。

        Returns:
            分类报告。
        """
        return self.get_classification_report(db_name)