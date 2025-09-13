"""假数据服务实现"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from .models import FakeLLMConfig, FakeAnnotation
from src.llm_services.base_service import BaseLLMService
from src.llm_services.schemas import PoemData, EmotionSchema


class FakeDataService(BaseLLMService):
    """假数据服务，模拟LLM API响应"""
    
    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser=None):
        # 调用基类构造函数
        super().__init__(config, model_config_name, response_parser)
        
        # 初始化假数据配置
        self.fake_config = FakeLLMConfig(
            response_delay=float(config.get('response_delay', 0.1)),
            error_rate=float(config.get('error_rate', 0.0)),
            fixed_response=self._parse_fixed_response(config.get('fixed_response'))
        )
        
        # 假数据生成器函数，由插件提供
        self.annotation_generator: Optional[Callable[[PoemData, EmotionSchema], List[Dict[str, Any]]]] = None
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"[FakeData] 服务初始化完成 - 延迟: {self.fake_config.response_delay}s, 错误率: {self.fake_config.error_rate}")

        # 如果没有提供固定响应或外部生成器，设置一个默认的假数据生成器
        if not self.fake_config.fixed_response and not self.annotation_generator:
            self.set_annotation_generator(self._default_fake_annotation_generator)
    
    def _parse_fixed_response(self, fixed_response_str: Optional[str]) -> Optional[List[FakeAnnotation]]:
        """解析固定响应配置"""
        if not fixed_response_str:
            return None
        
        try:
            import json
            data = json.loads(fixed_response_str)
            if isinstance(data, list):
                return [FakeAnnotation(**item) for item in data]
            self.logger.warning("固定响应配置格式不正确，应为JSON数组")
            return None
        except Exception as e:
            self.logger.warning(f"解析固定响应配置失败: {e}")
            return None
    
    def set_annotation_generator(self, generator: Callable[[PoemData, EmotionSchema], List[Dict[str, Any]]]):
        """设置假数据生成器函数"""
        self.annotation_generator = generator
    
    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """模拟诗词标注"""
        # 模拟网络延迟
        await asyncio.sleep(self.fake_config.response_delay)
        
        # 模拟错误
        if self.fake_config.error_rate > 0:
            import random
            if random.random() < self.fake_config.error_rate:
                raise Exception("模拟API错误")
        
        # 生成句子ID列表
        sentences_with_id = self._generate_sentences_with_id(poem.paragraphs)
        
        # 如果配置了固定响应，直接返回
        if self.fake_config.fixed_response:
            result = []
            for fake_annotation in self.fake_config.fixed_response:
                # 确保ID匹配输入
                if any(s['id'] == fake_annotation.id for s in sentences_with_id):
                    result.append({
                        "id": fake_annotation.id,
                        "primary": fake_annotation.primary,
                        "secondary": fake_annotation.secondary
                    })
            return result
        
        # 如果提供了外部生成器，使用它来生成假数据
        if self.annotation_generator:
            return self.annotation_generator(poem, emotion_schema)
        
        # 如果没有提供生成器，抛出异常 (现在应该不会触发，因为有了默认生成器)
        raise NotImplementedError("未提供假数据生成器，无法生成标注结果")
    
    def _default_fake_annotation_generator(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """默认的假数据生成器，为每个句子生成一个简单的假标注"""
        sentences_with_id = self._generate_sentences_with_id(poem.paragraphs)
        fake_annotations = []
        # EmotionSchema 不包含 categories 属性，直接使用一个默认情感
        default_primary_emotion = "neutral" 

        for sentence in sentences_with_id:
            fake_annotations.append({
                "id": sentence['id'],
                "primary": default_primary_emotion,
                "secondary": []
            })
        self.logger.debug(f"[FakeData] 使用默认生成器为诗词 {poem.id} 生成了 {len(fake_annotations)} 条假标注。")
        return fake_annotations

    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> str:
        """模拟流式诗词标注"""
        # 模拟网络延迟
        await asyncio.sleep(self.fake_config.response_delay)
        
        # 模拟错误
        if self.fake_config.error_rate > 0:
            import random
            if random.random() < self.fake_config.error_rate:
                raise Exception("模拟API错误")
        
        # 生成句子ID列表
        sentences_with_id = self._generate_sentences_with_id(poem.paragraphs)
        
        # 如果配置了固定响应，直接返回
        if self.fake_config.fixed_response:
            result = []
            for fake_annotation in self.fake_config.fixed_response:
                # 确保ID匹配输入
                if any(s['id'] == fake_annotation.id for s in sentences_with_id):
                    result.append({
                        "id": fake_annotation.id,
                        "primary": fake_annotation.primary,
                        "secondary": fake_annotation.secondary
                    })
            return self._format_stream_response(result)
        
        # 如果提供了外部生成器，使用它来生成假数据
        if self.annotation_generator:
            result = self.annotation_generator(poem, emotion_schema)
            return self._format_stream_response(result)
        
        # 如果没有提供生成器，抛出异常
        raise NotImplementedError("未提供假数据生成器，无法生成标注结果")
    
    def _format_stream_response(self, annotations: List[Dict[str, Any]]) -> str:
        """格式化流式响应"""
        import json
        return json.dumps(annotations, ensure_ascii=False, indent=2)
    
    async def health_check(self) -> tuple[bool, str]:
        """健康检查"""
        return True, "Fake data service is always healthy"
