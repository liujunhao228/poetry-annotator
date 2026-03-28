"""
数据访问层 - Repository 模式实现

Repository package - implements data access abstraction
"""

from .base import Repository, UnitOfWork
from .poetry_repository import PoetryRepository, PoetryRepositoryImpl
from .author_repository import AuthorRepository, AuthorRepositoryImpl
from .annotation_repository import AnnotationRepository, AnnotationRepositoryImpl

__all__ = [
    # Base classes
    "Repository",
    "UnitOfWork",
    # Poetry repository
    "PoetryRepository",
    "PoetryRepositoryImpl",
    # Author repository
    "AuthorRepository",
    "AuthorRepositoryImpl",
    # Annotation repository
    "AnnotationRepository",
    "AnnotationRepositoryImpl",
]
