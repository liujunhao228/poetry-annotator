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
from src.config.manager import get_config_manager # 导入 get_config_manager

# 配置日志
logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器"""
    
    @staticmethod
    def load_plugin(plugin_config: PluginConfig, project_root: str, **kwargs) -> BasePlugin:
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
            
            # 创建插件实例，传递额外的 kwargs
            logger.info(f"Creating plugin instance: {module_name}.{class_name} with kwargs: {kwargs}")
            plugin = plugin_class(plugin_config, **kwargs)
            return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_name}.{class_name}: {e}")
            raise
    
    @staticmethod
    def load_plugins_from_config(config_manager: ProjectPluginConfigManager, plugin_manager: PluginManager, project_root: str):
        """根据配置管理器加载所有启用的插件"""
        try:
            plugin_configs = config_manager.get_all_plugin_configs()
            
            # 使用 ConfigManager 获取数据配置
            logger.debug("Attempting to get global config manager...")
            global_config_manager = get_config_manager()
            logger.debug(f"Global config manager obtained: {global_config_manager}")

            data_config = global_config_manager.get_effective_data_config()
            logger.debug(f"Effective data config obtained: {data_config}")
            
            data_output_dir = data_config.get('output_dir')
            logger.debug(f"Extracted data output_dir: '{data_output_dir}'")

            for plugin_name, plugin_config in plugin_configs.items():
                try:
                    # 准备传递给插件的额外参数
                    plugin_kwargs = {}
                    if data_output_dir:
                        plugin_kwargs['output_dir'] = data_output_dir

                    logger.debug(f"plugin_kwargs for plugin '{plugin_name}': {plugin_kwargs}")

                    # 加载插件，传递 output_dir
                    plugin = PluginLoader.load_plugin(plugin_config, project_root, **plugin_kwargs)
                    
                    # 注册插件
                    plugin_manager.register_plugin(plugin)
                    
                except Exception as e:
                    logger.error(f"Warning: Failed to load plugin '{plugin_name}': {e}")
        except Exception as e:
            logger.warning(f"Failed to load plugins from config: {e}")
