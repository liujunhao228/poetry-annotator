"""项目 Schema 定义 - 用于动态生成 UI 表单"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class SchemaField:
    """
    Schema 字段定义
    
    Attributes:
        id: 字段 ID（如 relationship_action）
        name_zh: 中文字段名
        name_en: 英文字段名
        description: 字段描述
        field_type: 字段类型（single_select, multi_select, text, number）
        categories: 可选值列表（用于 select 类型）
    """
    id: str
    name_zh: str
    name_en: str
    description: str
    field_type: str = "single_select"  # single_select, multi_select, text, number
    categories: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_category_ids(self) -> List[str]:
        """获取所有分类 ID"""
        return [cat["id"] for cat in self.categories]
    
    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取分类定义"""
        for cat in self.categories:
            if cat["id"] == category_id:
                return cat
        return None


@dataclass
class ProjectSchema:
    """
    项目 Schema 定义
    
    包含项目类型的所有标注维度定义，用于：
    1. 动态生成 UI 表单
    2. 验证标注数据
    3. 提供字段元数据
    """
    project_type: str
    fields: Dict[str, SchemaField] = field(default_factory=dict)
    
    @property
    def field_ids(self) -> List[str]:
        """获取所有字段 ID 列表"""
        return list(self.fields.keys())
    
    @property
    def field_count(self) -> int:
        """获取字段数量"""
        return len(self.fields)
    
    def get_field(self, field_id: str) -> Optional[SchemaField]:
        """获取指定字段定义"""
        return self.fields.get(field_id)
    
    def is_valid_value(self, field_id: str, value: Any) -> bool:
        """
        验证字段值是否有效
        
        Args:
            field_id: 字段 ID
            value: 字段值
            
        Returns:
            是否有效
        """
        field_def = self.fields.get(field_id)
        if not field_def:
            return False
        
        if value is None:
            return True  # None 总是有效（表示未选择）
        
        if field_def.field_type == "multi_select":
            if not isinstance(value, list):
                return False
            valid_ids = set(field_def.get_category_ids())
            return all(v in valid_ids for v in value)
        else:
            # single_select, text, number
            valid_ids = set(field_def.get_category_ids())
            if isinstance(value, str):
                return value in valid_ids or value == ""
            return value in valid_ids
    
    @classmethod
    def from_project_type(cls, project_type: str) -> "ProjectSchema":
        """
        从项目类型加载 Schema
        
        Args:
            project_type: 项目类型名称（如 social_analysis）
            
        Returns:
            ProjectSchema 实例
        """
        from src.projects import get_project_type
        
        try:
            components = get_project_type(project_type)
        except ValueError:
            # 项目类型不存在，返回空 Schema
            return cls(project_type=project_type, fields={})
        
        schema_class = components.get("schema")
        if schema_class is None:
            return cls(project_type=project_type, fields={})
        
        # 创建 Schema 实例并获取定义
        schema_instance = schema_class()
        raw_schema = schema_instance.get_schema()
        
        # 转换为 SchemaField 字典
        fields = {}
        for field_id, field_def in raw_schema.items():
            # 推断字段类型
            field_type = cls._infer_field_type(field_def)
            categories = field_def.get("categories", [])
            
            fields[field_id] = SchemaField(
                id=field_id,
                name_zh=field_def.get("name_zh", field_id),
                name_en=field_def.get("name_en", field_id),
                description=field_def.get("description", ""),
                field_type=field_type,
                categories=categories,
            )
        
        return cls(project_type=project_type, fields=fields)
    
    @classmethod
    def _infer_field_type(cls, field_def: Dict[str, Any]) -> str:
        """
        根据字段定义推断字段类型
        
        Args:
            field_def: 字段定义
            
        Returns:
            字段类型
        """
        # 检查是否有显式指定类型
        if "field_type" in field_def:
            return field_def["field_type"]
        
        # 根据 categories 推断
        categories = field_def.get("categories", [])
        if categories:
            # 检查是否有 multi_select 标记
            if field_def.get("multi_select", False):
                return "multi_select"
            return "single_select"
        
        # 没有 categories，默认为文本
        return "text"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于序列化）"""
        return {
            "project_type": self.project_type,
            "fields": {
                field_id: {
                    "id": f.id,
                    "name_zh": f.name_zh,
                    "name_en": f.name_en,
                    "description": f.description,
                    "field_type": f.field_type,
                    "categories": f.categories,
                }
                for field_id, f in self.fields.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectSchema":
        """从字典创建"""
        fields = {}
        for field_id, field_data in data.get("fields", {}).items():
            fields[field_id] = SchemaField(
                id=field_data["id"],
                name_zh=field_data["name_zh"],
                name_en=field_data["name_en"],
                description=field_data["description"],
                field_type=field_data["field_type"],
                categories=field_data.get("categories", []),
            )
        return cls(
            project_type=data.get("project_type", "unknown"),
            fields=fields,
        )
