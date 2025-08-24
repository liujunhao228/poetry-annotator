"""
Prompt插件适配器
将项目中的SocialAnalysisPromptBuilderPlugin适配为新的Plugin系统
"""

import logging
from typing import Tuple, Dict, Any
from src.plugin_system.interfaces import PromptBuilderPlugin
from src.config.schema import PluginConfig
from src.llm_services.schemas import PoemData, EmotionSchema

# 配置日志
logger = logging.getLogger(__name__)


class SocialAnalysisPromptBuilderPluginAdapter(PromptBuilderPlugin):
    """Prompt插件适配器"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        self.prompt_plugin = None
        self._name = None
        self._description = None
        
        # 根据配置动态加载
        self._load_prompt_plugin()
    
    def _load_prompt_plugin(self):
        """根据配置动态加载Prompt插件"""
        if not self.plugin_config.module or not self.plugin_config.class_name:
            raise ValueError("Prompt插件配置缺少module或class_name")
        
        # 从配置中获取模块名和类名
        plugin_module_name = self.plugin_config.module
        plugin_class_name = self.plugin_config.class_name
        
        # 动态导入插件模块
        try:
            plugin_module = __import__(plugin_module_name, fromlist=[plugin_class_name])
        except ImportError as e:
            logger.warning(f"无法导入模块 {plugin_module_name}: {e}")
            raise
        
        plugin_class = getattr(plugin_module, plugin_class_name)
        
        # 实例化插件，过滤掉不应该传递给构造函数的参数
        init_kwargs = self._filter_init_kwargs()
        
        self.prompt_plugin = plugin_class(**init_kwargs)
        self._name = self.prompt_plugin.get_name()
        self._description = self.prompt_plugin.get_description()
        
        logger.info(f"Prompt插件适配器创建成功: {self._name}")
    
    def _filter_init_kwargs(self):
        """过滤初始化参数"""
        # 定义不应传递给构造函数的参数
        excluded_keys = {'type', 'module', 'class'}
        
        # 过滤插件设置
        filtered_settings = {k: v for k, v in self.plugin_config.settings.items() if k not in excluded_keys}
        
        return filtered_settings
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self._name
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self._description
    
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                      model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词"""
        if not self.prompt_plugin:
            raise RuntimeError("Prompt插件未正确初始化")
        return self.prompt_plugin.build_prompts(poem_data, emotion_schema, model_config)