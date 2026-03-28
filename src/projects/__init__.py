"""
项目注册表 - 管理所有项目类型的注册和获取

Project Registry - manages registration and retrieval of all project types
"""

from typing import Dict, Type, Any

# 导入项目类型组件
from .social_analysis.schema import SocialAnalysisSchema
from .social_analysis.prompts import SocialAnalysisPromptBuilder
from .social_analysis.annotator import SocialAnalysisAnnotator


# 项目类型注册表
PROJECT_TYPES: Dict[str, Dict[str, Any]] = {
    "social_analysis": {
        "name": "社会分析项目",
        "description": "基于社会学、传播学框架的诗词分析",
        "annotator": SocialAnalysisAnnotator,
        "schema": SocialAnalysisSchema,
        "prompt_builder": SocialAnalysisPromptBuilder,
    },
    # 未来可扩展更多项目类型
    # "emotion_classify": {
    #     "name": "情感分类项目",
    #     "description": "传统诗词情感分类标注",
    #     ...
    # },
}


def get_project_type(project_type: str) -> Dict[str, Any]:
    """
    获取项目类型的组件类
    
    Args:
        project_type: 项目类型名称
        
    Returns:
        包含组件类的字典
        
    Raises:
        ValueError: 当项目类型不存在时
    """
    if project_type not in PROJECT_TYPES:
        available = ", ".join(PROJECT_TYPES.keys())
        raise ValueError(f"未知的项目类型：{project_type}。可用的项目类型：{available}")
    
    return PROJECT_TYPES[project_type]


def list_project_types() -> list:
    """
    列出所有已注册的项目类型
    
    Returns:
        项目类型名称列表
    """
    return list(PROJECT_TYPES.keys())


def register_project_type(
    name: str, 
    annotator: Type,
    schema: Type = None,
    prompt_builder: Type = None,
    description: str = ""
) -> None:
    """
    注册新的项目类型
    
    Args:
        name: 项目类型名称
        annotator: 标注器类
        schema: Schema 类（可选）
        prompt_builder: Prompt 构建器类（可选）
        description: 项目描述
    """
    PROJECT_TYPES[name] = {
        "name": name,
        "description": description,
        "annotator": annotator,
        "schema": schema,
        "prompt_builder": prompt_builder,
    }
