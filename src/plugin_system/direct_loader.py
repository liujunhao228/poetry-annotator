"""
直接插件加载器
用于直接加载项目中的插件类，无需适配器
"""

import importlib
import logging
from typing import Dict, Any
from src.plugin_system.base import BasePlugin
from src.plugin_system.manager import PluginManager
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


class DirectPluginLoader:
    """直接插件加载器"""
    
import os
import configparser # 导入 configparser

class DirectPluginLoader:
    """直接插件加载器"""
    
    @staticmethod
    def load_plugin(plugin_config: PluginConfig, project_root: str, **kwargs) -> BasePlugin:
        """根据配置直接加载插件"""
        module_name = plugin_config.module
        class_name = plugin_config.class_name
        
        if not module_name or not class_name:
            raise ValueError("Plugin configuration missing module or class name")
        
        # 读取 project.ini 获取全局数据配置，例如 output_dir
        project_config_path = os.path.join(project_root, "project", "project.ini")
        project_config = configparser.ConfigParser()
        project_config.read(project_config_path, encoding='utf-8')
        
        data_output_dir = None
        if 'Data' in project_config and 'output_dir' in project_config['Data']:
            data_output_dir = project_config['Data']['output_dir']
            logger.debug(f"Found data output_dir in project.ini: '{data_output_dir}'")

        # 准备传递给插件的额外参数
        plugin_kwargs = {}
        if data_output_dir:
            plugin_kwargs['output_dir'] = data_output_dir
        plugin_kwargs.update(kwargs) # 合并传入的 kwargs

        try:
            # 动态导入模块
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)
            
            # 获取插件类
            logger.debug(f"Getting class: {class_name} from module: {module_name}")
            plugin_class = getattr(module, class_name)
            
            # 创建插件实例，传递 plugin_config 和额外的 kwargs
            logger.info(f"Creating plugin instance: {module_name}.{class_name} with kwargs: {plugin_kwargs}")
            plugin = plugin_class(plugin_config, **plugin_kwargs)
            return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_name}.{class_name}: {e}")
            raise
    
    @staticmethod
    def load_plugins_from_config(config_manager, plugin_manager: PluginManager, project_root: str):
        """根据配置管理器直接加载所有启用的插件"""
        try:
            # 获取项目插件配置
            project_plugins_config = config_manager.get_project_plugins_config()
        except Exception as e:
            logger.warning(f"Failed to get project plugin config: {e}")
            return
        
        # 遍历所有插件配置
        for plugin_name, plugin_config in project_plugins_config.plugins.items():
            try:
                # 如果插件被禁用，跳过
                if not plugin_config.enabled:
                    logger.debug(f"Plugin '{plugin_name}' is disabled, skipping")
                    continue
                
                # 直接加载插件，传递 project_root
                plugin = DirectPluginLoader.load_plugin(plugin_config, project_root)
                
                # 注册插件
                plugin_manager.register_plugin(plugin)
                
            except Exception as e:
                logger.error(f"Warning: Failed to load plugin '{plugin_name}': {e}")
