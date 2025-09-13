"""
响应解析插件管理器
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from src.response_parsing.core import ResponseParsingCore


class ResponseParsingManager:
    """
    响应解析插件管理器
    """
    
    def __init__(self, project_root: str = "."):
        """
        初始化响应解析管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root
        self.core = ResponseParsingCore(project_root)
        
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
        return self.core.parse_response(text)
        
    def parse_and_validate(self, text: str) -> List[Dict[str, Any]]:
        """
        解析并验证响应文本
        
        Args:
            text: LLM返回的原始文本
            
        Returns:
            一个经过解析和验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果解析或验证失败
        """
        return self.core.parse_and_validate(text)