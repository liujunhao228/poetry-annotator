"""
Prompt 构建器抽象基类 - 定义 LLM Prompt 构建接口

Prompt Builder Abstract Base Class - defines LLM prompt building interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import logging


class BasePromptBuilder(ABC):
    """
    Prompt 构建器抽象基类
    
    每个项目类型需要实现此基类，定义其专用的 prompt 构建逻辑
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def build_prompts(
        self, 
        poem_data: Dict[str, Any], 
        schema: Dict[str, Any],
        model_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        构建 system 和 user prompt
        
        Args:
            poem_data: 诗词数据（包含 title, author, paragraphs 等）
            schema: 标注 schema 定义
            model_config: 模型配置
            
        Returns:
            (system_prompt, user_prompt) 元组
        """
        pass
    
    def _generate_sentences_with_id(self, paragraphs: list) -> list:
        """
        为句子生成 ID 并构建 JSON 格式
        
        Args:
            paragraphs: 诗句段落列表
            
        Returns:
            带 ID 的句子列表
        """
        return [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(paragraphs)]
    
    def _build_default_system_prompt(self, schema_text: str) -> str:
        """
        构建默认的 system prompt 模板
        
        Args:
            schema_text: schema 的文本描述
            
        Returns:
            system prompt 字符串
        """
        return f"""# 角色
你是一位专业的诗词分析专家。

# 核心任务
你的任务是分析一首诗词中每一句的深层含义。

# 分析框架
{schema_text}

# 输出规范
- 输出必须是纯粹的 JSON 数组
- 不要包含任何 Markdown 标记或解释性文字
- 确保 JSON 格式正确，可以被直接解析

# 示例输出格式
```json
[
    {{
        "id": "S1",
        "analysis": "分析结果..."
    }}
]
```"""
