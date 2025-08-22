"""
模型配置管理器，处理模型配置的获取和管理。
"""

import configparser
import os
from typing import Dict, Any, List, Optional


class ModelManager:
    """模型配置管理器"""
    
    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path

    def get_effective_model_configs(self, project_model_names: List[str]) -> List[Dict[str, Any]]:
        """获取生效的模型配置列表"""
        # 使用项目配置中指定的模型名称列表
        return [self._get_global_model_config(name) for name in project_model_names]

    def _get_all_global_model_configs(self) -> List[Dict[str, Any]]:
        """获取所有全局模型配置"""
        if not os.path.exists(self.global_config_path):
            return []

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        model_configs = []
        for section in config.sections():
            if section.startswith('Model.'):
                model_name = section[len('Model.'):]
                model_config = self._get_global_model_config(model_name)
                if model_config:
                    model_configs.append(model_config)

        return model_configs

    def _get_global_model_config(self, model_name: str) -> Dict[str, Any]:
        """根据模型名称获取全局模型配置"""
        section_name = f"Model.{model_name}"
        if not os.path.exists(self.global_config_path):
            return {}

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        if not config.has_section(section_name):
            return {}

        return dict(config.items(section_name))
        
    # --- 旧版本API兼容接口 ---
    
    def add_model_section(self, model_name: str, template: Optional[Dict[str, Any]] = None):
        """
        添加一个新的模型配置节。
        可以基于一个模板字典来创建。
        """
        config = self._load_config()
        section_name = f"Model.{model_name}"
        if config.has_section(section_name):
            raise ValueError(f"模型配置节 '{section_name}' 已存在。")
        config.add_section(section_name)
        if template:
            for key, value in template.items():
                config.set(section_name, key, str(value))
        else:  # Add some default empty values
            defaults = {
                'provider': '', 'model_name': '', 'api_key': '', 'base_url': '',
                'temperature': '0.3', 'max_tokens': '1000', 'timeout': '30',
                'system_prompt_instruction_template': 'config/system_prompt_instruction.txt',
                'system_prompt_example_template': 'config/system_prompt_example.txt',
                'user_prompt_template': 'config/user_prompt_template.txt'
            }
            for key, value in defaults.items():
                config.set(section_name, key, str(value))
                
        with open(self.global_config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def remove_model_section(self, model_name: str):
        """删除一个模型配置节。"""
        config = self._load_config()
        section_name = f"Model.{model_name}"
        if not config.has_section(section_name):
            raise ValueError(f"未找到模型配置节: '{section_name}'")
        config.remove_section(section_name)
        
        with open(self.global_config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def get_raw_items(self, section: str) -> List[tuple[str, str]]:
        """获取指定节下的所有原始键值对。"""
        config = self._load_config()
        if config.has_section(section):
            return config.items(section)
        return []

    def get_model_config(self, config_name: str) -> Dict[str, Any]:
        """
        获取指定模型配置别名的详细配置

        Args:
            config_name: 模型配置的别名 (例如 'gpt-4o')

        Returns:
            包含该模型所有配置项的字典
        """
        return self._get_global_model_config(config_name)

    def list_model_configs(self) -> List[str]:
        """
        列出所有已定义的模型配置别名，顺序与配置文件中的顺序一致。

        Returns:
            一个包含所有模型别名的列表
        """
        # 这里需要根据实际的配置文件结构来实现
        # 暂时返回一个空列表，需要在后续完善
        return []

    def get_model_prompt_config(self, model_name: str, global_prompt_config: Dict[str, str]) -> Dict[str, str]:
        """
        获取指定模型的提示词模板配置
        
        Args:
            model_name: 模型配置别名
            global_prompt_config: 全局提示词配置
            
        Returns:
            包含模型特定提示词模板配置的字典
        """
        # 获取全局默认配置
        global_config = global_prompt_config
        
        # 获取模型特定配置
        model_config = self.get_model_config(model_name)
        
        # 合并配置，模型特定配置优先
        prompt_config = {
            'template_path': model_config.get('template_path', global_config['template_path']),
            'system_prompt_instruction_template': model_config.get('system_prompt_instruction_template', global_config['system_prompt_instruction_template']),
            'system_prompt_example_template': model_config.get('system_prompt_example_template', global_config['system_prompt_example_template']),
            'user_prompt_template': model_config.get('user_prompt_template', global_config['user_prompt_template'])
        }
        
        return prompt_config
        
    def _load_config(self):
        """加载配置文件（旧版本兼容接口）"""
        if not os.path.exists(self.global_config_path):
            # 如果文件不存在，可以考虑创建一个默认的
            print(f"警告: 配置文件不存在: {self.global_config_path}。将使用一个空的配置。")
            config = configparser.ConfigParser(interpolation=None)
            config.read_string('')  # 初始化一个空的ConfigParser
        else:
            config = configparser.ConfigParser(interpolation=None)
            config.read(self.global_config_path, encoding='utf-8')
        return config