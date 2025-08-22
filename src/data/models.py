"""
数据模型定义
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class Poem:
    """诗词数据模型"""
    id: int
    title: str
    author: str
    paragraphs: List[str]
    full_text: str
    author_desc: str = ""
    data_status: str = "active"
    pre_classification: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        # 确保paragraphs是列表类型
        if isinstance(self.paragraphs, str):
            try:
                self.paragraphs = json.loads(self.paragraphs)
            except json.JSONDecodeError:
                self.paragraphs = [self.paragraphs]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Poem':
        """从字典创建Poem实例"""
        # 处理title/rhythmic字段差异
        if 'rhythmic' in data and 'title' not in data:
            data['title'] = data['rhythmic']
        elif 'title' in data and 'rhythmic' not in data:
            data['rhythmic'] = data['title']
        
        return cls(**data)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Poem':
        """从数据库行记录字典创建Poem实例"""
        # 处理title/rhythmic字段差异
        if 'rhythmic' in row and 'title' not in row:
            row['title'] = row['rhythmic']
        elif 'title' in row and 'rhythmic' not in row:
            row['rhythmic'] = row['title']
            
        # 处理paragraphs JSON字符串
        if isinstance(row.get('paragraphs'), str):
            try:
                row['paragraphs'] = json.loads(row['paragraphs'])
            except json.JSONDecodeError:
                row['paragraphs'] = [row['paragraphs']]
                
        return cls(**row)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'paragraphs': self.paragraphs,
            'full_text': self.full_text,
            'author_desc': self.author_desc,
            'data_status': self.data_status,
            'pre_classification': self.pre_classification,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class Author:
    """作者数据模型"""
    name: str
    description: str = ""
    short_description: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Author':
        """从字典创建Author实例"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'short_description': self.short_description,
            'created_at': self.created_at
        }


@dataclass
class Annotation:
    """标注数据模型"""
    id: Optional[int]
    poem_id: int
    model_identifier: str
    status: str  # 'completed' or 'failed'
    annotation_result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Annotation':
        """从字典创建Annotation实例"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'poem_id': self.poem_id,
            'model_identifier': self.model_identifier,
            'status': self.status,
            'annotation_result': self.annotation_result,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }