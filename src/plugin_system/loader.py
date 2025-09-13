"""
插件加载器实现
"""

import importlib
import logging
import os
import sys
from typing import Dict, Any
from src.plugin_system.base import BasePlugin
from src.plugin_system.manager import PluginManager
from src.plugin_system.project_config_manager import ProjectPluginConfigManager
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器"""
    
    @staticmethod
    def load_plugin(plugin_config: PluginConfig, project_root: str) -> BasePlugin:
        """根据配置加载插件"""
        module_name = plugin_config.module
        class_name = plugin_config.class_name
        plugin_path = plugin_config.path
        
        if not module_name or not class_name:
            raise ValueError("Plugin configuration missing module or class name")
            
        # 将插件路径添加到sys.path
        if plugin_path:
            full_plugin_path = os.path.join(project_root, plugin_path)
            if full_plugin_path not in sys.path:
                sys.path.insert(0, full_plugin_path)
                logger.debug(f"Added plugin path to sys.path: {full_plugin_path}")
        
        try:
            # 动态导入模块
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)
            
            # 获取插件类
            logger.debug(f"Getting class: {class_name} from module: {module_name}")
            plugin_class = getattr(module, class_name)
            
            # 创建插件实例
            logger.info(f"Creating plugin instance: {module_name}.{class_name}")
            plugin = plugin_class(plugin_config)
            return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_name}.{class_name}: {e}")
            raise
    
    @staticmethod
    def load_plugins_from_config(config_manager: ProjectPluginConfigManager, plugin_manager: PluginManager, project_root: str):
        """根据配置管理器加载所有启用的插件"""
        try:
            plugin_configs = config_manager.get_all_plugin_configs()
            
            for plugin_name, plugin_config in plugin_configs.items():
                try:
                    # 加载插件
                    plugin = PluginLoader.load_plugin(plugin_config, project_root)
                    
                    # 注册插件
                    plugin_manager.register_plugin(plugin)
                    
                except Exception as e:
                    logger.error(f"Warning: Failed to load plugin '{plugin_name}': {e}")
        except Exception as e:
            logger.warning(f"Failed to load plugins from config: {e}")