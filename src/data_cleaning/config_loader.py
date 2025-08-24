"""
清洗配置加载器，负责加载清洗配置。
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class CleaningConfigLoader:
    """
    清洗配置加载器，负责加载清洗配置。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化清洗配置加载器。

        Args:
            config_path: 配置文件路径，默认为 config/cleaning_rules.yaml
        """
        self.config_path = config_path

    def load_config(self) -> dict:
        """ 加载数据清洗的配置文件
        :return: 解析后的配置字典
        """
        if self.config_path is None:
            # 尝试在项目根目录下查找配置文件
            project_root = Path(__file__).parent.parent.parent
            self.config_path = os.path.join(project_root, 'config', 'cleaning_rules.yaml')

        if not os.path.exists(self.config_path):
            print(f"警告: 配置文件 {self.config_path} 不存在，将使用默认规则。")
            # 返回一个默认配置或抛出异常，这里简化处理
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"成功加载配置文件: {self.config_path}")
            return config
        except Exception as e:
            print(f"加载配置文件 {self.config_path} 时出错: {e}")
            raise