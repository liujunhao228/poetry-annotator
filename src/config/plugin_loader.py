"""插件配置加载器"""

import configparser
import os
from typing import Dict, Any, List
from src.config.schema import PluginConfig, ProjectPluginsConfig


class ProjectPluginConfigLoader:
    """项目插件配置加载器，专门用于加载 project/plugins.ini"""
    
    def __init__(self, project_plugins_ini_path: str):
        self.project_plugins_ini_path = project_plugins_ini_path
    
    def load_project_plugin_config(self) -> ProjectPluginsConfig: # 注意：这里可以复用 ProjectPluginsConfig Schema
        """加载项目插件的全局配置部分 (enabled_plugins, plugin_paths)"""
        if not os.path.exists(self.project_plugins_ini_path):
            return ProjectPluginsConfig() # 返回空配置
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.project_plugins_ini_path, encoding='utf-8')
        
        plugin_config = ProjectPluginsConfig()
        
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
        """加载特定项目插件的详细配置"""
        section_name = f"Plugin.{plugin_name}"
        if not os.path.exists(self.project_plugins_ini_path):
            return PluginConfig()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.project_plugins_ini_path, encoding='utf-8')
        
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