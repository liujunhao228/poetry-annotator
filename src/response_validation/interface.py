"""
响应验证插件接口定义
"""

from abc import abstractmethod
from typing import Dict, Any, List
from src.plugin_system.interfaces import ResponseValidatorPlugin


class ResponseValidationPlugin(ResponseValidatorPlugin):
    """响应验证插件基类"""
    
    @abstractmethod
    def validate_response(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证响应结果
        
        Args:
            result_list: 解析后的标注列表
            
        Returns:
            一个经过验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果验证失败
        """
        pass