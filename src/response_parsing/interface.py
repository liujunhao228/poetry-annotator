"""
响应解析插件接口定义
"""

from abc import abstractmethod
from typing import Dict, Any, List
from src.plugin_system.interfaces import ResponseParsingAndValidationPlugin


class ResponseParsingPlugin(ResponseParsingAndValidationPlugin):
    """响应解析插件基类"""
    
    @abstractmethod
    def parse_response(self, text: str) -> List[Dict[str, Any]]:
        """
        解析响应文本
        
        Args:
            text: LLM返回的原始文本
            
        Returns:
            一个经过解析的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果解析失败
        """
        pass