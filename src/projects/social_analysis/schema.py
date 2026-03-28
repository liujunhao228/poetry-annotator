"""
社会分析项目 Schema - 四维编码体系

Social Analysis Project Schema - Four-dimensional coding system
"""

from typing import Dict, Any, List
from src.core.base_schema import BaseAnnotationSchema


class SocialAnalysisSchema(BaseAnnotationSchema):
    """
    社会分析项目专用 Schema
    
    四维分析框架：
    1. 关系动作 (Relationship Action) - 诗句在人际关系中的功能
    2. 情感策略 (Emotional Strategy) - 情感表达方式
    3. 传播场景 (Communication Scene) - 预期传播环境
    4. 风险等级 (Risk Level) - 社交风险程度
    """
    
    def __init__(self):
        super().__init__()
        self._schema = self._build_schema()
    
    def _build_schema(self) -> Dict[str, Any]:
        """构建社会分析 schema"""
        return {
            "relationship_action": {
                "id": "relationship_action",
                "name_zh": "关系动作",
                "name_en": "Relationship Action",
                "description": "诗句在人际关系中发挥的具体功能",
                "categories": [
                    {"id": "RA01", "name_zh": "情感充值", "name_en": "Emotional Recharge", "description": "维系或加深情感纽带"},
                    {"id": "RA02", "name_zh": "资源请求", "name_en": "Resource Request", "description": "索取有形或无形的帮助、机会、引荐"},
                    {"id": "RA03", "name_zh": "身份认证", "name_en": "Identity Verification", "description": "确认或强化在特定圈层、群体的归属感"},
                    {"id": "RA04", "name_zh": "危机公关", "name_en": "Crisis Management", "description": "辩解、修复或重塑受损的个人形象"},
                    {"id": "RA05", "name_zh": "价值展示", "name_en": "Value Display", "description": "展示才华、品德或抱负，以提升个人品牌价值"},
                    {"id": "RA06", "name_zh": "权力应答", "name_en": "Power Response", "description": "对上级或权威的指令、意志进行回应、确认或颂扬"},
                    {"id": "RA07", "name_zh": "加密传讯", "name_en": "Encrypted Communication", "description": "在特定小圈子内传递敏感、隐晦的信息或立场"},
                    {"id": "RA08", "name_zh": "情绪爆破", "name_en": "Emotional Explosion", "description": "以强烈的情感宣泄来突破常规社交预期，施加压力或表达极端立场"},
                ]
            },
            "emotional_strategy": {
                "id": "emotional_strategy",
                "name_zh": "情感策略",
                "name_en": "Emotional Strategy",
                "description": "为达成关系动作所采用的情感表达方式",
                "categories": [
                    {"id": "ES01", "name_zh": "暴雨式", "name_en": "Torrential", "description": "直接、强烈、饱和的情感冲击"},
                    {"id": "ES02", "name_zh": "针灸式", "name_en": "Acupuncture", "description": "精准、含蓄地触动特定情感点或文化共鸣点"},
                    {"id": "ES03", "name_zh": "迷雾式", "name_en": "Foggy", "description": "运用模糊、多义的意象，引发对方解读，保留解释空间"},
                    {"id": "ES04", "name_zh": "糖衣式", "name_en": "Sugar-coated", "description": "将真实意图（如批评、请求）包裹在赞美或美好的意象之下"},
                ]
            },
            "communication_scene": {
                "id": "communication_scene",
                "name_zh": "传播场景",
                "name_en": "Communication Scene",
                "description": "诗句预期的传播环境和受众范围",
                "categories": [
                    {"id": "SC01", "name_zh": "密室私语", "name_en": "Private Whisper", "description": "预期为一对一的私密沟通"},
                    {"id": "SC02", "name_zh": "沙龙展演", "name_en": "Salon Performance", "description": "预期在小圈子（如宴会、雅集）内传播"},
                    {"id": "SC03", "name_zh": "广场广播", "name_en": "Public Broadcast", "description": "创作时即意图获得最广泛的公众传播"},
                    {"id": "SC04", "name_zh": "权力剧场", "name_en": "Power Theater", "description": "在官方、仪式化的场合中进行表演"},
                ]
            },
            "risk_level": {
                "id": "risk_level",
                "name_zh": "风险等级",
                "name_en": "Risk Level",
                "description": "诗句所承载的社交风险程度",
                "categories": [
                    {"id": "RS01", "name_zh": "安全牌", "name_en": "Safe Card", "description": "遵循社交常规，几乎没有负面风险"},
                    {"id": "RS02", "name_zh": "杠杆牌", "name_en": "Leverage Card", "description": "中度风险，意在以小博大，可能提升地位也可能被拒"},
                    {"id": "RS03", "name_zh": "炸弹牌", "name_en": "Bomb Card", "description": "高风险行为，可能带来巨大回报，也可能导致关系破裂或政治灾难"},
                ]
            }
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """返回社会分析 schema"""
        return self._schema
    
    def validate_response(
        self, 
        llm_output: List[Dict[str, Any]], 
        input_sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证 LLM 响应是否符合社会分析 schema
        
        验证内容：
        1. 输出必须是非空列表
        2. 输出 ID 必须与输入 ID 完全匹配
        3. 每个标注必须包含必需的字段
        4. 编码值必须在定义的范围内
        
        Args:
            llm_output: LLM 返回的原始输出
            input_sentences: 输入的句子列表（带 ID）
            
        Returns:
            验证通过后的标注结果（添加原始句子文本）
            
        Raises:
            ValueError: 当验证失败时
        """
        self.logger.debug(f"验证社会分析响应 - 输入句子数：{len(input_sentences)}")
        
        # 验证 1: 输出必须是非空列表
        if not isinstance(llm_output, list) or not llm_output:
            error_msg = f"LLM 输出必须是非空列表，但实际是：{llm_output}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证 2: ID 必须匹配
        input_ids = {item['id'] for item in input_sentences}
        output_ids = {item['id'] for item in llm_output}
        
        if input_ids != output_ids:
            missing = sorted(list(input_ids - output_ids))
            extra = sorted(list(output_ids - input_ids))
            error_msg = f"LLM 返回的 ID 与输入不匹配！缺失：{missing}, 多余：{extra}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证 3 & 4: 字段完整性和编码有效性
        valid_ra_ids = {cat['id'] for cat in self._schema['relationship_action']['categories']}
        valid_es_ids = {cat['id'] for cat in self._schema['emotional_strategy']['categories']}
        valid_sc_ids = {cat['id'] for cat in self._schema['communication_scene']['categories']}
        valid_rs_ids = {cat['id'] for cat in self._schema['risk_level']['categories']}
        
        required_fields = ['relationship_action', 'emotional_strategy', 'context_analysis', 'brief_rationale']
        
        for item in llm_output:
            # 检查必需字段
            for field in required_fields:
                if field not in item:
                    error_msg = f"句子 ID {item.get('id', 'Unknown')} 缺少必需字段：{field}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # 验证关系动作编码
            ra = item.get('relationship_action')
            if ra not in valid_ra_ids:
                error_msg = f"句子 ID {item['id']} 的关系动作编码无效：{ra}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 验证情感策略编码
            es = item.get('emotional_strategy')
            if es not in valid_es_ids:
                error_msg = f"句子 ID {item['id']} 的情感策略编码无效：{es}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 验证风险等级编码
            context = item.get('context_analysis', {})
            rs = context.get('risk_level')
            if rs not in valid_rs_ids:
                error_msg = f"句子 ID {item['id']} 的风险等级编码无效：{rs}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 验证传播场景（可以是列表）
            scenes = context.get('communication_scene', [])
            if not isinstance(scenes, list) or not scenes:
                error_msg = f"句子 ID {item['id']} 的传播场景必须是非空列表"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            for scene in scenes:
                if scene not in valid_sc_ids:
                    error_msg = f"句子 ID {item['id']} 的传播场景编码无效：{scene}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
        
        # 验证通过，添加原始句子文本
        sentences_map = {item['id']: item['sentence'] for item in input_sentences}
        for item in llm_output:
            item['sentence'] = sentences_map.get(item['id'])
        
        self.logger.debug(f"社会分析验证通过 - 标注数：{len(llm_output)}")
        return llm_output
