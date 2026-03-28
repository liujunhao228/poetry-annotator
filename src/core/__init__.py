"""
核心抽象层 - 定义标注系统的通用接口和抽象基类

Core abstraction layer - defines common interfaces and abstract base classes for the annotation system
"""

from .base_schema import BaseAnnotationSchema, BaseSchema
from .base_prompt import BasePromptBuilder
from .base_annotator import BaseAnnotator

__all__ = [
    "BaseAnnotationSchema",
    "BaseSchema",  # 别名
    "BasePromptBuilder",
    "BaseAnnotator",
]
