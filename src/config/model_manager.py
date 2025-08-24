"""
模型管理器，用于管理模型配置。
"""

import configparser
import os
from typing import Dict, Any, List, Optional


class ModelManager:
    """模型管理器"""

    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path
        self.config = self._load_config()

    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件"""
        if not os.path.exists(self.global_config_path):
            return configparser.ConfigParser()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')
        return config

    def get_effective_model_configs(self, model_names: List[str]) -> List[Dict[str, Any]]:
        """
        获取生效的模型配置列表
        
        Args:
            model_names: 模型名称列表
            
        Returns:
            模型配置列表
        """
        model_configs = []
        for model_name in model_names:
            model_config = self.get_model_config(model_name)
            if model_config:
                model_configs.append(model_config)
        return model_configs

    def get_model_config(self, config_name: str) -> Dict[str, Any]:
        """
        获取指定模型配置别名的详细配置

        Args:
            config_name: 模型配置的别名 (例如 'qwen-max')

        Returns:
            包含该模型所有配置项的字典
        """
        section_name = f"Model.{config_name}"
        if not self.config.has_section(section_name):
            return {}

        model_config = dict(self.config[section_name])
        # 转换特定字段的类型
        if 'request_delay' in model_config:
            model_config['request_delay'] = float(model_config['request_delay'])
        if 'temperature' in model_config:
            model_config['temperature'] = float(model_config['temperature'])
        if 'max_tokens' in model_config:
            model_config['max_tokens'] = int(model_config['max_tokens'])
        if 'timeout' in model_config:
            model_config['timeout'] = int(model_config['timeout'])
        if 'enable_thinking' in model_config:
            model_config['enable_thinking'] = model_config['enable_thinking'].lower() == 'true'
        if 'stream' in model_config:
            model_config['stream'] = model_config['stream'].lower() == 'true'

        return model_config

    def list_model_configs(self) -> List[str]:
        """
        列出所有已定义的模型配置别名，顺序与配置文件中的顺序一致。

        Returns:
            一个包含所有模型别名的列表
        """
        model_names = []
        for section_name in self.config.sections():
            if section_name.startswith('Model.'):
                model_names.append(section_name[len('Model.'):])
        return model_names

    def add_model_section(self, model_name: str, template: Optional[Dict[str, Any]] = None):
        """
        添加一个新的模型配置节。
        可以基于一个模板字典来创建。
        """
        section_name = f"Model.{model_name}"
        
        if not self.config.has_section(section_name):
            self.config.add_section(section_name)
        
        if template:
            for key, value in template.items():
                self.config.set(section_name, key, str(value))
        
        # 保存到文件
        with open(self.global_config_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def remove_model_section(self, model_name: str):
        """删除一个模型配置节。"""
        section_name = f"Model.{model_name}"
        
        if self.config.has_section(section_name):
            self.config.remove_section(section_name)
            
            # 保存到文件
            with open(self.global_config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)

    def get_raw_items(self, section: str) -> List[tuple[str, str]]:
        """获取指定节下的所有原始键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def _get_all_global_model_configs(self) -> List[Dict[str, Any]]:
        """获取所有全局模型配置（内部使用）"""
        model_configs = []
        for section_name in self.config.sections():
            if section_name.startswith('Model.'):
                model_name = section_name[len('Model.'):]
                model_config = self.get_model_config(model_name)
                model_config['name'] = model_name
                model_configs.append(model_config)
        return model_configs

    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件（旧版本兼容接口）"""
        if not os.path.exists(self.global_config_path):
            return configparser.ConfigParser()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')
        return config