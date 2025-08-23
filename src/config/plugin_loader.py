"""插件配置加载器"""

import configparser
import os
from typing import Dict, Any, List
from src.config.config_schema import GlobalPluginConfig, PluginConfig


class PluginConfigLoader:
    """插件配置加载器"""
    
    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path
    
    def load_global_plugin_config(self) -> GlobalPluginConfig:
        """加载全局插件配置"""
        if not os.path.exists(self.global_config_path):
            return GlobalPluginConfig()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')
        
        plugin_config = GlobalPluginConfig()
        
        if config.has_section('Plugins'):
            enabled_plugins_str = config.get('Plugins', 'enabled_plugins', fallback='')
            if enabled_plugins_str:
                plugin_config.enabled_plugins = [
                    name.strip() for name in enabled_plugins_str.split(',') if name.strip()
                ]
            
            plugin_paths_str = config.get('Plugins', 'plugin_paths', fallback='')
            if plugin_paths_str:
                plugin_config.plugin_paths = [
                    path.strip() for path in plugin_paths_str.split(',') if path.strip()
                ]
        
        return plugin_config
    
    def load_plugin_config(self, plugin_name: str) -> PluginConfig:
        """加载特定插件配置"""
        section_name = f"Plugin.{plugin_name}"
        if not os.path.exists(self.global_config_path):
            return PluginConfig()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')
        
        plugin_config = PluginConfig()
        
        if config.has_section(section_name):
            plugin_config.enabled = config.getboolean(section_name, 'enabled', fallback=True)
            # 显式处理 module 和 class_name 属性
            plugin_config.module = config.get(section_name, 'module', fallback="")
            plugin_config.class_name = config.get(section_name, 'class', fallback="")
            # 加载插件特定配置项
            for key, value in config.items(section_name):
                if key not in ['enabled', 'module', 'class']:
                    plugin_config.settings[key] = value
        
        return plugin_config