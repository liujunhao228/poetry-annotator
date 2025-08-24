# 插件适配器测试

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.plugin_system.adapters.query_adapter import QueryPluginAdapter
from src.plugin_system.adapters.preprocessing_adapter import PreprocessingPluginAdapter
from src.plugin_system.adapters.prompt_adapter import PromptPluginAdapter
from src.plugin_system.adapters.label_parser_adapter import LabelParserPluginAdapter
from src.plugin_system.adapters.db_init_adapter import DatabaseInitPluginAdapter
from src.config.schema import PluginConfig


class TestQueryPluginAdapter(unittest.TestCase):
    """测试查询插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "src.data.plugin_interface"
        self.plugin_config.class_name = "QueryPlugin"
        self.plugin_config.settings = {
            "name": "test_query",
            "description": "Test query plugin"
        }
    
    @patch('src.plugin_system.adapters.query_adapter.__import__')
    def test_query_plugin_adapter_creation(self, mock_import):
        """测试查询插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "test_query"
        mock_plugin_instance.get_description.return_value = "Test query plugin"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.QueryPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = QueryPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "test_query")
        self.assertEqual(adapter.get_description(), "Test query plugin")


class TestPreprocessingPluginAdapter(unittest.TestCase):
    """测试预处理插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "src.data_cleaning.manager"
        self.plugin_config.class_name = "DataCleaningManager"
        self.plugin_config.settings = {
            "name": "test_preprocessing",
            "description": "Test preprocessing plugin"
        }
    
    @patch('src.plugin_system.adapters.preprocessing_adapter.__import__')
    def test_preprocessing_plugin_adapter_creation(self, mock_import):
        """测试预处理插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name = Mock(return_value="test_preprocessing")
        mock_plugin_instance.get_description = Mock(return_value="Test preprocessing plugin")
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.DataCleaningManager = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = PreprocessingPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "test_preprocessing")
        self.assertEqual(adapter.get_description(), "Test preprocessing plugin")


class TestPromptPluginAdapter(unittest.TestCase):
    """测试Prompt插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "src.prompt.default_plugin"
        self.plugin_config.class_name = "DefaultPromptBuilderPlugin"
        self.plugin_config.settings = {
            "name": "test_prompt",
            "description": "Test prompt plugin"
        }
    
    @patch('src.plugin_system.adapters.prompt_adapter.__import__')
    def test_prompt_plugin_adapter_creation(self, mock_import):
        """测试Prompt插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "test_prompt"
        mock_plugin_instance.get_description.return_value = "Test prompt plugin"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.DefaultPromptBuilderPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = PromptPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "test_prompt")
        self.assertEqual(adapter.get_description(), "Test prompt plugin")


class TestLabelParserPluginAdapter(unittest.TestCase):
    """测试标签解析插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "src.data.label_parser_plugin_interface"
        self.plugin_config.class_name = "LabelParserPlugin"
        self.plugin_config.settings = {
            "name": "test_label_parser",
            "description": "Test label parser plugin"
        }
    
    @patch('src.plugin_system.adapters.label_parser_adapter.__import__')
    def test_label_parser_plugin_adapter_creation(self, mock_import):
        """测试标签解析插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "test_label_parser"
        mock_plugin_instance.get_description.return_value = "Test label parser plugin"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.LabelParserPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = LabelParserPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "test_label_parser")
        self.assertEqual(adapter.get_description(), "Test label parser plugin")


class TestDatabaseInitPluginAdapter(unittest.TestCase):
    """测试数据库初始化插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "src.db_initializer.plugin_interface"
        self.plugin_config.class_name = "DatabaseInitPlugin"
        self.plugin_config.settings = {
            "name": "test_db_init",
            "description": "Test database init plugin"
        }
    
    @patch('src.plugin_system.adapters.db_init_adapter.__import__')
    def test_database_init_plugin_adapter_creation(self, mock_import):
        """测试数据库初始化插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "test_db_init"
        mock_plugin_instance.get_description.return_value = "Test database init plugin"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.DatabaseInitPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = DatabaseInitPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "test_db_init")
        self.assertEqual(adapter.get_description(), "Test database init plugin")


if __name__ == '__main__':
    unittest.main()