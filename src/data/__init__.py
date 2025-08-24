"""
数据模块初始化
"""
from src.data.plugin_manager import PluginManager
from src.data.models import set_plugin_manager
from src.data.manager import get_data_manager


def initialize_data_system():
    """初始化数据系统"""
    # 获取插件管理器实例
    plugin_manager = PluginManager.get_instance()
    
    # 初始化插件
    plugin_manager.initialize_plugins()
    
    # 设置模型模块使用的插件管理器
    set_plugin_manager(plugin_manager)
    
    return plugin_manager


# 在模块导入时自动初始化
plugin_manager = initialize_data_system()