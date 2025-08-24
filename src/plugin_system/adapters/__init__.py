"""
插件适配器入口文件
"""

from .query_adapter import QueryPluginAdapter
from .preprocessing_adapter import PreprocessingPluginAdapter
from .prompt_adapter import PromptPluginAdapter
from .label_parser_adapter import LabelParserPluginAdapter
from .db_init_adapter import DatabaseInitPluginAdapter
from .custom_query_adapter import CustomQueryPluginAdapter
from .social_emotion_adapter import HardcodedSocialEmotionCategoriesPluginAdapter
from .db_initializer_adapter import SocialPoemAnalysisDBInitializerAdapter
from .social_prompt_adapter import SocialAnalysisPromptBuilderPluginAdapter

__all__ = [
    "QueryPluginAdapter",
    "PreprocessingPluginAdapter",
    "PromptPluginAdapter",
    "LabelParserPluginAdapter",
    "DatabaseInitPluginAdapter",
    "CustomQueryPluginAdapter",
    "HardcodedSocialEmotionCategoriesPluginAdapter",
    "SocialPoemAnalysisDBInitializerAdapter",
    "SocialAnalysisPromptBuilderPluginAdapter"
]