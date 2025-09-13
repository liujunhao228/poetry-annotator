"""社交诗分析假数据插件"""

import asyncio
import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from src.plugin_system.base import BasePlugin
from src.plugin_system.interfaces import LLMServicePlugin
from src.plugin_system.plugin_types import PluginType
from src.config.schema import PluginConfig
from src.fake_data.service import FakeDataService
from src.fake_data.factory import FakeDataFactory
from src.llm_services.schemas import PoemData, EmotionSchema


class SocialPoemAnalysisFakeDataPlugin(LLMServicePlugin):
    """社交诗分析假数据插件，提供模拟LLM服务功能"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 从插件配置中获取LLM配置名称
        self.model_config_name = plugin_config.settings.get('model_config_name', 'fake_data_default')
        
        # 创建假数据服务实例
        self.fake_service: Optional[FakeDataService] = None
        
    def get_name(self) -> str:
        """获取插件名称"""
        return "social_poem_analysis_fake_data_service"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "社交诗分析假数据服务插件，用于模拟LLM标注服务，生成符合交际诗分析框架的标注结果"
    
    def get_plugin_type(self) -> PluginType:
        """获取插件类型"""
        return PluginType.LLM_SERVICE
    
    def initialize(self) -> bool:
        """初始化插件"""
        try:
            # 获取插件配置中的LLM配置
            llm_config = self.plugin_config.settings.get('llm_config', {})
            
            # 使用工厂创建假数据服务实例
            self.fake_service = FakeDataFactory.create_fake_service(
                llm_config, 
                self.model_config_name
            )
            
            # 设置假数据生成器
            self.fake_service.set_annotation_generator(self._generate_fake_annotations)
            
            self.logger.info(f"SocialPoemAnalysisFakeDataPlugin initialized with model config: {self.model_config_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize SocialPoemAnalysisFakeDataPlugin: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理插件资源"""
        self.logger.info("Cleaning up SocialPoemAnalysisFakeDataPlugin")
        # FakeDataService不需要特殊清理
        return True
    
    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        处理诗词标注请求
        
        Args:
            poem: 诗词数据
            emotion_schema: 情感分类体系
            
        Returns:
            标注结果列表
        """
        if not self.fake_service:
            raise RuntimeError("FakeDataService not initialized")
        
        try:
            # 使用假数据服务进行标注
            result = await self.fake_service.annotate_poem(poem, emotion_schema)
            self.logger.debug(f"Processed poem {poem.id} with social poem analysis fake data service")
            return result
        except Exception as e:
            self.logger.error(f"Error processing poem {poem.id} with social poem analysis fake data service: {e}")
            raise
    
    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> str:
        """
        处理流式诗词标注请求
        
        Args:
            poem: 诗词数据
            emotion_schema: 情感分类体系
            
        Returns:
            流式响应结果
        """
        if not self.fake_service:
            raise RuntimeError("FakeDataService not initialized")
        
        try:
            # 使用假数据服务进行流式标注
            result = await self.fake_service.annotate_poem_stream(poem, emotion_schema)
            self.logger.debug(f"Processed poem {poem.id} with social poem analysis fake data service (stream)")
            return result
        except Exception as e:
            self.logger.error(f"Error processing poem {poem.id} with social poem analysis fake data service (stream): {e}")
            raise
    
    async def health_check(self) -> Tuple[bool, str]:
        """
        健康检查
        
        Returns:
            (是否健康, 描述信息)
        """
        if not self.fake_service:
            return False, "FakeDataService not initialized"
        
        try:
            is_healthy, message = await self.fake_service.health_check()
            return is_healthy, f"SocialPoemAnalysisFakeDataPlugin: {message}"
        except Exception as e:
            return False, f"SocialPoemAnalysisFakeDataPlugin health check failed: {e}"
    
    def _generate_fake_annotations(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        生成符合社交诗分析框架的假标注结果
        
        Args:
            poem: 诗词数据
            emotion_schema: 情感分类体系
            
        Returns:
            标注结果列表
        """
        # 生成句子ID列表
        sentences_with_id = self.fake_service._generate_sentences_with_id(poem.paragraphs)
        
        # 生成符合社交诗分析框架的标注结果
        result = []
        for sentence in sentences_with_id:
            # 随机选择关系动作 (RA01-RA08)
            ra_actions = [f"RA{i:02d}" for i in range(1, 9)]
            relationship_action = random.choice(ra_actions)
            
            # 随机选择情感策略 (ES01-ES04)
            es_strategies = [f"ES{i:02d}" for i in range(1, 5)]
            emotional_strategy = random.choice(es_strategies)
            
            # 随机选择传播场景 (SC01-SC04)，1-2个
            sc_scenes = [f"SC{i:02d}" for i in range(1, 5)]
            communication_scene = random.sample(sc_scenes, random.randint(1, 2))
            
            # 随机选择风险等级 (RS01-RS03)
            rs_levels = [f"RS{i:02d}" for i in range(1, 4)]
            risk_level = random.choice(rs_levels)
            
            # 生成简短理由
            rationales = [
                "展示才学提升个人品牌，中度风险。",
                "维系情感纽带，安全稳妥。",
                "传递隐晦立场，高度风险。",
                "颂扬上级权威，安全操作。",
                "请求资源支持，中度风险。",
                "重塑个人形象，高度风险。",
                "精准触动情感点，安全有效。",
                "直接情感冲击，中度风险。"
            ]
            brief_rationale = random.choice(rationales)
            
            result.append({
                "id": sentence["id"],
                "relationship_action": relationship_action,
                "emotional_strategy": emotional_strategy,
                "context_analysis": {
                    "communication_scene": communication_scene,
                    "risk_level": risk_level
                },
                "brief_rationale": brief_rationale
            })
        
        return result