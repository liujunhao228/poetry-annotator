"""
诗词数据模型 - 定义诗词和作者的核心数据结构

Poetry data models for type-safe data handling
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List


class PoetryModel(BaseModel):
    """
    诗词数据模型

    用于数据库读写操作的完整数据模型
    """
    id: int = Field(..., description="全局唯一 ID")
    title: Optional[str] = Field(None, description="诗词标题")
    author: str = Field(..., min_length=1, description="作者姓名")
    paragraphs: List[str] = Field(default_factory=list, description="段落列表")
    full_text: str = Field(..., description="完整文本，段落用换行分隔")
    author_desc: Optional[str] = Field(None, description="作者简介")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True  # 支持从 ORM 模型/字典加载
        json_schema_extra = {
            "example": {
                "id": 1000001,
                "title": "静夜思",
                "author": "李白",
                "paragraphs": ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"],
                "full_text": "床前明月光，\n疑是地上霜。\n举头望明月，\n低头思故乡。",
                "author_desc": "李白（701-762），字太白，号青莲居士",
                "created_at": "2024-01-01T00:00:00+08:00",
                "updated_at": "2024-01-01T00:00:00+08:00"
            }
        }

    @field_validator('paragraphs', mode='before')
    @classmethod
    def parse_paragraphs(cls, value):
        """如果 paragraphs 是 JSON 字符串，则解析为列表"""
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return [value] if value else []
        return value

    @field_validator('full_text', mode='before')
    @classmethod
    def ensure_full_text(cls, value, info):
        """如果 full_text 为空但有 paragraphs，则自动生成"""
        if not value and info.data.get('paragraphs'):
            return '\n'.join(info.data['paragraphs'])
        return value

    def to_display_dict(self) -> dict:
        """转换为用于显示的字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "paragraphs": self.paragraphs,
            "full_text": self.full_text,
            "author_desc": self.author_desc,
        }


class PoetryCreate(BaseModel):
    """
    诗词创建数据模型

    用于从 JSON 文件加载时的数据验证和转换
    """
    title: Optional[str] = Field(None, description="诗词标题")
    author: str = Field(..., min_length=1, description="作者姓名")
    paragraphs: List[str] = Field(default_factory=list, description="段落列表")
    author_desc: Optional[str] = Field(None, description="作者简介")

    # 兼容旧数据格式：支持 rhythmic 字段作为 title 的别名
    rhythmic: Optional[str] = Field(None, description="词牌名（兼容旧格式）")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "静夜思",
                "author": "李白",
                "paragraphs": ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"],
                "author_desc": "李白（701-762），字太白，号青莲居士"
            }
        }

    @model_validator(mode='after')
    def ensure_title(self):
        """确保 title 有值（从 rhythmic 或自身）"""
        if not self.title and self.rhythmic:
            self.title = self.rhythmic
        # title 可以为空，不再强制要求
        return self

    def to_poetry_model(self, poem_id: int) -> PoetryModel:
        """转换为 PoetryModel 实例"""
        now = datetime.now()
        return PoetryModel(
            id=poem_id,
            title=self.title,
            author=self.author,
            paragraphs=self.paragraphs,
            full_text='\n'.join(self.paragraphs),
            author_desc=self.author_desc,
            created_at=now,
            updated_at=now,
        )


class PoetryUpdate(BaseModel):
    """
    诗词更新数据模型
    
    所有字段可选，用于部分更新
    """
    title: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1)
    paragraphs: Optional[List[str]] = None
    full_text: Optional[str] = None
    author_desc: Optional[str] = None


class AuthorModel(BaseModel):
    """
    作者数据模型
    """
    name: str = Field(..., min_length=1, description="作者姓名")
    description: Optional[str] = Field(None, description="作者详细描述")
    short_description: Optional[str] = Field(None, description="作者简短描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "李白",
                "description": "李白（701-762），字太白，号青莲居士，唐代伟大的浪漫主义诗人，被后人誉为'诗仙'。",
                "short_description": "唐代诗人，字太白，号青莲居士",
                "created_at": "2024-01-01T00:00:00+08:00"
            }
        }


class AuthorCreate(BaseModel):
    """
    作者创建数据模型

    兼容旧数据格式：支持 'desc' 字段
    """
    name: str = Field(..., min_length=1, description="作者姓名")
    desc: Optional[str] = Field(None, description="作者描述（兼容旧格式）")
    description: Optional[str] = Field(None, description="作者详细描述")
    short_description: Optional[str] = Field(None, description="作者简短描述")

    @model_validator(mode='after')
    def ensure_description(self):
        """如果提供了 desc 则赋值给 description"""
        if not self.description and self.desc:
            self.description = self.desc
        return self

    def to_author_model(self) -> AuthorModel:
        """转换为 AuthorModel 实例"""
        return AuthorModel(
            name=self.name,
            description=self.description or "",
            short_description=self.short_description,
        )


class AuthorUpdate(BaseModel):
    """
    作者更新数据模型
    """
    description: Optional[str] = None
    short_description: Optional[str] = None
