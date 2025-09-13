"""Prompt插件管理器"""

from typing import Dict, Any, Optional
import importlib

from src.prompt.plugin_interface import PromptPluginManager, PromptBuilderPlugin
from src.config import config_manager
from src.config.schema import PluginConfig


class PluginBasedPromptManager:
    """基于插件的Prompt管理器"""
    
    def __init__(self):
        self.plugin_manager = PromptPluginManager()
        self._load_plugins_from_config()
    
    def _load_plugins_from_config(self):
        """根据配置动态加载插件"""
        try:
            # 获取项目插件配置
            project_plugin_config = config_manager.get_project_plugins_config()
            
            # 遍历启用的Prompt插件列表，尝试加载每个插件
            for plugin_name in project_plugin_config.enabled_plugins:
                try:
                    # 获取插件配置
                    plugin_config = config_manager.get_plugin_config(plugin_name)
                    
                    # 如果插件被禁用，跳过
                    if not plugin_config.enabled:
                        continue
                    
                    # 检查是否是Prompt构建插件
                    plugin_type = plugin_config.settings.get('type', '')
                    if plugin_type != 'prompt_builder':
                        continue
                    
                    # 尝试导入并实例化插件
                    # 从配置中获取模块名和类名
                    plugin_module_name = plugin_config.module if plugin_config.module else f"src.prompt.plugins.{plugin_name}"
                    plugin_class_name = plugin_config.class_name if plugin_config.class_name else f"{plugin_name.capitalize()}PromptPlugin"
                    
                    # 动态导入插件模块
                    plugin_module = importlib.import_module(plugin_module_name)
                    plugin_class = getattr(plugin_module, plugin_class_name)
                    
                    # 实例化插件
                    plugin_instance = plugin_class()
                    self.plugin_manager.register_plugin(plugin_instance)
                    
                except Exception as e:
                    print(f"警告: 加载Prompt插件 '{plugin_name}' 时出错: {e}")
        except Exception as e:
            print(f"警告: 加载Prompt插件配置时出错: {e}")
    
    def get_prompt_builder(self, plugin_name: str = "default") -> PromptBuilderPlugin:
        """获取Prompt构建器"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            # 如果指定的插件不存在，返回默认插件
            plugin = self.plugin_manager.get_plugin("default")
        
        if not plugin:
            raise ValueError(f"未找到Prompt构建插件: {plugin_name}")
            
        return plugin
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return self.plugin_manager.list_plugins()