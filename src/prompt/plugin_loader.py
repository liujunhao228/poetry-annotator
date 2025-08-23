"""Prompt构建插件加载器"""

import os
from typing import Dict, Any
import configparser

from src.prompt.plugin_interface import PromptBuilderPlugin
from src.prompt.default_plugin import DefaultPromptBuilderPlugin


class PromptPluginLoader:
    """Prompt插件加载器"""
    
    def __init__(self, plugins_config_path: str = "config/plugins.ini"):
        self.plugins_config_path = plugins_config_path
        self.default_plugin = DefaultPromptBuilderPlugin()
    
    def load_prompt_plugin(self, plugin_name: str) -> PromptBuilderPlugin:
        """加载特定Prompt插件"""
        # 对于默认插件，直接返回默认实例
        if plugin_name == "default":
            return self.default_plugin
            
        # 对于其他插件，需要从配置文件中读取并动态加载
        if not os.path.exists(self.plugins_config_path):
            return self.default_plugin
            
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.plugins_config_path, encoding='utf-8')
        
        section_name = f"PromptPlugin.{plugin_name}"
        if not config.has_section(section_name):
            return self.default_plugin
            
        try:
            # 从配置中获取模块名和类名
            plugin_module_name = config.get(section_name, 'module', fallback=f"src.prompt.plugins.{plugin_name}")
            plugin_class_name = config.get(section_name, 'class', fallback=f"{plugin_name.capitalize()}PromptPlugin")
            
            # 动态导入插件模块
            import importlib
            plugin_module = importlib.import_module(plugin_module_name)
            plugin_class = getattr(plugin_module, plugin_class_name)
            
            # 实例化插件
            plugin_instance = plugin_class()
            return plugin_instance
        except Exception as e:
            print(f"警告: 加载Prompt插件 '{plugin_name}' 时出错，使用默认插件: {e}")
            return self.default_plugin
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取特定插件配置"""
        section_name = f"PromptPlugin.{plugin_name}"
        if not os.path.exists(self.plugins_config_path):
            return {}
            
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.plugins_config_path, encoding='utf-8')
        
        plugin_config = {}
        if config.has_section(section_name):
            for key, value in config.items(section_name):
                plugin_config[key] = value
                
        return plugin_config