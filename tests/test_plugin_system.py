# 插件系统测试

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path

from src.plugin_system.base import BasePlugin
from src.plugin_system.plugin_types import PluginType
from src.plugin_system.manager import PluginManager
from src.plugin_system.loader import PluginLoader
from src.config.schema import PluginConfig


class TestBasePlugin(unittest.TestCase):
    """测试基础插件类"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "test_module"
        self.plugin_config.class_name = "TestClass"
        self.plugin_config.settings = {"name": "test", "description": "Test plugin"}
    
    def test_base_plugin_initialization(self):
        """测试基础插件初始化"""
        # 创建一个具体的插件实现
        class ConcretePlugin(BasePlugin):
            def get_name(self):
                return "test_plugin"
                
            def get_description(self):
                return "Test plugin for testing"
        
        plugin = ConcretePlugin(self.plugin_config)
        self.assertEqual(plugin.get_config(), self.plugin_config)
        self.assertTrue(plugin.initialize())
        self.assertTrue(plugin.cleanup())


class TestPluginManager(unittest.TestCase):
    """测试插件管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_manager = PluginManager()
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "test_module"
        self.plugin_config.class_name = "TestClass"
        self.plugin_config.settings = {"name": "test", "description": "Test plugin"}
    
    def test_plugin_registration(self):
        """测试插件注册"""
        # 创建一个模拟插件
        mock_plugin = Mock()
        mock_plugin.get_name.return_value = "test_plugin"
        mock_plugin.get_description.return_value = "Test plugin"
        
        # 注册插件
        result = self.plugin_manager.register_plugin(mock_plugin)
        self.assertTrue(result)
        
        # 验证插件已注册
        registered_plugin = self.plugin_manager.get_plugin("test_plugin")
        self.assertEqual(registered_plugin, mock_plugin)
    
    def test_duplicate_plugin_registration(self):
        """测试重复插件注册"""
        # 创建一个模拟插件
        mock_plugin1 = Mock()
        mock_plugin1.get_name.return_value = "test_plugin"
        mock_plugin1.get_description.return_value = "Test plugin 1"
        
        mock_plugin2 = Mock()
        mock_plugin2.get_name.return_value = "test_plugin"
        mock_plugin2.get_description.return_value = "Test plugin 2"
        
        # 注册第一个插件
        result1 = self.plugin_manager.register_plugin(mock_plugin1)
        self.assertTrue(result1)
        
        # 尝试注册同名插件
        result2 = self.plugin_manager.register_plugin(mock_plugin2)
        self.assertFalse(result2)
    
    def test_plugin_unregistration(self):
        """测试插件注销"""
        # 创建一个模拟插件
        mock_plugin = Mock()
        mock_plugin.get_name.return_value = "test_plugin"
        mock_plugin.get_description.return_value = "Test plugin"
        mock_plugin.cleanup.return_value = True
        
        # 注册插件
        self.plugin_manager.register_plugin(mock_plugin)
        
        # 注销插件
        result = self.plugin_manager.unregister_plugin("test_plugin")
        self.assertTrue(result)
        
        # 验证插件已注销
        registered_plugin = self.plugin_manager.get_plugin("test_plugin")
        self.assertIsNone(registered_plugin)
    
    def test_list_plugins(self):
        """测试列出插件"""
        # 创建模拟插件
        mock_plugin1 = Mock()
        mock_plugin1.get_name.return_value = "plugin1"
        mock_plugin1.get_description.return_value = "First plugin"
        
        mock_plugin2 = Mock()
        mock_plugin2.get_name.return_value = "plugin2"
        mock_plugin2.get_description.return_value = "Second plugin"
        
        # 注册插件
        self.plugin_manager.register_plugin(mock_plugin1)
        self.plugin_manager.register_plugin(mock_plugin2)
        
        # 获取插件列表
        plugins = self.plugin_manager.list_plugins()
        self.assertEqual(len(plugins), 2)
        self.assertIn("plugin1", plugins)
        self.assertIn("plugin2", plugins)
        self.assertEqual(plugins["plugin1"], "First plugin")
        self.assertEqual(plugins["plugin2"], "Second plugin")


class TestPluginTypes(unittest.TestCase):
    """测试插件类型枚举"""
    
    def test_plugin_type_creation(self):
        """测试插件类型创建"""
        # 测试从字符串创建插件类型
        query_type = PluginType.from_string("query")
        self.assertEqual(query_type, PluginType.QUERY)
        
        preprocessing_type = PluginType.from_string("preprocessing")
        self.assertEqual(preprocessing_type, PluginType.PREPROCESSING)
        
        # 测试无效类型
        with self.assertRaises(ValueError):
            PluginType.from_string("invalid_type")


if __name__ == '__main__':
    unittest.main()