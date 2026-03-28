"""
社会分析项目 Prompt 构建器

Social Analysis Project Prompt Builder
"""

import json
from typing import Dict, Any, Tuple
from src.core.base_prompt import BasePromptBuilder


class SocialAnalysisPromptBuilder(BasePromptBuilder):
    """
    社会分析项目专用 Prompt 构建器
    
    构建用于社会分析任务的 system 和 user prompt
    """
    
    def build_prompts(
        self, 
        poem_data: Dict[str, Any], 
        schema: Dict[str, Any],
        model_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        构建社会分析任务的 prompts
        
        Args:
            poem_data: 诗词数据（title, author, paragraphs 等）
            schema: 社会分析 schema 定义
            model_config: 模型配置
            
        Returns:
            (system_prompt, user_prompt) 元组
        """
        system_prompt = self._build_system_prompt(schema)
        user_prompt = self._build_user_prompt(poem_data)
        
        return system_prompt, user_prompt
    
    def _build_system_prompt(self, schema: Dict[str, Any]) -> str:
        """
        构建 system prompt
        
        定义角色、任务和分析框架
        """
        schema_text = self._format_schema_for_prompt(schema)
        
        return f"""# 角色
你是一位跨学科的顶级专家，无缝融合了中国古典文学的深厚学养与社会学、传播学及策略博弈论的分析框架。你的核心能力是解码诗歌的潜台词，将每一首诗视为一个动态的"社会行为工具"，而非静态的审美对象。

# 核心任务
你的任务是解构一首中国古诗中每一句所隐含的社会逻辑。你将通过一个四维策略分析框架，揭示该句诗在关系管理、声望经营和权力互动中的具体功能。

# 分析框架定义
{schema_text}

# 输入说明
你将收到一首诗词的元数据（包括标题、作者）和一个 JSON 数组（诗词内容），数组中的每个对象都包含一个 id 和对应的 sentence。

# 输出规范
你的回答必须是一个格式严格的 JSON 数组。数组中的每个对象代表对一句诗的分析，且必须包含以下字段：
- id: **必须原样返回**输入中对应的句子 ID。
- relationship_action: 这句诗执行的主要**关系动作**，提供**一个**RA 编码（如 "RA05"）。
- emotional_strategy: 为达成上述动作所采用的**情感策略**，提供**一个**ES 编码（如 "ES04"）。
- context_analysis: 一个包含场景和风险分析的对象，包含以下两个键：
    - communication_scene: 一个包含**一到两个**最相关 SC 编码的列表（如 `["SC01", "SC03"]`）。
    - risk_level: 该行为的**风险等级**，提供**一个**RS 编码（如 "RS02"）。
- brief_rationale: 一句**不超过 25 个字**的精炼中文解释，说明你为何做出以上判断。

**重要：最终输出必须是纯粹的、不含任何解释性文字或 Markdown 标记的 JSON 数组。**

# 示例

--- 输入 ---
- 作者：白居易
- 标题：宣武令狐相公以诗寄赠传播吴中聊奉短草用申酬谢
- 待标注句子:
[
  {{
    "id": "S1",
    "sentence": "新诗传咏忽纷纷，楚老吴娃耳遍闻。"
  }},
  {{
    "id": "S2",
    "sentence": "尽解呼为好才子，不知官是上将军。"
  }}
]

--- 输出 ---
[
    {{
        "id": "S1",
        "relationship_action": "RA05",
        "emotional_strategy": "ES04",
        "context_analysis": {{
            "communication_scene": ["SC02", "SC03"],
            "risk_level": "RS02"
        }},
        "brief_rationale": "展示诗作广传提升声望，中度风险。"
    }},
    {{
        "id": "S2",
        "relationship_action": "RA06",
        "emotional_strategy": "ES02",
        "context_analysis": {{
            "communication_scene": ["SC02"],
            "risk_level": "RS01"
        }},
        "brief_rationale": "颂扬上级传播功劳，低风险安全。"
    }}
]"""
    
    def _build_user_prompt(self, poem_data: Dict[str, Any]) -> str:
        """
        构建 user prompt
        
        包含具体的诗词内容和标注请求
        """
        author = poem_data.get('author', 'N/A')
        title = poem_data.get('title', 'N/A')
        paragraphs = poem_data.get('paragraphs', [])
        
        # 构建带 ID 的句子 JSON
        sentences_with_id = [
            {"id": f"S{i+1}", "sentence": sentence} 
            for i, sentence in enumerate(paragraphs)
        ]
        sentences_json = json.dumps(sentences_with_id, ensure_ascii=False, indent=2)
        
        return f"""# 开始标注

--- 输入 ---
- 作者：{author}
- 标题：{title}
- 待标注句子:
{sentences_json}

--- 输出 ---"""
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """
        将 schema 格式化为 prompt 文本
        
        Args:
            schema: schema 字典
            
        Returns:
            格式化的 schema 文本
        """
        lines = []
        
        for dim_id, dim_data in schema.items():
            name_zh = dim_data.get('name_zh', dim_id)
            name_en = dim_data.get('name_en', '')
            description = dim_data.get('description', '')
            
            # 获取维度的简短 ID（如 RA, ES, SC, RS）
            dim_short_id = dim_id.replace('_', '').upper()[:2]
            if dim_short_id == 'RA':
                dim_prefix = "关系动作"
            elif dim_short_id == 'ES':
                dim_prefix = "情感策略"
            elif dim_short_id == 'SC':
                dim_prefix = "传播场景"
            elif dim_short_id == 'RS':
                dim_prefix = "风险等级"
            else:
                dim_prefix = name_zh
            
            lines.append(f"### 维度{len(lines)+1}: {name_zh} ({name_en})")
            lines.append(f"{description}")
            
            for cat in dim_data.get('categories', []):
                cat_id = cat.get('id', '')
                cat_name_zh = cat.get('name_zh', '')
                cat_name_en = cat.get('name_en', '')
                cat_desc = cat.get('description', '')
                lines.append(f"- **{cat_id} ({cat_name_zh}/{cat_name_en})**: {cat_desc}")
            
            lines.append("")
        
        return "\n".join(lines)
