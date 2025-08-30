"""
社交诗分析统一插件测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path
import json
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from project.plugins.data.social_poem_analysis_plugin import SocialPoemAnalysisPlugin
from src.config.schema import PluginConfig
from src.llm_services.schemas import PoemData, EmotionSchema


class TestSocialPoemAnalysisPlugin(unittest.TestCase):
    """测试社交诗分析统一插件"""

    def setUp(self):
        """设置测试环境"""
        self.plugin_config = PluginConfig()
        self.plugin_config.module = "project.plugins.data.social_poem_analysis_plugin"
        self.plugin_config.class_name = "SocialPoemAnalysisPlugin"
        self.plugin_config.settings = {
            "name": "social_poem_analysis",
            "description": "《交际诗分析》项目统一插件，集成数据查询、Prompt构建、标签解析和数据库初始化功能"
        }
        
        # 创建插件实例
        self.plugin = SocialPoemAnalysisPlugin(self.plugin_config)

    def test_plugin_initialization(self):
        """测试插件初始化"""
        # 验证插件属性
        self.assertEqual(self.plugin.get_name(), "social_poem_analysis")
        self.assertEqual(self.plugin.get_description(), "《交际诗分析》项目统一插件，集成数据查询、Prompt构建、标签解析和数据库初始化功能")
        
        # 验证情感分类体系已加载
        categories = self.plugin.get_categories()
        self.assertIn("relationship_action", categories)
        self.assertIn("emotional_strategy", categories)
        self.assertIn("communication_scene", categories)
        self.assertIn("risk_level", categories)

    def test_query_plugin_interface(self):
        """测试查询插件接口"""
        # 测试execute_query方法
        result = self.plugin.execute_query()
        self.assertIsInstance(result, pd.DataFrame)
        
        # 测试get_required_params方法
        required_params = self.plugin.get_required_params()
        self.assertIsInstance(required_params, list)

    def test_prompt_builder_plugin_interface(self):
        """测试Prompt构建插件接口"""
        # 创建测试数据
        poem_data = PoemData(
            id=1,
            author="李白",
            title="静夜思",
            paragraphs=["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        )
        
        emotion_schema = EmotionSchema(
            text="测试情感体系"
        )
        
        model_config = {
            "model_name": "test_model"
        }
        
        # 测试build_prompts方法
        system_prompt, user_prompt = self.plugin.build_prompts(poem_data, emotion_schema, model_config)
        
        # 验证返回值类型
        self.assertIsInstance(system_prompt, str)
        self.assertIsInstance(user_prompt, str)
        
        # 验证提示词内容包含关键信息
        self.assertIn("关系动作", system_prompt)
        self.assertIn("情感策略", system_prompt)
        self.assertIn("传播场景", system_prompt)
        self.assertIn("风险等级", system_prompt)
        self.assertIn("李白", user_prompt)
        self.assertIn("静夜思", user_prompt)

    def test_label_parser_plugin_interface(self):
        """测试标签解析插件接口"""
        # 测试get_categories方法
        categories = self.plugin.get_categories()
        self.assertIsInstance(categories, dict)
        self.assertGreater(len(categories), 0)
        
        # 验证分类体系结构
        for category_id, category_data in categories.items():
            self.assertIn("id", category_data)
            self.assertIn("name_zh", category_data)
            self.assertIn("name_en", category_data)
            self.assertIn("description", category_data)
            self.assertIn("categories", category_data)
            self.assertIsInstance(category_data["categories"], list)
        
        # 测试extend_category_data方法
        base_categories = {
            "test_category": {
                "id": "test_category",
                "name": "Test Category"
            }
        }
        
        extended_categories = self.plugin.extend_category_data(base_categories)
        self.assertIsInstance(extended_categories, dict)
        self.assertIn("test_category", extended_categories)
        self.assertIn("relationship_action", extended_categories)

    @patch('project.plugins.data.social_poem_analysis_plugin.SeparateDatabaseManager')
    def test_database_init_plugin_interface(self, mock_db_manager):
        """测试数据库初始化插件接口"""
        # 设置模拟对象
        mock_db_adapter = Mock()
        mock_db_manager_instance = Mock()
        mock_db_manager_instance.get_db_adapter.return_value = mock_db_adapter
        mock_db_manager.return_value = mock_db_manager_instance
        
        # 测试initialize_database方法
        result = self.plugin.initialize_database("test_db")
        
        # 验证返回值
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("message", result)
        
        # 验证数据库适配器被调用
        mock_db_manager_instance.get_db_adapter.assert_called_once_with("test_db")
        mock_db_adapter.execute_script.assert_called_once()
        
        # 测试on_database_initialized方法
        # 这个方法应该是空实现，不抛出异常即可
        try:
            self.plugin.on_database_initialized("test_db", result)
        except Exception as e:
            self.fail(f"on_database_initialized方法抛出异常: {e}")


if __name__ == '__main__':
    unittest.main()