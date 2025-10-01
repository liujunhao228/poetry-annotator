"""假数据插件实现"""

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


class FakeDataPlugin(LLMServicePlugin):
    """假数据插件，提供模拟LLM服务功能"""
    
    def __init__(self, plugin_config: PluginConfig, **kwargs):
        super().__init__(plugin_config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 从插件配置中获取LLM配置名称
        self.model_config_name = plugin_config.settings.get('model_config_name', 'fake_data_default')
        
        # 创建假数据服务实例
        self.fake_service: Optional[FakeDataService] = None
        
    def get_name(self) -> str:
        """获取插件名称"""
        return "fake_data_service"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "假数据服务插件，用于模拟LLM标注服务"
    
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
            
            self.logger.info(f"FakeDataPlugin initialized with model config: {self.model_config_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize FakeDataPlugin: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理插件资源"""
        self.logger.info("Cleaning up FakeDataPlugin")
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
            self.logger.debug(f"Processed poem {poem.id} with fake data service")
            return result
        except Exception as e:
            self.logger.error(f"Error processing poem {poem.id} with fake data service: {e}")
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
            self.logger.debug(f"Processed poem {poem.id} with fake data service (stream)")
            return result
        except Exception as e:
            self.logger.error(f"Error processing poem {poem.id} with fake data service (stream): {e}")
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
            return is_healthy, f"FakeDataPlugin: {message}"
        except Exception as e:
            return False, f"FakeDataPlugin health check failed: {e}"
    
    def _generate_fake_annotations(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        生成假的标注结果
        
        Args:
            poem: 诗词数据
            emotion_schema: 情感分类体系
            
        Returns:
            标注结果列表
        """
        # 生成句子ID列表
        sentences_with_id = self.fake_service._generate_sentences_with_id(poem.paragraphs)
        
        # 生成随机标注结果
        result = []
        for sentence in sentences_with_id:
            # 随机选择主要情感(01.01-11.10)
            primary_category = f"{random.randint(1, 11):02d}"
            primary_subcategory = f"{random.randint(1, 10):02d}"
            primary = f"{primary_category}.{primary_subcategory}"
            
            # 随机选择0-2个次要情感
            secondary = []
            for _ in range(random.randint(0, 2)):
                sec_category = f"{random.randint(1, 11):02d}"
                sec_subcategory = f"{random.randint(1, 10):02d}"
                secondary.append(f"{sec_category}.{sec_subcategory}")
            
            result.append({
                "id": sentence["id"],
                "primary": primary,
                "secondary": secondary
            })
        
        return result
