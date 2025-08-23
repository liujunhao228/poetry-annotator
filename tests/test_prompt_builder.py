"""测试prompt_builder模块"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.prompt_builder import PromptBuilder
from src.llm_services.schemas import PoemData, EmotionSchema


class TestPromptBuilder(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.prompt_builder = PromptBuilder()

        # 创建测试数据
        self.poem_data = PoemData(
            id="1",
            author="李白",
            title="静夜思",
            paragraphs=["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        )

        self.emotion_schema = EmotionSchema(
            text="01.01 愉悦\n01.02 欢乐\n01.03 欣慰\n01.04 满足\n01.05 激动\n01.06 热爱"
        )

        self.model_config_name = "test-model"

    def test_build_prompts_success(self):
        """测试成功构建提示词"""
        # 执行测试
        system_prompt, user_prompt = self.prompt_builder.build_prompts(
            self.poem_data, self.emotion_schema, self.model_config_name
        )

        # 验证结果
        self.assertIsInstance(system_prompt, str)
        self.assertIsInstance(user_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        self.assertGreater(len(user_prompt), 0)

        # 验证情感分类体系是否正确插入
        self.assertIn("01.01 愉悦", system_prompt)

        # 验证诗词信息是否正确插入
        self.assertIn("李白", user_prompt)
        self.assertIn("静夜思", user_prompt)
        self.assertIn("床前明月光", user_prompt)

    def test_build_system_prompt_content(self):
        """测试系统提示词内容"""
        system_prompt, _ = self.prompt_builder.build_prompts(
            self.poem_data, self.emotion_schema, self.model_config_name
        )

        # 验证关键内容
        self.assertIn("# 角色", system_prompt)
        self.assertIn("情感标注", system_prompt)
        self.assertIn("JSON数组", system_prompt)
        self.assertIn("01.01 愉悦", system_prompt)
        self.assertIn("示例", system_prompt)

    def test_build_user_prompt_content(self):
        """测试用户提示词中JSON数据的正确性"""
        # 执行测试
        _, user_prompt = self.prompt_builder.build_prompts(
            self.poem_data, self.emotion_schema, self.model_config_name
        )

        # 验证JSON格式的句子是否正确生成
        self.assertIn('"id": "S1"', user_prompt)
        self.assertIn('"sentence": "床前明月光"', user_prompt)
        self.assertIn('"id": "S4"', user_prompt)
        self.assertIn('"sentence": "低头思故乡"', user_prompt)


if __name__ == '__main__':
    unittest.main()