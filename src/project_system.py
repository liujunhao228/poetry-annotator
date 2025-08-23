"""项目系统模块，负责协调插件、数据管理和标注流程"""

import os
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, Union
from src.config import config_manager
from src.annotator import Annotator
from src.data import get_data_manager

# 配置日志
logger = logging.getLogger(__name__)

# 定义组件类型常量，用于 get_component 方法
COMPONENT_ANNOTATOR = "annotator"
COMPONENT_DATA_MANAGER = "data_manager"

class ProjectSystem:
    """项目系统，负责与插件系统交互并管理标注流程"""
    
    def __init__(self):
        """初始化项目系统，加载插件配置"""
        self.config = config_manager
        self._plugin_configs = {}
        self._load_plugin_configs()
        
    def _load_plugin_configs(self):
        """加载所有已启用的插件配置"""
        try:
            # 首先加载全局插件配置（为了兼容性）
            try:
                global_plugin_config = self.config.get_global_plugin_config()
                enabled_plugins = global_plugin_config.enabled_plugins
                
                for plugin_name in enabled_plugins:
                    try:
                        plugin_config = self.config.get_plugin_config(plugin_name)
                        if plugin_config.enabled:
                            self._plugin_configs[plugin_name] = plugin_config
                            logger.info(f"成功加载并启用全局插件配置: {plugin_name}")
                        else:
                            logger.debug(f"全局插件 '{plugin_name}' 在配置中被禁用。")
                    except Exception as e:
                        logger.error(f"加载全局插件 '{plugin_name}' 的配置时出错: {e}")
            except Exception as e:
                logger.warning(f"加载全局插件配置时出错（可能没有配置）: {e}")
            
            # 然后加载项目插件配置
            plugins_dir = Path("project")
            plugin_ini_path = plugins_dir / "plugins.ini"
            if plugin_ini_path.exists():
                try:
                    # 为项目插件创建一个独立的配置管理器
                    from src.config.manager import ConfigManager
                    project_config_manager = ConfigManager(str(plugin_ini_path))
                    project_plugin_config = project_config_manager.get_global_plugin_config()
                    project_enabled_plugins = project_plugin_config.enabled_plugins
                    
                    for plugin_name in project_enabled_plugins:
                        try:
                            plugin_config = project_config_manager.get_plugin_config(plugin_name)
                            if plugin_config.enabled:
                                self._plugin_configs[plugin_name] = plugin_config
                                logger.info(f"成功加载并启用项目插件配置: {plugin_name}")
                            else:
                                logger.debug(f"项目插件 '{plugin_name}' 在配置中被禁用。")
                        except Exception as e:
                            logger.error(f"加载项目插件 '{plugin_name}' 的配置时出错: {e}")
                except Exception as e:
                    logger.error(f"加载项目插件配置时出错: {e}")
        except Exception as e:
            logger.error(f"加载插件配置时出错: {e}")

    def get_component(self, component_type: str, **kwargs) -> Union[Annotator, object]:
        """
        工厂方法：根据插件配置获取组件实例。
        
        Args:
            component_type: 组件类型字符串 (例如 'annotator', 'data_manager')。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            组件实例（可能是插件实例，也可能是默认实例）。
        """
        # 查找插件配置
        plugin_config = self._plugin_configs.get(component_type)
        
        if plugin_config and plugin_config.enabled:
            try:
                logger.debug(f"尝试加载 {component_type} 插件: {plugin_config.module}.{plugin_config.class_name}")
                
                # 为项目插件添加 project 目录到 sys.path
                import sys
                plugins_dir = "project"
                if plugins_dir not in sys.path:
                    sys.path.insert(0, plugins_dir)
                    logger.debug(f"已将 project 目录添加到 sys.path: {plugins_dir}")
                
                # 动态导入模块
                module = importlib.import_module(plugin_config.module)
                # 获取类
                plugin_class = getattr(module, plugin_config.class_name)
                
                # 合并插件配置和传入的参数
                # 传入的 kwargs 优先级更高
                init_kwargs = {**plugin_config.settings, **kwargs}
                
                # 创建实例
                instance = plugin_class(**init_kwargs)
                logger.info(f"成功创建 {component_type} 插件实例: {plugin_config.module}.{plugin_config.class_name}")
                return instance
                
            except Exception as e:
                logger.error(f"加载 {component_type} 插件 '{plugin_config.module}.{plugin_config.class_name}' 失败: {e}")
                # 记录错误但不中断，回退到默认实现
        
        # 回退到默认实现
        logger.info(f"未找到启用的 {component_type} 插件，使用默认实现。")
        return self._get_default_component(component_type, **kwargs)
    
    def _get_default_component(self, component_type: str, **kwargs):
        """
        获取默认组件实例。
        
        Args:
            component_type: 组件类型。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            默认组件实例。
        """
        if component_type == COMPONENT_ANNOTATOR:
            model_config_name = kwargs.get('model_config_name')
            if not model_config_name:
                raise ValueError("创建默认 Annotator 需要提供 'model_config_name' 参数。")
            return Annotator(model_config_name)
            
        elif component_type == COMPONENT_DATA_MANAGER:
            db_name = kwargs.get('db_name', 'default')
            return get_data_manager(db_name)
            
        else:
            raise ValueError(f"未知的组件类型: {component_type}")

    # --- 任务执行方法 (待实现) ---
    async def run_annotation_task(self, 
                                  model_config_name: str,
                                  limit: Optional[int] = None,
                                  start_id: Optional[int] = None,
                                  end_id: Optional[int] = None,
                                  force_rerun: bool = False,
                                  poem_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        运行标注任务 (占位符)
        """
        # TODO: 实现具体的任务执行逻辑
        pass

# 全局项目系统实例
project_system = ProjectSystem()