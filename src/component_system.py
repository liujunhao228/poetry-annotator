"""
组件系统模块，负责管理严格的组件类型机制

该模块实现了更加严格和明确的组件类型机制，解决了以下问题：
1. 使用枚举确保组件类型的安全性
2. 过滤插件配置参数，防止元数据传递给构造函数
3. 基于插件类型而非名称查找插件
4. 提供清晰的错误处理和日志记录

主要类：
- ComponentType: 组件类型枚举
- Component: 组件基类
- ComponentSystem: 组件系统核心类
"""

import importlib
import logging
from typing import Dict, Any, Optional, Type, Union
from src.config.plugin_loader import ProjectPluginConfigLoader
from src.config.schema import PluginConfig
# 导入新的插件系统
from src.plugin_system import get_plugin_manager, PluginLoader
from src.plugin_system.plugin_types import PluginType
from src.plugin_system.base import ComponentType, Component, BasePlugin # Import from base.py

# 配置日志
logger = logging.getLogger(__name__)


class Plugin(BasePlugin): # Inherit from BasePlugin
    """插件基类"""
    def __init__(self, component_type: ComponentType, plugin_config: PluginConfig):
        super().__init__(plugin_config) # Call BasePlugin's constructor
        self.component_type = component_type # Add component_type attribute
    
    def get_name(self) -> str:
        """获取插件名称"""
        # Assuming plugin_config has a name, or derive it
        return self.plugin_config.name if self.plugin_config.name else "Unnamed Plugin"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self.plugin_config.description if self.plugin_config.description else "No description provided."
    
    def initialize(self):
        """插件初始化方法"""
        super().initialize() # Call BasePlugin's initialize
    
    def cleanup(self):
        """插件清理方法"""
        super().cleanup() # Call BasePlugin's cleanup


class ComponentSystem:
    """组件系统，负责严格管理组件类型和实例化"""
    
    def __init__(self, project_root):
        # 确保 project_root 是 Path 对象
        from pathlib import Path
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self._plugin_configs: Dict[str, PluginConfig] = {}
        self._component_registry: Dict[ComponentType, Type[Component]] = {}
        # 使用全局插件管理器
        self.plugin_manager = get_plugin_manager()
        self._load_plugin_configs()
        self._register_default_components()
        
    def _load_plugin_configs(self):
        """加载所有已启用的项目插件配置"""
        try:
            project_plugins_ini_path = self.project_root / "project" / "plugins.ini"
            
            if project_plugins_ini_path.exists():
                try:
                    project_plugin_loader = ProjectPluginConfigLoader(str(project_plugins_ini_path))
                    project_plugin_config: ProjectPluginsConfig = project_plugin_loader.load_project_plugin_config()
                    project_enabled_plugins = project_plugin_config.enabled_plugins
                    
                    logger.info(f"项目插件配置加载完成，启用的插件: {project_enabled_plugins}")
                    logger.info(f"插件路径: {project_plugin_config.plugin_paths}")
                    
                    # 为项目插件添加 plugin_paths 到 sys.path
                    import sys
                    for plugin_path in project_plugin_config.plugin_paths:
                        # 处理相对路径和绝对路径
                        if plugin_path.startswith("project/"):
                            # 如果是project开头的路径，直接使用
                            full_plugin_path = str(self.project_root / plugin_path)
                        else:
                            # 其他路径在project目录下查找
                            full_plugin_path = str(self.project_root / "project" / plugin_path)
                        if full_plugin_path not in sys.path:
                            sys.path.insert(0, full_plugin_path)
                            logger.debug(f"已将项目插件路径添加到 sys.path: {full_plugin_path}")
                    
                    for plugin_name in project_enabled_plugins:
                        try:
                            plugin_config: PluginConfig = project_plugin_loader.load_plugin_config(plugin_name)
                            logger.info(f"加载插件配置: {plugin_name}, enabled: {plugin_config.enabled}")
                            if plugin_config.enabled:
                                self._plugin_configs[plugin_name] = plugin_config
                                logger.info(f"成功加载并启用项目插件配置: {plugin_name}")
                            else:
                                logger.info(f"项目插件配置已加载但未启用: {plugin_name}")
                        except Exception as e:
                            logger.error(f"加载项目插件 '{plugin_name}' 的配置时出错: {e}")
                    
                    # 使用新的插件加载器加载所有启用的插件
                    from src.plugin_system.project_config_manager import ProjectPluginConfigManager
                    config_manager = ProjectPluginConfigManager(self._plugin_configs)
                    PluginLoader.load_plugins_from_config(config_manager, self.plugin_manager, self.project_root)                    # 注册项目插件到新的插件系统
                    from src.plugin_system.project_plugins import register_project_plugins
                    register_project_plugins(self.plugin_manager, self._plugin_configs)
                except Exception as e:
                    logger.error(f"加载项目插件配置时出错: {e}")
            else:
                logger.warning(f"项目插件配置文件不存在: {project_plugins_ini_path}。将不加载任何项目插件。")
        except Exception as e:
            logger.error(f"加载插件配置时出错: {e}")
    
    def _register_default_components(self):
        """注册默认组件"""
        # 这里可以注册默认组件类
        pass
        
    def get_component(self, component_type: Union[str, ComponentType], **kwargs) -> Union[Component, object]:
        """
        工厂方法：根据插件配置获取组件实例。
        
        Args:
            component_type: 组件类型字符串或枚举。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            组件实例（可能是插件实例，也可能是默认实例）。
        """
        # 确保组件类型是枚举类型
        if isinstance(component_type, str):
            try:
                component_type = ComponentType.from_string(component_type)
            except ValueError as e:
                logger.error(f"无效的组件类型: {component_type}")
                raise
        
        # 首先检查是否已存在缓存实例
        if component_type in self._component_registry:
            logger.debug(f"从缓存中获取 {component_type.value} 组件实例。")
            return self._component_registry[component_type]

        instance = None
        # 查找插件配置
        plugin_config = self._find_plugin_config_by_type(component_type)
        
        if plugin_config and plugin_config.enabled:
            try:
                logger.debug(f"尝试加载 {component_type.value} 插件: {plugin_config.module}.{plugin_config.class_name}")
                
                # 动态导入模块
                module = importlib.import_module(plugin_config.module)
                # 获取类
                plugin_class = getattr(module, plugin_config.class_name)
                
                # 过滤掉插件配置中不应该传递给构造函数的参数
                init_kwargs = ComponentSystem._filter_plugin_init_kwargs(plugin_config.settings, kwargs)
                
                # 创建实例
                instance = plugin_class(**init_kwargs)
                logger.info(f"成功创建 {component_type.value} 插件实例: {plugin_config.module}.{plugin_config.class_name}")
                
            except Exception as e:
                logger.error(f"加载 {component_type.value} 插件 '{plugin_config.module}.{plugin_config.class_name}' 失败: {e}")
                # 记录错误但不中断，回退到默认实现
        
        if instance is None:
            # 回退到默认实现
            logger.info(f"未找到启用的 {component_type.value} 插件，使用默认实现。")
            instance = self._get_default_component(component_type, **kwargs)
        
        # 缓存实例
        self._component_registry[component_type] = instance
        return instance
    
    def _find_plugin_config_by_type(self, component_type: ComponentType) -> Optional[PluginConfig]:
        """
        根据组件类型查找插件配置
        
        Args:
            component_type: 组件类型枚举
            
        Returns:
            匹配的插件配置或None
        """
        # 首先检查是否有专门针对该类型的插件
        for plugin_name, plugin_config in self._plugin_configs.items():
            if plugin_config.settings.get('type') == component_type.value:
                return plugin_config
        
        # 如果没有找到专门的插件，检查是否有统一插件可以处理该类型
        # 统一插件的类型为 'social_poem_analysis'
        for plugin_name, plugin_config in self._plugin_configs.items():
            if plugin_config.settings.get('type') == 'social_poem_analysis':
                return plugin_config
                
        return None
    
    @staticmethod
    def _filter_plugin_init_kwargs(plugin_settings: Dict[str, Any], user_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤插件配置参数，移除不应该传递给构造函数的参数
        
        Args:
            plugin_settings: 插件配置设置
            user_kwargs: 用户传入的参数
            
        Returns:
            过滤后的参数字典
        """
        # 定义不应传递给构造函数的参数
        excluded_keys = {'type', 'module', 'class'}
        
        # 过滤插件设置
        filtered_settings = {k: v for k, v in plugin_settings.items() if k not in excluded_keys}
        
        # 合并用户参数（优先级更高）
        init_kwargs = {**filtered_settings, **user_kwargs}
        
        return init_kwargs
    
    def _get_default_component(self, component_type: ComponentType, **kwargs):
        """
        获取默认组件实例。
        
        Args:
            component_type: 组件类型枚举。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            默认组件实例。
        """
        if component_type == ComponentType.DATA_MANAGER:
            # 延迟导入以避免循环依赖
            from src.data import get_data_manager
            db_name = kwargs.get('db_name', 'default')
            return get_data_manager(db_name)
        elif component_type == ComponentType.ANNOTATOR:
            # 延迟导入以避免循环依赖
            from src.annotator import Annotator
            model_config_name = kwargs.get('model_config_name')
            if not model_config_name:
                raise ValueError("创建默认 Annotator 需要提供 'model_config_name' 参数。")
            return Annotator(model_config_name)
        elif component_type == ComponentType.PREPROCESSING:
            # 延迟导入以避免循环依赖
            from src.data_cleaning import DataCleaningManager
            # 获取当前项目的配置路径
            from src.config.manager import get_config_manager
            config_manager = get_config_manager()
            global_config_path = config_manager.global_config_path
            project_config_path = config_manager.project_config_path
            return DataCleaningManager(global_config_path, project_config_path)
        elif component_type in [ComponentType.DATA_STORAGE, ComponentType.DATA_QUERY, 
                               ComponentType.DATA_PROCESSING, ComponentType.ANNOTATION_MANAGEMENT]:
            # 对于数据相关的组件类型，如果没有找到插件，应该直接创建DataManager实例
            # 注意：不能通过get_data_manager函数获取，因为这会导致循环依赖
            from src.data.manager import DataManager
            db_name = kwargs.get('db_name', 'default')
            return DataManager(db_name=db_name)
        elif component_type == ComponentType.RESPONSE_VALIDATOR:
            # 延迟导入以避免循环依赖
            from src.response_validation.manager import ResponseValidationManager as ResponseValidator
            return ResponseValidator()
        elif component_type == ComponentType.LABEL_PARSER:
            # 延迟导入以避免循环依赖
            from src.emotion_classifier import EmotionClassifier
            project_root = kwargs.get('project_root', self.project_root)
            if ComponentType.LABEL_PARSER not in self._component_registry:
                self._component_registry[ComponentType.LABEL_PARSER] = EmotionClassifier(project_root=project_root)
            return self._component_registry[ComponentType.LABEL_PARSER]
        else:
            raise ValueError(f"未知的组件类型: {component_type.value}")
# 全局组件系统实例
component_system = None

def get_component_system(project_root):
    """获取全局组件系统实例"""
    global component_system
    if component_system is None:
        component_system = ComponentSystem(project_root)
    return component_system
