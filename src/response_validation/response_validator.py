"""
响应验证器模块，提供默认验证器的获取函数。
"""

from typing import Any, List, Dict
from .manager import ResponseValidationManager

# 全局默认验证器实例
_default_validator: ResponseValidationManager = None


def get_default_validator() -> ResponseValidationManager:
    """
    获取默认的响应验证器实例。
    
    Returns:
        ResponseValidationManager: 默认的响应验证器实例
    """
    global _default_validator
    if _default_validator is None:
        _default_validator = ResponseValidationManager()
    return _default_validator