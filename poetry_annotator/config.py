"""
配置管理器 - 负责加载、管理和保存配置文件
"""

import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigManager:
    """配置管理器，负责加载、管理和保存配置文件"""

    def __init__(self, config_paths: List[str]):
        self.config_paths = config_paths
        self.config = configparser.ConfigParser(interpolation=None)
        self._load_config()

    def _load_config(self):
        """
        加载一个或多个配置文件。
        列表中的后续文件会覆盖前面文件中的同名配置项。
        """
        loaded_files = self.config.read(self.config_paths, encoding='utf-8')
        if not loaded_files:
            print(f"警告：配置文件都未找到：{self.config_paths}。将使用一个空的配置。")

    def save_config(self, path_index: int = -1):
        """
        将当前配置写入指定的一个文件。
        默认写入最后一个配置文件，通常是项目配置文件。
        """
        if not self.config_paths:
            raise ValueError("没有配置文件路径可供保存。")
        if path_index >= len(self.config_paths) or path_index < -len(self.config_paths):
            raise IndexError("指定的 path_index 超出范围。")

        target_path = self.config_paths[path_index]
        target_dir = os.path.dirname(target_path)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with open(target_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def update_setting(self, section: str, option: str, value: Any):
        """更新一个配置项。如果节不存在，则创建它。"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def add_model_section(self, model_name: str, template: Optional[Dict[str, Any]] = None):
        """添加一个新的模型配置节。"""
        section_name = f"Model.{model_name}"
        if self.config.has_section(section_name):
            raise ValueError(f"模型配置节 '{section_name}' 已存在。")
        self.config.add_section(section_name)
        if template:
            for key, value in template.items():
                self.config.set(section_name, key, str(value))
        else:
            defaults = {
                'provider': '', 'model_name': '', 'api_key': '', 'base_url': '',
                'temperature': '0.3', 'max_tokens': '1000', 'timeout': '30'
            }
            for key, value in defaults.items():
                 self.config.set(section_name, key, str(value))

    def remove_model_section(self, model_name: str):
        """删除一个模型配置节。"""
        section_name = f"Model.{model_name}"
        if not self.config.has_section(section_name):
            raise ValueError(f"未找到模型配置节：'{section_name}'")
        self.config.remove_section(section_name)

    def get_raw_items(self, section: str) -> List[tuple[str, str]]:
        """获取指定节下的所有原始键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 相关配置"""
        return {
            'max_workers': self.config.getint('LLM', 'max_workers'),
            'max_model_pipelines': self.config.getint('LLM', 'max_model_pipelines'),
            'max_retries': self.config.getint('LLM', 'max_retries'),
            'retry_delay': self.config.getint('LLM', 'retry_delay')
        }

    def get_model_config(self, config_name: str) -> Dict[str, Any]:
        """获取指定模型配置别名的详细配置"""
        section_name = f"Model.{config_name}"
        if not self.config.has_section(section_name):
            raise ValueError(f"未在配置文件中找到模型配置节：[{section_name}]")
        return dict(self.config.items(section_name))

    def list_model_configs(self) -> List[str]:
        """列出所有已定义的模型配置别名。"""
        prefix = "Model."
        configs = []
        for section in self.config.sections():
            if section.startswith(prefix):
                configs.append(section[len(prefix):])
        return configs

    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        db_paths_str = self.config.get('Database', 'db_paths', fallback=None)
        if db_paths_str:
            db_paths = {}
            for item in db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    db_paths[name.strip()] = path.strip()
            return {'db_paths': db_paths}
        db_path = self.config.get('Database', 'db_path', fallback=None)
        if db_path:
            return {'db_path': db_path}
        return {}

    def get_data_config(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return {
            'source_dir': self.config.get('Data', 'source_dir'),
            'output_dir': self.config.get('Data', 'output_dir')
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置，支持分离的日志级别"""
        return {
            'console_log_level': self.config.get('Logging', 'console_log_level', fallback='INFO'),
            'file_log_level': self.config.get('Logging', 'file_log_level', fallback='DEBUG'),
            'enable_file_log': self.config.getboolean('Logging', 'enable_file_log', fallback=True),
            'log_file': self.config.get('Logging', 'log_file', fallback='logs/poetry_annotator.log'),
            'enable_console_log': self.config.getboolean('Logging', 'enable_console_log', fallback=True),
            'max_file_size': self.config.getint('Logging', 'max_file_size', fallback=10),
            'backup_count': self.config.getint('Logging', 'backup_count', fallback=5),
            'quiet_third_party': self.config.getboolean('Logging', 'quiet_third_party', fallback=True),
        }

    def get_visualizer_config(self) -> Dict[str, Any]:
        """获取数据可视化配置"""
        return {
            'enable_custom_download': self.config.getboolean('Visualizer', 'enable_custom_download', fallback=False)
        }

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        all_configs = {
            'llm': self.get_llm_config(),
            'database': self.get_database_config(),
            'data': self.get_data_config(),
            'visualizer': self.get_visualizer_config(),
            'models': {}
        }
        for name in self.list_model_configs():
            all_configs['models'][name] = self.get_model_config(name)
        return all_configs

    def validate_config(self) -> bool:
        """验证配置的完整性"""
        try:
            required_sections = ['LLM', 'Database', 'Data']
            for section in required_sections:
                if not self.config.has_section(section):
                    print(f"警告：缺少配置节 [{section}]")
                    return False
            llm_config = self.get_llm_config()
            db_config = self.get_database_config()
            if not db_config:
                print("错误：未设置数据库路径 (db_path 或 db_paths)")
                return False
            data_config = self.get_data_config()
            if not data_config['source_dir'] or not data_config['output_dir']:
                print("错误：未设置数据路径")
                return False
            return True
        except Exception as e:
            print(f"配置验证失败：{e}")
            return False
