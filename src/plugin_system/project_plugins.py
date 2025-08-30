"""
项目插件注册模块
负责将项目中的旧版插件适配到新的插件系统
"""

import logging
from src.plugin_system.manager import PluginManager
from src.plugin_system.adapters import (
    CustomQueryPluginAdapter,
    HardcodedSocialEmotionCategoriesPluginAdapter,
    SocialPoemAnalysisDBInitializerAdapter,
    SocialAnalysisPromptBuilderPluginAdapter
)
from src.config.schema import PluginConfig

# 配置日志
logger = logging.getLogger(__name__)


def register_project_plugins(plugin_manager: PluginManager, plugin_configs: dict):
    """注册项目插件到新的插件系统
    
    Args:
        plugin_manager: 插件管理器实例
        plugin_configs: 插件配置字典
    """
    # 定义插件适配器映射
    adapter_mapping = {
        'custom_query': CustomQueryPluginAdapter,
        'social_emotion_categories': HardcodedSocialEmotionCategoriesPluginAdapter,
        'social_db_init': SocialPoemAnalysisDBInitializerAdapter,
        'social_prompt': SocialAnalysisPromptBuilderPluginAdapter
    }
    
    # 遍历所有插件配置
    for plugin_name, plugin_config in plugin_configs.items():
        try:
            # 检查插件是否启用
            if not plugin_config.enabled:
                logger.debug(f"插件 '{plugin_name}' 未启用，跳过注册")
                continue
            
            # 获取插件类型
            plugin_type = plugin_config.settings.get('type')
            if not plugin_type:
                logger.warning(f"插件 '{plugin_name}' 缺少类型配置，无法注册")
                continue
            
            # 检查是否有对应的适配器
            if plugin_name in adapter_mapping:
                # 创建适配器实例
                adapter_class = adapter_mapping[plugin_name]
                adapter_instance = adapter_class(plugin_config)
                
                # 注册插件
                plugin_manager.register_plugin(adapter_instance)
                logger.info(f"成功注册项目插件: {plugin_name} (类型: {plugin_type})")
            else:
                # 对于没有适配器的插件，直接注册原始插件
                # 这适用于新的统一插件实现
                logger.debug(f"插件 '{plugin_name}' 没有适配器，将直接尝试加载")
                
        except Exception as e:
            logger.error(f"注册插件 '{plugin_name}' 时出错: {e}")