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
from enum import Enum
from src.config.plugin_loader import ProjectPluginConfigLoader
from src.config.schema import GlobalPluginConfig, PluginConfig
# 导入新的插件系统
from src.plugin_system import get_plugin_manager, PluginLoader
from src.plugin_system.plugin_types import PluginType

# 配置日志
logger = logging.getLogger(__name__)

# 定义严格的组件类型枚举
class ComponentType(Enum):
    """组件类型枚举，确保类型安全"""
    ANNOTATOR = "annotator"
    DATA_MANAGER = "data_manager"
    QUERY_BUILDER = "query_builder"
    PROMPT_BUILDER = "prompt_builder"
    DB_INITIALIZER = "db_initializer"
    LABEL_PARSER = "label_parser"
    CUSTOM_QUERY = "custom_query"
    PREPROCESSING = "preprocessing"
    # 数据相关插件类型
    DATA_STORAGE = "data_storage"
    DATA_QUERY = "data_query"
    DATA_PROCESSING = "data_processing"
    ANNOTATION_MANAGEMENT = "annotation_management"
    DATA_MODEL_DEFINITION = "data_model_definition"
    
    @classmethod
    def from_string(cls, value: str) -> 'ComponentType':
        """从字符串创建组件类型"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"未知的组件类型: {value}")

# 定义组件接口
class Component:
    """组件基类"""
    def __init__(self, component_type: ComponentType):
        self.component_type = component_type
    
    def get_type(self) -> ComponentType:
        """获取组件类型"""
        return self.component_type


class Plugin(Component):
    """插件基类"""
    def __init__(self, component_type: ComponentType, plugin_config: PluginConfig):
        super().__init__(component_type)
        self.plugin_config = plugin_config
    
    def get_name(self) -> str:
        """获取插件名称"""
        raise NotImplementedError("插件必须实现get_name方法")
    
    def get_description(self) -> str:
        """获取插件描述"""
        raise NotImplementedError("插件必须实现get_description方法")
    
    def initialize(self):
        """插件初始化方法"""
        pass
    
    def cleanup(self):
        """插件清理方法"""
        pass


class ComponentSystem:
    """组件系统，负责严格管理组件类型和实例化"""
    
    def __init__(self, project_root):
        self.project_root = project_root
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
                    project_plugin_config: GlobalPluginConfig = project_plugin_loader.load_project_plugin_config()
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
                    from src.config.manager import get_config_manager
                    config_manager = get_config_manager()
                    PluginLoader.load_plugins_from_config(config_manager, self.plugin_manager)
                    
                    # 注册项目插件到新的插件系统
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
                
                # 如果是统一插件，传递组件类型信息
                # 注意：新的SocialPoemAnalysisPlugin构造函数不再接受component_type参数
                # if plugin_config.settings.get('type') == 'social_poem_analysis':
                #     init_kwargs['component_type'] = component_type.value
                
                # 创建实例
                instance = plugin_class(**init_kwargs)
                logger.info(f"成功创建 {component_type.value} 插件实例: {plugin_config.module}.{plugin_config.class_name}")
                return instance
                
            except Exception as e:
                logger.error(f"加载 {component_type.value} 插件 '{plugin_config.module}.{plugin_config.class_name}' 失败: {e}")
                # 记录错误但不中断，回退到默认实现
        
        # 回退到默认实现
        logger.info(f"未找到启用的 {component_type.value} 插件，使用默认实现。")
        return self._get_default_component(component_type, **kwargs)
    
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