"""
全局配置加载器，负责从全局配置文件加载各种配置到对应的 schema 对象中。
"""

import configparser
import os
from typing import Dict, Any, Optional, List

from src.config.schema import (
    GlobalConfig, GlobalLLMConfig, GlobalDatabaseConfig, GlobalDataPathConfig,
    GlobalPromptConfig, GlobalLoggingConfig, GlobalVisualizerConfig,
    GlobalModelConfigTemplate
)


class GlobalConfigLoader:
    """全局配置加载器"""

    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path

    def load(self) -> GlobalConfig:
        """加载全局配置文件"""
        if not os.path.exists(self.global_config_path):
            print(f"警告: 全局配置文件不存在: {self.global_config_path}。将使用默认配置。")
            return GlobalConfig()

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        global_config = GlobalConfig()

        # LLM 配置
        if config.has_section('LLM'):
            global_config.llm = GlobalLLMConfig(
                max_workers=config.getint('LLM', 'max_workers', fallback=1),
                max_model_pipelines=config.getint('LLM', 'max_model_pipelines', fallback=1),
                max_retries=config.getint('LLM', 'max_retries', fallback=3),
                retry_delay=config.getint('LLM', 'retry_delay', fallback=5),
                breaker_fail_max=config.getint('LLM', 'breaker_fail_max', fallback=3),
                breaker_reset_timeout=config.getint('LLM', 'breaker_reset_timeout', fallback=60),
                save_full_response=config.getboolean('LLM', 'save_full_response', fallback=False)
            )

        # 数据库配置
        if config.has_section('Database'):
            # 这里只加载可用配置的名称，不加载实际路径
            db_paths_str = config.get('Database', 'db_paths', fallback='')
            if db_paths_str:
                available_configs = list(
                    name.strip() for name in db_paths_str.split(',') if '=' in name.strip()
                )
                global_config.database = GlobalDatabaseConfig(
                    available_configs=available_configs
                )
            
            # 加载分离数据库配置模板
            separate_db_paths_str = config.get('Database', 'separate_db_paths', fallback=None)
            if separate_db_paths_str:
                separate_db_template = {}
                for item in separate_db_paths_str.split(','):
                    if '=' in item:
                        name, path = item.split('=', 1)
                        separate_db_template[name.strip()] = path.strip()
                global_config.database.separate_db_template = separate_db_template

        # 数据路径配置
        if config.has_section('Data'):
            # 这里只定义配置名称，不加载实际路径
            global_config.data_path = GlobalDataPathConfig(
                available_configs=["default"]
            )

        # 提示词配置
        if config.has_section('Prompt'):
            # 这里只定义配置名称，不加载实际路径
            global_config.prompt = GlobalPromptConfig(
                available_configs=["default"]
            )

        # 日志配置
        if config.has_section('Logging'):
            global_config.logging = GlobalLoggingConfig(
                console_log_level=config.get('Logging', 'console_log_level', fallback='INFO'),
                file_log_level=config.get('Logging', 'file_log_level', fallback='DEBUG'),
                enable_file_log=config.getboolean('Logging', 'enable_file_log', fallback=True),
                log_file=config.get('Logging', 'log_file', fallback=''),
                enable_console_log=config.getboolean('Logging', 'enable_console_log', fallback=True),
                max_file_size=config.getint('Logging', 'max_file_size', fallback=10),
                backup_count=config.getint('Logging', 'backup_count', fallback=5),
                quiet_third_party=config.getboolean('Logging', 'quiet_third_party', fallback=True)
            )

        # 可视化配置
        if config.has_section('Visualizer'):
            global_config.visualizer = GlobalVisualizerConfig(
                enable_custom_download=config.getboolean('Visualizer', 'enable_custom_download',
                                                        fallback=False)
            )

        # 模型配置模板（模型特定配置在_model_configs中处理）
        global_config.model_template = GlobalModelConfigTemplate()
        
        # 插件配置在plugin_loader中处理

        return global_config

    def save(self, global_config: GlobalConfig):
        """将当前全局配置写入文件"""
        config = configparser.ConfigParser(interpolation=None)

        # LLM 配置
        config.add_section('LLM')
        llm = global_config.llm
        config.set('LLM', 'max_workers', str(llm.max_workers))
        config.set('LLM', 'max_model_pipelines', str(llm.max_model_pipelines))
        config.set('LLM', 'max_retries', str(llm.max_retries))
        config.set('LLM', 'retry_delay', str(llm.retry_delay))
        config.set('LLM', 'breaker_fail_max', str(llm.breaker_fail_max))
        config.set('LLM', 'breaker_reset_timeout', str(llm.breaker_reset_timeout))
        config.set('LLM', 'save_full_response', str(llm.save_full_response))

        # 数据库配置
        config.add_section('Database')
        db = global_config.database
        # 注意：这里只保存配置名称，不保存实际路径
        config.set('Database', 'db_paths', ','.join(db.available_configs))
        # 保存分离数据库配置模板
        if db.separate_db_template:
            separate_db_paths_str = ','.join(f"{k}={v}" for k, v in db.separate_db_template.items())
            config.set('Database', 'separate_db_paths', separate_db_paths_str)

        # 数据路径配置
        config.add_section('Data')
        data = global_config.data_path
        # 注意：这里只保存配置名称
        config.set('Data', 'available_configs', ','.join(data.available_configs))

        # 提示词配置
        config.add_section('Prompt')
        prompt = global_config.prompt
        # 注意：这里只保存配置名称
        config.set('Prompt', 'available_configs', ','.join(prompt.available_configs))

        # 日志配置
        config.add_section('Logging')
        log = global_config.logging
        config.set('Logging', 'console_log_level', log.console_log_level)
        config.set('Logging', 'file_log_level', log.file_log_level)
        config.set('Logging', 'enable_file_log', str(log.enable_file_log))
        config.set('Logging', 'log_file', log.log_file)
        config.set('Logging', 'enable_console_log', str(log.enable_console_log))
        config.set('Logging', 'max_file_size', str(log.max_file_size))
        config.set('Logging', 'backup_count', str(log.backup_count))
        config.set('Logging', 'quiet_third_party', str(log.quiet_third_party))

        # 可视化配置
        config.add_section('Visualizer')
        viz = global_config.visualizer
        config.set('Visualizer', 'enable_custom_download', str(viz.enable_custom_download))

        # 保存到文件
        with open(self.global_config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def _get_global_database_config(self) -> Dict[str, Any]:
        """获取全局数据库配置（默认），支持主数据库和分离数据库"""
        # 这里需要从全局配置文件中读取实际的路径
        # 由于我们只在_global_config中保存了名称，需要重新读取配置文件
        if not os.path.exists(self.global_config_path):
            return {}

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        if not config.has_section('Database'):
            return {}

        result = {}

        # 尝试获取新的多数据库配置
        db_paths_str = config.get('Database', 'db_paths', fallback=None)
        if db_paths_str:
            # 解析 "name1=path1,name2=path2" 格式
            db_paths = {}
            for item in db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    db_paths[name.strip()] = path.strip()
            result['db_paths'] = db_paths

        # 尝试获取分离数据库配置
        separate_db_paths_str = config.get('Database', 'separate_db_paths', fallback=None)
        if separate_db_paths_str:
            # 解析 "name1=path1,name2=path2" 格式
            separate_db_paths = {}
            for item in separate_db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    separate_db_paths[name.strip()] = path.strip()
            result['separate_db_paths'] = separate_db_paths

        # 回退到旧的单数据库配置
        if not result.get('db_paths'):
            db_path = config.get('Database', 'db_path', fallback=None)
            if db_path:
                result['db_path'] = db_path

        return result

    def _get_global_data_config(self) -> Dict[str, str]:
        """获取全局数据路径配置（默认）"""
        if not os.path.exists(self.global_config_path):
            return {}

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        if not config.has_section('Data'):
            return {}

        return {
            'source_dir': config.get('Data', 'source_dir', fallback=None),
            'output_dir': config.get('Data', 'output_dir', fallback=None)
        }

    def _get_global_prompt_config(self) -> Dict[str, str]:
        """获取全局提示词配置（旧版本兼容接口）"""
        # 不再使用模板文件，返回空配置
        return {}

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