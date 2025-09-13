"""
情感分类模块入口文件。
"""

from .manager import EmotionClassificationManager
from .core import EmotionClassificationCore
from .interface import EmotionClassificationPlugin
from .plugin_adapter import EmotionClassifierPluginAdapter

__all__ = [
    "EmotionClassificationManager",
    "EmotionClassificationCore",
    "EmotionClassificationPlugin",
    "EmotionClassifierPluginAdapter"
]