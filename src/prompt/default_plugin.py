"""默认Prompt构建插件"""

import json
import logging
from typing import Tuple, Dict, Any

from src.prompt.plugin_interface import PromptBuilderPlugin
from src.llm_services.schemas import PoemData, EmotionSchema


class DefaultPromptBuilderPlugin(PromptBuilderPlugin):
    """默认Prompt构建插件"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_name(self) -> str:
        return "default"
    
    def get_description(self) -> str:
        return "默认Prompt构建器，提供基础的Prompt构建功能"
    
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                      model_config: Dict[str, Any]) -> Tuple[str, str]:
        """
        构建系统提示词和用户提示词
        """
        # 构建系统提示词
        system_prompt = f"""# 角色
你是一位精通中国古典文学和情感分析的专家。

# 任务
你的任务是为一份包含ID和句子的JSON列表进行情感标注。

# 输入说明
你将收到一首诗词的元数据（包括标题、作者）和一个JSON数组（诗词内容），数组中的每个对象都包含一个id和对应的sentence。

# 输出规范
你的回答必须是一个格式严格的JSON数组，数组中的每个对象代表对一句诗的标注，且必须包含以下字段：
- id: **必须原样返回**输入中对应的句子ID。
- primary: 这句诗词的**主要情感**，提供**一个**二级情感分类的ID。
- secondary: 这句诗词的**次要情感**，提供**0到2个**二级情感分类的ID列表。如果无次要情感，请提供一个空列表 []。

**重要：最终输出必须不含任何解释性文字或Markdown标记。**
# 情感分类体系（仅使用ID）
{emotion_schema.text}

# 示例
--- 输入 ---
- 作者: 姚云文
- 词牌: 紫萸香慢
- 待标注句子:
[
  {{ "id": "S1", "sentence": "近重阳、偏多风雨，绝怜此日暄明。" }},
  {{ "id": "S2", "sentence": "问秋香浓未，待携客、出西城。" }},
  {{ "id": "S3", "sentence": "正自羁怀多感，怕荒台高处，更不胜情。" }},
  {{ "id": "S4", "sentence": "向尊前、又忆洒酒插花人。" }},
  {{ "id": "S5", "sentence": "只座上、已无老兵。" }},
  {{ "id": "S6", "sentence": "凄情。" }}, 
  {{ "id": "S7", "sentence": "浅醉还醒。" }}, 
  {{ "id": "S8", "sentence": "愁不肯、与诗平。" }}, 
  {{ "id": "S9", "sentence": "记长楸走马，雕弓ㄇ柳，前事休评。" }}, 
  {{ "id": "S10", "sentence": "紫萸一枝传赐，梦谁到、汉家陵。" }}, 
  {{ "id": "S11", "sentence": "尽乌纱、便随风去，要天知道，华发如此星星。" }}, 
  {{ "id": "S12", "sentence": "歌罢涕零。" }}, 
]

--- 输出 ---
[
    {{ "id": "S1", "primary": "01.05", "secondary": ["01.01"] }},
    {{ "id": "S2", "primary": "02.02", "secondary": ["02.04"] }},
    {{ "id": "S3", "primary": "10.01", "secondary": ["11.02"] }},
    {{ "id": "S4", "primary": "08.08", "secondary": ["08.10"] }},
    {{ "id": "S5", "primary": "10.04", "secondary": ["08.08"] }},
    {{ "id": "S6", "primary": "11.02", "secondary": ["10.01"] }},
    {{ "id": "S7", "primary": "11.02", "secondary": ["02.05"] }},
    {{ "id": "S8", "primary": "11.02", "secondary": ["10.01"] }},
    {{ "id": "S9", "primary": "08.10", "secondary": ["10.04"] }},
    {{ "id": "S10", "primary": "10.02", "secondary": ["05.04"] }},
    {{ "id": "S11", "primary": "04.08", "secondary": ["10.03"] }},
    {{ "id": "S12", "primary": "11.02", "secondary": ["10.01"] }},
]"""
        
        # 构建用户提示词
        sentences_with_id = [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(poem_data.paragraphs)]
        sentences_json = json.dumps(sentences_with_id, ensure_ascii=False, indent=2)
        
        user_prompt = f"""# 开始标注
--- 输入 ---
- 作者: {poem_data.author}
- 标题: {poem_data.title}
- 待标注句子:
{sentences_json}

--- 输出 ---"""
        
        return system_prompt, user_prompt