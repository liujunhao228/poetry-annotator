"""
预处理插件适配器
"""

import logging
from typing import Dict, Any
from src.component_system import Plugin, ComponentType, PluginConfig

logger = logging.getLogger(__name__)


class PreprocessingPlugin(Plugin):
    """预处理插件基类"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(ComponentType.PREPROCESSING, plugin_config)
    
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            处理后的数据
        """
        raise NotImplementedError("预处理插件必须实现 preprocess 方法")


class PreprocessingPluginAdapter(PreprocessingPlugin):
    """预处理插件适配器"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        # 从插件配置中获取设置
        self.settings = plugin_config.settings
        
        # 动态导入并创建实际的预处理类实例
        module_name = plugin_config.module
        class_name = plugin_config.class_name
        
        try:
            import importlib
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            # 创建实际的插件实例
            self.plugin_instance = plugin_class(**self.settings)
            logger.info(f"成功创建预处理插件实例: {module_name}.{class_name}")
        except Exception as e:
            logger.error(f"创建预处理插件实例失败: {e}")
            raise
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self.plugin_config.settings.get('name', 'Unknown Preprocessing Plugin')
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self.plugin_config.settings.get('description', '预处理插件')
    
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            处理后的数据
        """
        if hasattr(self.plugin_instance, 'preprocess'):
            return self.plugin_instance.preprocess(data, **kwargs)
        else:
            raise NotImplementedError(f"插件 {self.get_name()} 没有实现 preprocess 方法")