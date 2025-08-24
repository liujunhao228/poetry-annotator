"""
数据模型插件接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass, asdict
from src.data.models import Poem, Author, Annotation


class DataModelPlugin(ABC):
    """数据模型插件抽象基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_poem_model(self) -> type:
        """获取诗词数据模型类"""
        pass
    
    @abstractmethod
    def get_author_model(self) -> type:
        """获取作者数据模型类"""
        pass
    
    @abstractmethod
    def get_annotation_model(self) -> type:
        """获取标注数据模型类"""
        pass