"""
响应验证插件管理器
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from src.response_validation.core import ResponseValidationCore


class ResponseValidationManager:
    """
    响应验证插件管理器
    """
    
    def __init__(self, project_root: str = "."):
        """
        初始化响应验证管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root
        self.core = ResponseValidationCore(project_root)
        
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
        return self.core.validate_response(result_list)
        
    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证标注列表的内容（实现ResponseValidatorPlugin接口）
        
        Args:
            result_list: 解析后的标注列表
            
        Returns:
            一个经过验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果验证失败
        """
        return self.core.validate(result_list)