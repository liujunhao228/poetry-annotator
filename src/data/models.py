"""
数据模型定义模块
此模块通过插件系统动态生成数据模型类
"""
import logging
from typing import Dict, Any, List, Optional, Type
from src.data.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def set_plugin_manager(plugin_manager: PluginManager):
    """设置插件管理器"""
    global _plugin_manager
    _plugin_manager = plugin_manager


def get_model_class(model_name: str, plugin_type: str = "data_model_definition") -> Optional[Type]:
    """获取模型类
    
    Args:
        model_name: 模型名称
        plugin_type: 插件类型，默认为"data_model_definition"
        
    Returns:
        模型类或None
    """
    if _plugin_manager is None:
        raise RuntimeError("插件管理器未初始化，请先调用set_plugin_manager")
    
    # 首先尝试通过指定的插件类型获取
    if plugin_type != "data_model_definition":
        model_class = _plugin_manager.get_model_class_by_type(plugin_type, plugin_type, model_name)
        if model_class:
            return model_class
    
    # 如果失败，回退到默认的data_model_definition插件
    return _plugin_manager.get_model_class("data_model_definition", model_name)


def create_model_instance(model_name: str, data: Dict[str, Any], plugin_type: str = "data_model_definition"):
    """创建模型实例
    
    Args:
        model_name: 模型名称
        data: 模型数据
        plugin_type: 插件类型，默认为"data_model_definition"
        
    Returns:
        模型实例
    """
    if _plugin_manager is None:
        raise RuntimeError("插件管理器未初始化，请先调用set_plugin_manager")
    
    # 首先尝试通过指定的插件类型创建
    if plugin_type != "data_model_definition":
        # 尝试通过插件管理器的通用方法获取插件
        specific_plugin = _plugin_manager.get_plugin(plugin_type)
        if specific_plugin and hasattr(specific_plugin, 'create_model_instance'):
            try:
                return specific_plugin.create_model_instance(model_name, data)
            except Exception as e:
                logger.error(f"Error calling create_model_instance on specific plugin '{plugin_type}': {e}")
                return None

    # 如果失败，回退到默认的data_model_definition插件
    data_model_plugin = _plugin_manager.get_plugin("data_model_definition")
    if data_model_plugin and hasattr(data_model_plugin, 'create_model_instance'):
        try:
            return data_model_plugin.create_model_instance(model_name, data)
        except Exception as e:
            logger.error(f"Error calling create_model_instance on default data_model_definition plugin: {e}")
            return None
    else:
        logger.error("DataModelDefinitionPlugin not found or lacks create_model_instance method.")
        return None


def serialize_model(model_instance, plugin_type: str = "data_model_serialization") -> Dict[str, Any]:
    """序列化模型实例
    
    Args:
        model_instance: 模型实例
        plugin_type: 插件类型，默认为"data_model_serialization"
        
    Returns:
        序列化后的字典
    """
    if _plugin_manager is None:
        raise RuntimeError("插件管理器未初始化，请先调用set_plugin_manager")
    
    model_type = type(model_instance)
    model_name = model_type.__name__
    
    # 首先尝试通过指定的插件类型序列化
    if plugin_type != "data_model_serialization":
        serialized = _plugin_manager.serialize_model_by_type(plugin_type, plugin_type, model_instance)
        if serialized:
            return serialized
    
    # 如果失败，回退到默认的data_model_serialization插件
    return _plugin_manager.serialize_model("data_model_serialization", model_instance)


def get_model_fields(model_name: str, plugin_type: str = "data_model_definition") -> List[str]:
    """获取模型字段列表
    
    Args:
        model_name: 模型名称
        plugin_type: 插件类型，默认为"data_model_definition"
        
    Returns:
        字段名称列表
    """
    if _plugin_manager is None:
        raise RuntimeError("插件管理器未初始化，请先调用set_plugin_manager")
    
    # 首先尝试通过指定的插件类型获取
    if plugin_type != "data_model_definition":
        fields = _plugin_manager.get_model_fields(plugin_type, model_name)
        if fields:
            return fields
    
    # 如果失败，回退到默认的data_model_definition插件
    return _plugin_manager.get_model_fields("data_model_definition", model_name)


# 为每个模型创建别名，以便在代码中直接使用
def Poem(*args, **kwargs):
    """诗词数据模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("Poem", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("Poem", plugin_type)

def Author(*args, **kwargs):
    """作者数据模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("Author", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("Author", plugin_type)

def StrategyCategory(*args, **kwargs):
    """策略分类模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("StrategyCategory", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("StrategyCategory", plugin_type)

def Annotation(*args, **kwargs):
    """标注数据模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("Annotation", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("Annotation", plugin_type)

def SentenceAnnotation(*args, **kwargs):
    """句子标注模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("SentenceAnnotation", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("SentenceAnnotation", plugin_type)

def SentenceStrategyLink(*args, **kwargs):
    """句子策略链接模型"""
    if args or kwargs:
        # 检查是否有plugin_type参数
        plugin_type = kwargs.pop('plugin_type', 'data_model_definition')
        return create_model_instance("SentenceStrategyLink", kwargs if not args else args[0], plugin_type)
    # 检查是否有plugin_type参数
    plugin_type = kwargs.get('plugin_type', 'data_model_definition') if kwargs else 'data_model_definition'
    return get_model_class("SentenceStrategyLink", plugin_type)
