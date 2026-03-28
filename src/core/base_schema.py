"""
标注 Schema 抽象基类 - 定义标注数据的验证接口

Annotation Schema Abstract Base Class - defines validation interface for annotation data
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging


class BaseAnnotationSchema(ABC):
    """
    标注 Schema 抽象基类
    
    每个项目类型需要实现此基类，定义其专用的标注 schema 和验证逻辑
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        返回标注 schema 定义
        
        Returns:
            schema 字典，包含所有标注维度的定义
        """
        pass
    
    @abstractmethod
    def validate_response(
        self, 
        llm_output: List[Dict[str, Any]], 
        input_sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证 LLM 响应是否符合 schema 定义
        
        Args:
            llm_output: LLM 返回的原始输出（已解析为 JSON）
            input_sentences: 输入的句子列表（带 ID）
            
        Returns:
            验证通过后的标注结果
            
        Raises:
            ValueError: 当验证失败时
        """
        pass
    
    def get_schema_text(self) -> str:
        """
        获取 schema 的文本表示，用于构建 prompt
        
        Returns:
            schema 的文本描述
        """
        schema = self.get_schema()
        lines = ["# 分析框架定义\n"]
        
        for dim_id, dim_data in schema.items():
            name_zh = dim_data.get('name_zh', dim_id)
            name_en = dim_data.get('name_en', '')
            description = dim_data.get('description', '')
            
            lines.append(f"### 维度：{name_zh} ({name_en})")
            lines.append(f"{description}\n")
            
            for cat in dim_data.get('categories', []):
                cat_id = cat.get('id', '')
                cat_name_zh = cat.get('name_zh', '')
                cat_name_en = cat.get('name_en', '')
                cat_desc = cat.get('description', '')
                lines.append(f"- **{cat_id} ({cat_name_zh}/{cat_name_en})**: {cat_desc}")
            
            lines.append("")
        
        return "\n".join(lines)


# 别名，方便使用
BaseSchema = BaseAnnotationSchema
