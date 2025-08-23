"""Prompt构建插件接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from src.llm_services.schemas import PoemData, EmotionSchema


class PromptBuilderPlugin(ABC):
    """Prompt构建插件抽象基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                      model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词
        
        Args:
            poem_data: 诗词数据
            emotion_schema: 情感分类体系
            model_config: 模型配置
            
        Returns:
            Tuple[str, str]: (系统提示词, 用户提示词)
        """
        pass


class PromptPluginManager:
    """Prompt插件管理器"""
    
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, plugin: PromptBuilderPlugin):
        """注册插件"""
        self.plugins[plugin.get_name()] = plugin
    
    def get_plugin(self, name: str) -> Optional[PromptBuilderPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件及其描述"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}