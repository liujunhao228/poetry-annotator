"""
插件加载器实现
"""

import importlib
import logging
from typing import Dict, Any
from src.plugin_system.base import BasePlugin
from src.plugin_system.manager import PluginManager
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器"""
    
    @staticmethod
    def load_plugin(plugin_config: PluginConfig) -> BasePlugin:
        """根据配置加载插件"""
        module_name = plugin_config.module
        class_name = plugin_config.class_name
        
        if not module_name or not class_name:
            raise ValueError("Plugin configuration missing module or class name")
        
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
    def load_plugins_from_config(config_manager, plugin_manager: PluginManager):
        """根据配置管理器加载所有启用的插件"""
        try:
            # 获取全局插件配置
            global_plugin_config = config_manager.get_global_plugin_config()
        except Exception as e:
            logger.warning(f"Failed to get global plugin config: {e}")
            return
        
        # 遍历启用的插件列表
        for plugin_name in global_plugin_config.enabled_plugins:
            try:
                # 获取插件配置
                plugin_config = config_manager.get_plugin_config(plugin_name)
                
                # 如果插件被禁用，跳过
                if not plugin_config.enabled:
                    logger.debug(f"Plugin '{plugin_name}' is disabled, skipping")
                    continue
                
                # 加载插件
                plugin = PluginLoader.load_plugin(plugin_config)
                
                # 注册插件
                plugin_manager.register_plugin(plugin)
                
            except Exception as e:
                logger.error(f"Warning: Failed to load plugin '{plugin_name}': {e}")