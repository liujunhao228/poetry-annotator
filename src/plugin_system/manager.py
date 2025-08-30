"""
插件管理器实现
"""

import logging
from typing import Dict, Any, Optional
from src.plugin_system.base import BasePlugin

# 配置日志
logger = logging.getLogger(__name__)

# 全局插件管理器实例
_plugin_manager_instance: Optional['PluginManager'] = None


def get_plugin_manager() -> 'PluginManager':
    """获取全局插件管理器实例"""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance


class PluginManager:
    """统一插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """注册插件"""
        plugin_name = plugin.get_name()
        if plugin_name in self.plugins:
            self.logger.warning(f"Plugin '{plugin_name}' already registered")
            return False
        
        self.plugins[plugin_name] = plugin
        self.logger.info(f"Plugin registered: {plugin_name}")
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name in self.plugins:
            # 先清理插件资源
            plugin = self.plugins[plugin_name]
            try:
                plugin.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")
            
            del self.plugins[plugin_name]
            self.logger.info(f"Plugin unregistered: {plugin_name}")
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def initialize_all_plugins(self) -> Dict[str, bool]:
        """初始化所有插件"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                results[name] = plugin.initialize()
            except Exception as e:
                self.logger.error(f"Error initializing plugin '{name}': {e}")
                results[name] = False
        return results
    
    def cleanup_all_plugins(self) -> Dict[str, bool]:
        """清理所有插件资源"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                results[name] = plugin.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin '{name}': {e}")
                results[name] = False
        return results
    
    def get_plugins_by_type(self, plugin_type: str) -> Dict[str, BasePlugin]:
        """根据类型获取插件"""
        result = {}
        for name, plugin in self.plugins.items():
            # 获取插件配置中的类型信息
            config = plugin.get_config()
            if config.settings.get('type') == plugin_type:
                result[name] = plugin
        return result
        
    def get_plugin_by_type(self, plugin_type: str) -> Optional[BasePlugin]:
        """根据类型获取单个插件实例"""
        plugins = self.get_plugins_by_type(plugin_type)
        if plugins:
            # 返回第一个匹配的插件
            return next(iter(plugins.values()))
        return None