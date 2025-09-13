"""
项目插件配置管理器
负责读取和管理项目插件配置
"""

import configparser
import logging
from typing import Dict
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


class ProjectPluginConfigManager:
    """项目插件配置管理器"""
    
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path, encoding='utf-8')
        
    def get_plugin_config(self, plugin_name: str) -> PluginConfig:
        """获取特定插件的配置"""
        section_name = f'Plugin.{plugin_name}'
        
        if section_name not in self.config:
            raise ValueError(f"Plugin configuration for '{plugin_name}' not found")
            
        plugin_section = self.config[section_name]
        
        # 获取基本配置项
        enabled = plugin_section.getboolean('enabled', False)
        path = plugin_section.get('path', '')
        module = plugin_section.get('module', '')
        class_name = plugin_section.get('class', '')
        
        # 获取其他设置
        settings = {}
        for key, value in plugin_section.items():
            if key not in ['enabled', 'path', 'module', 'class']:
                settings[key] = value
                
        return PluginConfig(
            enabled=enabled,
            path=path,
            module=module,
            class_name=class_name,
            settings=settings
        )
        
    def get_all_plugin_configs(self) -> Dict[str, PluginConfig]:
        """获取所有插件配置"""
        plugin_configs = {}
        
        # 遍历所有Plugin.*节
        for section_name in self.config.sections():
            if section_name.startswith('Plugin.'):
                plugin_name = section_name[len('Plugin.'):]
                try:
                    config = self.get_plugin_config(plugin_name)
                    if config.enabled:
                        plugin_configs[plugin_name] = config
                except Exception as e:
                    logger.error(f"Failed to load plugin config for '{plugin_name}': {e}")
                    
        return plugin_configs