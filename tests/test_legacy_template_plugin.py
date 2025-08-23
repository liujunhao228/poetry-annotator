#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试LegacyTemplatePromptBuilderPlugin插件的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
# 获取当前脚本的目录 (tests)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (tests的父目录)
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.prompt.plugins.legacy_template_plugin import LegacyTemplatePromptBuilderPlugin
from src.llm_services.schemas import PoemData, EmotionSchema


def test_legacy_template_plugin():
    """测试LegacyTemplatePromptBuilderPlugin插件"""
    print("测试LegacyTemplatePromptBuilderPlugin插件...")
    
    # 创建插件实例
    plugin = LegacyTemplatePromptBuilderPlugin()
    
    # 测试插件基本信息
    print(f"插件名称: {plugin.get_name()}")
    print(f"插件描述: {plugin.get_description()}")
    
    # 创建测试数据
    poem_data = PoemData(
        id="test_poem_001",
        title="静夜思",
        author="李白",
        paragraphs=[
            "床前明月光，疑是地上霜。",
            "举头望明月，低头思故乡。"
        ]
    )
    
    emotion_schema_text = """01. 喜 (喜悦)
01.01. 欢乐
01.02. 陶醉
01.03. 赞美
01.04. 祝福
01.05. 欣慰
02. 怒 (愤怒)
02.01. 憎恨
02.02. 指责
02.03. 讽刺
02.04. 焦躁
02.05. 烦闷
03. 哀 (哀伤)
03.01. 悲伤
03.02. 惆怅
03.03. 思念
03.04. 失落
03.05. 痛苦
04. 惧 (恐惧)
04.01. 担忧
04.02. 紧张
04.03. 惊讶
04.04. 困惑
05. 欲 (欲望)
05.01. 渴望
05.02. 追求
05.03. 贪婪
05.04. 炫耀
06. 恶 (厌恶)
06.01. 厌恶
06.02. 嫉妒
06.03. 鄙视
07. 理 (理性)
07.01. 思考
07.02. 分析
07.03. 客观
07.04. 批判
08. 情 (情感)
08.01. 爱情
08.02. 友情
08.03. 亲情
08.04. 怜悯
08.05. 关怀
08.06. 感激
08.07. 怀念
08.08. 思念
08.09. 惆怅
08.10. 怀旧
09. 闲 (闲适)
09.01. 悠闲
09.02. 淡然
09.03. 幽默
09.04. 自嘲
10. 时 (时令)
10.01. 春天
10.02. 夏天
10.03. 秋天
10.04. 冬天
11. 事 (事件)
11.01. 离别
11.02. 思乡
11.03. 怀古
11.04. 送别
11.05. 感时
11.06. 悼亡
11.07. 咏史
11.08. 咏物
12. 景 (景物)
12.01. 山水
12.02. 花鸟
12.03. 风雨
12.04. 月夜
12.05. 边塞"""
    
    emotion_schema = EmotionSchema(text=emotion_schema_text)
    
    # 测试构建提示词
    try:
        system_prompt, user_prompt = plugin.build_prompts(poem_data, emotion_schema, "default")
        print("\n--- 系统提示词 ---")
        print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        print("\n--- 用户提示词 ---")
        print(user_prompt)
        print("\n插件测试成功!")
        return True
    except Exception as e:
        print(f"\n插件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_legacy_template_plugin()
    sys.exit(0 if success else 1)