"""
硬编码社交情感分类插件
为《交际诗分析》项目提供预定义的情感分类体系
"""

from typing import Dict, Any
from src.data.label_parser_plugin_interface import LabelParserPlugin


class HardcodedSocialEmotionCategoriesPlugin(LabelParserPlugin):
    """硬编码社交情感分类插件"""
    
    def get_name(self) -> str:
        """获取插件名称"""
        return "hardcoded_social_emotion_categories"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "《交际诗分析》项目专用硬编码情感分类信息"
    
    def get_categories(self) -> Dict[str, Any]:
        """
        获取硬编码的社交情感分类信息
        
        Returns:
            社交情感分类信息字典
        """
        # 为《交际诗分析》项目定义的情感分类体系
        categories = {
            "relationship_action": {
                "id": "relationship_action",
                "name_zh": "关系动作",
                "name_en": "Relationship Action",
                "description": "诗句在人际关系中发挥的具体功能",
                "categories": [
                    {
                        "id": "RA01",
                        "name_zh": "情感充值",
                        "name_en": "Emotional Recharge",
                        "description": "维系或加深情感纽带"
                    },
                    {
                        "id": "RA02",
                        "name_zh": "资源请求",
                        "name_en": "Resource Request",
                        "description": "索取有形或无形的帮助、机会、引荐"
                    },
                    {
                        "id": "RA03",
                        "name_zh": "身份认证",
                        "name_en": "Identity Verification",
                        "description": "确认或强化在特定圈层、群体的归属感"
                    },
                    {
                        "id": "RA04",
                        "name_zh": "危机公关",
                        "name_en": "Crisis Management",
                        "description": "辩解、修复或重塑受损的个人形象"
                    },
                    {
                        "id": "RA05",
                        "name_zh": "价值展示",
                        "name_en": "Value Display",
                        "description": "展示才华、品德或抱负，以提升个人品牌价值"
                    },
                    {
                        "id": "RA06",
                        "name_zh": "权力应答",
                        "name_en": "Power Response",
                        "description": "对上级或权威的指令、意志进行回应、确认或颂扬"
                    },
                    {
                        "id": "RA07",
                        "name_zh": "加密传讯",
                        "name_en": "Encrypted Communication",
                        "description": "在特定小圈子内传递敏感、隐晦的信息或立场"
                    },
                    {
                        "id": "RA08",
                        "name_zh": "情绪爆破",
                        "name_en": "Emotional Explosion",
                        "description": "以强烈的情感宣泄来突破常规社交预期，施加压力或表达极端立场"
                    }
                ]
            },
            "emotional_strategy": {
                "id": "emotional_strategy",
                "name_zh": "情感策略",
                "name_en": "Emotional Strategy",
                "description": "为达成关系动作所采用的情感表达方式",
                "categories": [
                    {
                        "id": "ES01",
                        "name_zh": "暴雨式",
                        "name_en": "Torrential",
                        "description": "直接、强烈、饱和的情感冲击"
                    },
                    {
                        "id": "ES02",
                        "name_zh": "针灸式",
                        "name_en": "Acupuncture",
                        "description": "精准、含蓄地触动特定情感点或文化共鸣点"
                    },
                    {
                        "id": "ES03",
                        "name_zh": "迷雾式",
                        "name_en": "Foggy",
                        "description": "运用模糊、多义的意象，引发对方解读，保留解释空间"
                    },
                    {
                        "id": "ES04",
                        "name_zh": "糖衣式",
                        "name_en": "Sugar-coated",
                        "description": "将真实意图（如批评、请求）包裹在赞美或美好的意象之下"
                    }
                ]
            },
            "communication_scene": {
                "id": "communication_scene",
                "name_zh": "传播场景",
                "name_en": "Communication Scene",
                "description": "诗句预期的传播环境和受众范围",
                "categories": [
                    {
                        "id": "SC01",
                        "name_zh": "密室私语",
                        "name_en": "Private Whisper",
                        "description": "预期为一对一的私密沟通"
                    },
                    {
                        "id": "SC02",
                        "name_zh": "沙龙展演",
                        "name_en": "Salon Performance",
                        "description": "预期在小圈子（如宴会、雅集）内传播"
                    },
                    {
                        "id": "SC03",
                        "name_zh": "广场广播",
                        "name_en": "Public Broadcast",
                        "description": "创作时即意图获得最广泛的公众传播"
                    },
                    {
                        "id": "SC04",
                        "name_zh": "权力剧场",
                        "name_en": "Power Theater",
                        "description": "在官方、仪式化的场合中进行表演"
                    }
                ]
            },
            "risk_level": {
                "id": "risk_level",
                "name_zh": "风险等级",
                "name_en": "Risk Score",
                "description": "诗句所承载的社交风险程度",
                "categories": [
                    {
                        "id": "RS01",
                        "name_zh": "安全牌",
                        "name_en": "Safe Card",
                        "description": "遵循社交常规，几乎没有负面风险"
                    },
                    {
                        "id": "RS02",
                        "name_zh": "杠杆牌",
                        "name_en": "Leverage Card",
                        "description": "中度风险，意在以小博大，可能提升地位也可能被拒"
                    },
                    {
                        "id": "RS03",
                        "name_zh": "炸弹牌",
                        "name_en": "Bomb Card",
                        "description": "高风险行为，可能带来巨大回报，也可能导致关系破裂或政治灾难"
                    }
                ]
            }
        }
        
        return categories