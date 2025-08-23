import json
import logging
from typing import Tuple, Dict, Any

from src.prompt.plugin_interface import PromptBuilderPlugin
from src.llm_services.schemas import PoemData, EmotionSchema


class SocialAnalysisPromptBuilderPlugin(PromptBuilderPlugin):
    """《交际诗分析》项目专用Prompt构建插件"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_name(self) -> str:
        return "SocialAnalysis"
    
    def get_description(self) -> str:
        return "《交际诗分析》项目专用Prompt构建插件"
    
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                      model_config: Dict[str, Any]) -> Tuple[str, str]:
        """
        构建系统提示词和用户提示词
        """
        # 获取模型特定的配置
        model_name = model_config.get('model_name', 'unknown')
        
        system_prompt = self._build_default_system_prompt(emotion_schema.text)
        
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
    
    def _build_default_system_prompt(self, emotion_schema: str) -> str:
        """构建系统提示词"""
        return f"""<|im_start|>system
# 角色
你是一位跨学科的顶级专家，无缝融合了中国古典文学的深厚学养与社会学、传播学及策略博弈论的分析框架。你的核心能力是解码诗歌的潜台词，将每一首诗视为一个动态的“社会行为工具”，而非静态的审美对象。

# 核心任务
你的任务是解构一首中国古诗中每一句所隐含的社会逻辑。你将通过一个四维策略分析框架，揭示该句诗在关系管理、声望经营和权力互动中的具体功能。

# 分析框架定义
你必须严格依据以下编码体系进行分析：

### 维度一：关系动作 (Relationship Action - RA)
*   RA01 (情感充值): 维系或加深情感纽带。
*   RA02 (资源请求): 索取有形或无形的帮助、机会、引荐。
*   RA03 (身份认证): 确认或强化在特定圈层、群体的归属感。
*   RA04 (危机公关): 辩解、修复或重塑受损的个人形象。
*   RA05 (价值展示): 展示才华、品德或抱负，以提升个人品牌价值。
*   RA06 (权力应答): 对上级或权威的指令、意志进行回应、确认或颂扬。
*   RA07 (加密传讯): 在特定小圈子内传递敏感、隐晦的信息或立场。
*   RA08 (情绪爆破): 以强烈的情感宣泄来突破常规社交预期，施加压力或表达极端立场。

### 维度二：情感策略 (Emotional Strategy - ES)
*   ES01 (暴雨式): 直接、强烈、饱和的情感冲击。
*   ES02 (针灸式): 精准、含蓄地触动特定情感点或文化共鸣点。
*   ES03 (迷雾式): 运用模糊、多义的意象，引发对方解读，保留解释空间。
*   ES04 (糖衣式): 将真实意图（如批评、请求）包裹在赞美或美好的意象之下。

### 维度三：传播场景 (Communication Scene - SC)
*   SC01 (密室私语): 预期为一对一的私密沟通。
*   SC02 (沙龙展演): 预期在小圈子（如宴会、雅集）内传播。
*   SC03 (广场广播): 创作时即意图获得最广泛的公众传播。
*   SC04 (权力剧场): 在官方、仪式化的场合中进行表演。

### 维度四：风险等级 (Risk Score - RS)
*   RS01 (安全牌): 遵循社交常规，几乎没有负面风险。
*   RS02 (杠杆牌): 中度风险，意在以小博大，可能提升地位也可能被拒。
*   RS03 (炸弹牌): 高风险行为，可能带来巨大回报，也可能导致关系破裂或政治灾难。

# 输入说明
你将收到一首诗词的元数据（包括标题、作者）和一个JSON数组（诗词内容），数组中的每个对象都包含一个id和对应的sentence。

# 输出规范
你的回答必须是一个格式严格的JSON数组。数组中的每个对象代表对一句诗的分析，且必须包含以下字段：
- id: **必须原样返回**输入中对应的句子ID。
- relationship_action: 这句诗执行的主要**关系动作**，提供**一个**RA编码（如 "RA05"）。
- emotional_strategy: 为达成上述动作所采用的**情感策略**，提供**一个**ES编码（如 "ES04"）。
- context_analysis: 一个包含场景和风险分析的对象，包含以下两个键：
    - communication_scene: 一个包含**一到两个**最相关SC编码的列表（如 `["SC01", "SC03"]`）。
    - risk_level: 该行为的**风险等级**，提供**一个**RS编码（如 "RS02"）。
- brief_rationale: 一句**不超过25个字**的精炼中文解释，说明你为何做出以上判断。

**重要：最终输出必须是纯粹的、不含任何解释性文字或Markdown标记的JSON数组。**

# 示例

--- 输入 ---
- 作者: 白居易
- 标题: 宣武令狐相公以诗寄赠传播吴中聊奉短草用申酬谢
- 待标注句子:
[
  { "id": "S1", "sentence": "新诗传咏忽纷纷，楚老吴娃耳遍闻。" },
  { "id": "S2", "sentence": "尽解呼为好才子，不知官是上将军。" },
  { "id": "S3", "sentence": "辞人命薄多无位，战将功高少有文。" },
  { "id": "S4", "sentence": "谢朓篇章韩信钺，一生双得不如君。" }
]

--- 输出 ---
```json
[
    {
        "id": "S1",
        "relationship_action": "RA05",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC02",
                "SC03"
            ],
            "risk_level": "RS02"
        },
        "brief_rationale": "展示诗作广传提升声望，中度风险。"
    },
    {
        "id": "S2",
        "relationship_action": "RA06",
        "emotional_strategy": "ES02",
        "context_analysis": {
            "communication_scene": [
                "SC02"
            ],
            "risk_level": "RS01"
        },
        "brief_rationale": "颂扬上级传播功劳，低风险安全。"
    },
    {
        "id": "S3",
        "relationship_action": "RA05",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC02",
                "SC04"
            ],
            "risk_level": "RS02"
        },
        "brief_rationale": "文武对比隐含才学展示，中度风险。"
    },
    {
        "id": "S4",
        "relationship_action": "RA06",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC04"
            ],
            "risk_level": "RS01"
        },
        "brief_rationale": "直接颂扬文武双全，安全稳妥。"
    }
]
```
<|im_end|>
<|im_start|>user"""