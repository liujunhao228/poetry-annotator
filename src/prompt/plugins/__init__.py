"""Prompt插件初始化文件"""

from .example_plugin import ExamplePromptBuilderPlugin
from .advanced_plugin import AdvancedPromptBuilderPlugin
from .dynamic_plugin import DynamicPromptBuilderPlugin
from .custom_plugin import CustomPromptBuilderPlugin
from .legacy_template_plugin import LegacyTemplatePromptBuilderPlugin

__all__ = [
    "ExamplePromptBuilderPlugin",
    "AdvancedPromptBuilderPlugin",
    "DynamicPromptBuilderPlugin",
    "CustomPromptBuilderPlugin",
    "LegacyTemplatePromptBuilderPlugin"
]