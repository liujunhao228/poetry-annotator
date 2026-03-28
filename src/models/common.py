"""
通用数据模型 - 定义跨模块使用的通用数据结构

Common data models for cross-module usage
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ExportFormat(str, Enum):
    """导出格式枚举"""
    JSONL = "jsonl"
    JSON = "json"
    CSV = "csv"


class IDPrefixConfig(BaseModel):
    """
    ID 前缀配置
    
    用于确保不同数据库的诗词 ID 全局唯一
    """
    db_name: str = Field(..., description="数据库名称/别名")
    prefix: int = Field(0, description="ID 前缀值")

    class Config:
        json_schema_extra = {
            "example": {
                "db_name": "TangShi",
                "prefix": 1000000
            }
        }

    # 预定义的 ID 前缀映射
    PREFIX_MAP: Dict[str, int] = {
        "TangShi": 1000000,   # 唐诗 ID 前缀
        "SongCi": 2000000,    # 宋词 ID 前缀
        "YuanQu": 3000000,    # 元曲 ID 前缀
        "default": 0,         # 默认前缀
    }

    @classmethod
    def get_prefix(cls, db_name: str) -> int:
        """根据数据库名称获取 ID 前缀"""
        return cls.PREFIX_MAP.get(db_name, 0)

    @classmethod
    def get_db_name(cls, prefix: int) -> str:
        """根据 ID 前缀反推数据库名称"""
        for name, p in cls.PREFIX_MAP.items():
            if p == prefix:
                return name
        return "unknown"

    @classmethod
    def extract_original_id(cls, global_id: int) -> int:
        """从全局 ID 中提取原始 ID"""
        for prefix in cls.PREFIX_MAP.values():
            if global_id >= prefix:
                return global_id - prefix
        return global_id


class StatisticsResult(BaseModel):
    """
    数据库统计结果模型
    """
    total_poems: int = Field(..., description="总诗词数")
    total_authors: int = Field(..., description="总作者数")
    total_annotations: int = Field(0, description="总标注数")
    stats_by_model: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="按模型分组的统计"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_poems": 50000,
                "total_authors": 2000,
                "total_annotations": 100000,
                "stats_by_model": {
                    "gpt-4o": {
                        "completed": 45000,
                        "failed": 5000,
                        "total_annotated": 50000
                    }
                }
            }
        }


class InitResult(BaseModel):
    """
    数据库初始化结果模型
    """
    authors_inserted: int = Field(..., description="插入的作者数量")
    poems_inserted: int = Field(..., description="插入的诗词数量")
    success: bool = Field(True, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息（如果有）")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    @property
    def duration_seconds(self) -> Optional[float]:
        """计算初始化耗时（秒）"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    class Config:
        json_schema_extra = {
            "example": {
                "authors_inserted": 500,
                "poems_inserted": 50000,
                "success": True,
                "error_message": None,
                "started_at": "2024-01-01T00:00:00+08:00",
                "completed_at": "2024-01-01T00:05:00+08:00"
            }
        }


class DataFilter(BaseModel):
    """
    数据过滤条件模型
    
    用于查询时的过滤和分页
    """
    # 过滤条件
    author: Optional[str] = Field(None, description="作者名称（支持模糊匹配）")
    title: Optional[str] = Field(None, description="标题（支持模糊匹配）")
    model_identifier: Optional[str] = Field(None, description="模型标识符")
    status: Optional[str] = Field(None, pattern="^(completed|failed)$", description="标注状态")
    id_range: Optional[Dict[str, int]] = Field(None, description="ID 范围 {min: 1, max: 100}")

    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(10, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.per_page

    class Config:
        json_schema_extra = {
            "example": {
                "author": "李白",
                "title": "静夜思",
                "model_identifier": "gpt-4o",
                "status": "completed",
                "id_range": {"min": 1000000, "max": 2000000},
                "page": 1,
                "per_page": 20
            }
        }


class QueryResult(BaseModel):
    """
    查询结果模型（带分页）
    """
    items: List[Dict[str, Any]] = Field(..., description="数据项列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "per_page": 10,
                "pages": 10
            }
        }
