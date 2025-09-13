"""
响应验证插件管理器模块
"""

from typing import Dict, Any, List, Optional
from .plugin_adapter import ResponseValidatorPluginAdapter
from .manager import ResponseValidationManager


class PluginBasedResponseValidatorManager:
    """
    基于插件的响应验证管理器
    """
    
    def __init__(self, project_root: str = "."):
        """
        初始化插件基础的响应验证管理器
        
        Args:
            project_root: 项目根目录路径
        """
        # 确保 project_root 是 Path 对象
        from pathlib import Path
        self.project_root = Path(project_root) if isinstance(project_root, str) else Path(".")
        self.adapter = ResponseValidatorPluginAdapter(self.project_root)
        self.default_validator = ResponseValidationManager(str(self.project_root))
        
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
        try:
            return self.adapter.validate_response(result_list)
        except Exception as e:
            # 如果插件验证失败，使用默认验证器
            print(f"插件验证失败，使用默认验证器: {e}")
            return self.default_validator.validate_response(result_list)
            
    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证标注列表的内容
        
        Args:
            result_list: 解析后的标注列表
            
        Returns:
            一个经过验证的、包含标注信息的字典列表
            
        Raises:
            ValueError, TypeError: 如果验证失败
        """
        try:
            return self.adapter.validate(result_list)
        except Exception as e:
            # 如果插件验证失败，使用默认验证器
            print(f"插件验证失败，使用默认验证器: {e}")
            return self.default_validator.validate(result_list)