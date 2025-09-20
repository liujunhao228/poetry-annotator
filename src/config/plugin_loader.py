"""插件配置加载器"""

import configparser
import os
from typing import Dict, Any, List
from src.config.schema import PluginConfig, ProjectPluginsConfig


class ProjectPluginConfigLoader:
    """项目插件配置加载器，专门用于加载 project/plugins.ini"""
    
    def __init__(self, project_plugins_ini_path: str):
        self.project_plugins_ini_path = project_plugins_ini_path
    
    def load_project_plugin_config(self) -> ProjectPluginsConfig:
        """
        加载所有项目插件的配置，返回一个包含所有插件配置的 ProjectPluginsConfig 对象。
        """
        plugins_dict: Dict[str, PluginConfig] = {}
        
        if not os.path.exists(self.project_plugins_ini_path):
            return ProjectPluginsConfig(plugins=plugins_dict)
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.project_plugins_ini_path, encoding='utf-8')
        
        for section in config.sections():
            if section.startswith("Plugin."):
                plugin_name = section[len("Plugin."):]
                
                enabled = config.getboolean(section, 'enabled', fallback=True)
                path = config.get(section, 'path', fallback="")
                module = config.get(section, 'module', fallback="")
                class_name = config.get(section, 'class_name', fallback="") # Changed 'class' to 'class_name' for consistency
                
                settings = {}
                for key, value in config.items(section):
                    if key not in ['enabled', 'path', 'module', 'class_name']:
                        settings[key] = value
                
                plugins_dict[plugin_name] = PluginConfig(
                    enabled=enabled,
                    path=path,
                    module=module,
                    class_name=class_name,
                    settings=settings
                )
        
        return ProjectPluginsConfig(plugins=plugins_dict)
    
    def save_project_plugin_config(self, project_plugins_config: ProjectPluginsConfig):
        """
        保存项目插件配置到 project/plugins.ini 文件。
        """
        config = configparser.ConfigParser(interpolation=None)
        
        # 如果文件存在，先读取现有内容，以便保留未被 ProjectPluginsConfig 管理的配置
        if os.path.exists(self.project_plugins_ini_path):
            config.read(self.project_plugins_ini_path, encoding='utf-8')
            
        # 清除旧的插件配置节，以便完全由 ProjectPluginsConfig 控制
        sections_to_remove = [s for s in config.sections() if s.startswith("Plugin.")]
        for s in sections_to_remove:
            config.remove_section(s)
            
        for plugin_name, plugin_config in project_plugins_config.plugins.items():
            section_name = f"Plugin.{plugin_name}"
            if not config.has_section(section_name):
                config.add_section(section_name)
            
            config.set(section_name, 'enabled', str(plugin_config.enabled).lower())
            config.set(section_name, 'path', plugin_config.path)
            config.set(section_name, 'module', plugin_config.module)
            config.set(section_name, 'class_name', plugin_config.class_name) # Changed 'class' to 'class_name'
            
            for key, value in plugin_config.settings.items():
                config.set(section_name, key, str(value))
                
        with open(self.project_plugins_ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def load_plugin_config(self, plugin_name: str) -> PluginConfig:
        """
        从 project/plugins.ini 加载特定插件的详细配置。
        此方法现在会调用 load_project_plugin_config 并从中提取。
        """
        project_plugins_config = self.load_project_plugin_config()
        return project_plugins_config.plugins.get(plugin_name, PluginConfig())
