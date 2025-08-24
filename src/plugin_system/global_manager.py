"""
全局插件管理器实例
"""

from .manager import PluginManager

# 全局插件管理器实例
plugin_manager = PluginManager()

def get_plugin_manager():
    """获取全局插件管理器实例"""
    return plugin_manager