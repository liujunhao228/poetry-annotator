"""
项目插件适配器测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.plugin_system.adapters.custom_query_adapter import CustomQueryPluginAdapter
from src.plugin_system.adapters.social_emotion_adapter import HardcodedSocialEmotionCategoriesPluginAdapter
from src.plugin_system.adapters.db_initializer_adapter import SocialPoemAnalysisDBInitializerAdapter
from src.plugin_system.adapters.social_prompt_adapter import SocialAnalysisPromptBuilderPluginAdapter
from src.config.schema import PluginConfig


class TestCustomQueryPluginAdapter(unittest.TestCase):
    """测试自定义查询插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "project.plugins.data.custom_query_plugin"
        self.plugin_config.class_name = "CustomQueryPlugin"
        self.plugin_config.settings = {
            "name": "custom_query",
            "description": "自定义查询插件"
        }
    
    @patch('src.plugin_system.adapters.custom_query_adapter.__import__')
    def test_custom_query_plugin_adapter_creation(self, mock_import):
        """测试自定义查询插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "custom_query"
        mock_plugin_instance.get_description.return_value = "自定义查询插件"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.CustomQueryPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = CustomQueryPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "custom_query")
        self.assertEqual(adapter.get_description(), "自定义查询插件")


class TestSocialEmotionPluginAdapter(unittest.TestCase):
    """测试社交情感插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "project.plugins.data.hardcoded_social_emotion_categories"
        self.plugin_config.class_name = "HardcodedSocialEmotionCategoriesPlugin"
        self.plugin_config.settings = {
            "name": "social_emotion_categories",
            "description": "《交际诗分析》项目专用硬编码情感分类信息"
        }
    
    @patch('src.plugin_system.adapters.social_emotion_adapter.__import__')
    def test_social_emotion_plugin_adapter_creation(self, mock_import):
        """测试社交情感插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "social_emotion_categories"
        mock_plugin_instance.get_description.return_value = "《交际诗分析》项目专用硬编码情感分类信息"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.HardcodedSocialEmotionCategoriesPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = HardcodedSocialEmotionCategoriesPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "social_emotion_categories")
        self.assertEqual(adapter.get_description(), "《交际诗分析》项目专用硬编码情感分类信息")


class TestSocialDBInitPluginAdapter(unittest.TestCase):
    """测试社交数据库初始化插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "project.plugins.db_initializer.db_initializer_plugin"
        self.plugin_config.class_name = "SocialPoemAnalysisDBInitializer"
        self.plugin_config.settings = {
            "name": "social_db_init",
            "description": "《交际诗分析》项目数据库初始化插件"
        }
    
    @patch('src.plugin_system.adapters.db_initializer_adapter.__import__')
    def test_social_db_init_plugin_adapter_creation(self, mock_import):
        """测试社交数据库初始化插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "social_db_init"
        mock_plugin_instance.get_description.return_value = "《交际诗分析》项目数据库初始化插件"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.SocialPoemAnalysisDBInitializer = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = SocialPoemAnalysisDBInitializerAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "social_db_init")
        self.assertEqual(adapter.get_description(), "《交际诗分析》项目数据库初始化插件")


class TestSocialPromptPluginAdapter(unittest.TestCase):
    """测试社交Prompt插件适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "project.plugins.prompt.social_prompt_plugin"
        self.plugin_config.class_name = "SocialAnalysisPromptBuilderPlugin"
        self.plugin_config.settings = {
            "name": "social_prompt",
            "description": "《交际诗分析》项目专用Prompt构建插件"
        }
    
    @patch('src.plugin_system.adapters.social_prompt_adapter.__import__')
    def test_social_prompt_plugin_adapter_creation(self, mock_import):
        """测试社交Prompt插件适配器创建"""
        # 创建模拟的插件类
        mock_plugin_class = Mock()
        mock_plugin_instance = Mock()
        mock_plugin_instance.get_name.return_value = "social_prompt"
        mock_plugin_instance.get_description.return_value = "《交际诗分析》项目专用Prompt构建插件"
        mock_plugin_class.return_value = mock_plugin_instance
        
        # 设置模拟导入
        mock_module = Mock()
        mock_module.SocialAnalysisPromptBuilderPlugin = mock_plugin_class
        mock_import.return_value = mock_module
        
        # 创建适配器
        adapter = SocialAnalysisPromptBuilderPluginAdapter(self.plugin_config)
        
        # 验证适配器属性
        self.assertEqual(adapter.get_name(), "social_prompt")
        self.assertEqual(adapter.get_description(), "《交际诗分析》项目专用Prompt构建插件")


if __name__ == '__main__':
    unittest.main()