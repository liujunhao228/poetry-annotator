"""
标签解析器插件接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.config.schema import PluginConfig


class LabelParserPlugin(ABC):
    """标签解析器插件抽象基类"""
    
    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_categories(self) -> Dict[str, Any]:
        """
        获取插件提供的额外分类信息
        
        Returns:
            插件提供的分类信息字典，格式与LabelParser.categories一致
        """
        pass
    
    def extend_category_data(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """
        扩展分类数据
        
        Args:
            categories: 原始分类数据
            
        Returns:
            扩展后的分类数据
        """
        extended = categories.copy()
        plugin_categories = self.get_categories()
        
        # 合并分类信息
        for category_id, category_data in plugin_categories.items():
            if category_id not in extended:
                extended[category_id] = category_data
            else:
                # 合并现有分类和插件分类信息
                extended[category_id].update(category_data)
        
        return extended