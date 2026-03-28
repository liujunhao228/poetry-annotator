"""
数据模型层 - 使用 Pydantic 提供类型安全和数据验证

Models package - provides type-safe data models using Pydantic
"""

from .poetry import (
    PoetryModel,
    AuthorModel,
    PoetryCreate,
    PoetryUpdate,
    AuthorCreate,
    AuthorUpdate,
)
from .annotation import (
    AnnotationModel,
    AnnotationResult,
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationStatistics,
)
from .common import (
    IDPrefixConfig,
    StatisticsResult,
    InitResult,
    ExportFormat,
)

__all__ = [
    # Poetry models
    "PoetryModel",
    "PoetryCreate",
    "PoetryUpdate",
    "AuthorModel",
    "AuthorCreate",
    "AuthorUpdate",
    # Annotation models
    "AnnotationModel",
    "AnnotationResult",
    "AnnotationCreate",
    "AnnotationUpdate",
    "AnnotationStatistics",
    # Common models
    "IDPrefixConfig",
    "StatisticsResult",
    "InitResult",
    "ExportFormat",
]
