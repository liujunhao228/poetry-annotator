"""
社会分析项目 - 基于社会学、传播学框架的诗词分析

Social Analysis Project - poetry analysis based on sociology and communication framework
"""

from .schema import SocialAnalysisSchema
from .prompts import SocialAnalysisPromptBuilder
from .annotator import SocialAnalysisAnnotator

__all__ = [
    "SocialAnalysisSchema",
    "SocialAnalysisPromptBuilder",
    "SocialAnalysisAnnotator",
]
