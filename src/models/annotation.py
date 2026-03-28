"""
标注数据模型 - 定义标注结果和统计数据结构

Annotation data models for type-safe data handling
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any


class AnnotationResult(BaseModel):
    """
    标注结果业务模型
    
    表示单个句子的标注结果，用于业务逻辑处理
    """
    sentence_id: str = Field(..., description="句子 ID，如 'S1', 'S2'")
    sentence_text: str = Field(..., description="句子原文")
    primary_emotion: str = Field(..., description="主要情感")
    secondary_emotions: List[str] = Field(default_factory=list, description="次要情感列表")

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": "S1",
                "sentence_text": "床前明月光，",
                "primary_emotion": "思乡",
                "secondary_emotions": ["宁静", "感慨"]
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "sentence_id": self.sentence_id,
            "sentence_text": self.sentence_text,
            "primary_emotion": self.primary_emotion,
            "secondary_emotions": self.secondary_emotions,
        }


class AnnotationModel(BaseModel):
    """
    标注结果数据模型
    
    用于数据库读写操作的完整数据模型
    """
    id: Optional[int] = Field(None, description="标注记录 ID")
    poem_id: int = Field(..., description="诗词 ID")
    model_identifier: str = Field(..., min_length=1, description="模型标识符")
    status: str = Field(..., pattern="^(completed|failed)$", description="标注状态")
    annotation_result: Optional[str] = Field(None, description="标注结果（JSON 字符串）")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "poem_id": 1000001,
                "model_identifier": "gpt-4o",
                "status": "completed",
                "annotation_result": "[{\"sentence_id\":\"S1\",\"sentence_text\":\"床前明月光，\",\"primary_emotion\":\"思乡\",\"secondary_emotions\":[\"宁静\"]}]",
                "error_message": None,
                "created_at": "2024-01-01T00:00:00+08:00",
                "updated_at": "2024-01-01T00:00:00+08:00"
            }
        }

    @field_validator('annotation_result', mode='before')
    @classmethod
    def validate_annotation_result(cls, value):
        """如果是列表则转换为 JSON 字符串"""
        if isinstance(value, list):
            import json
            return json.dumps(value, ensure_ascii=False)
        return value

    def get_parsed_result(self) -> Optional[List[AnnotationResult]]:
        """解析 annotation_result 为 AnnotationResult 列表"""
        if not self.annotation_result:
            return None
        import json
        try:
            data = json.loads(self.annotation_result)
            if isinstance(data, list):
                return [AnnotationResult(**item) for item in data]
            return None
        except (json.JSONDecodeError, ValueError):
            return None

    def is_completed(self) -> bool:
        """检查标注是否完成"""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """检查标注是否失败"""
        return self.status == "failed"


class AnnotationCreate(BaseModel):
    """
    标注创建数据模型
    """
    poem_id: int = Field(..., description="诗词 ID")
    model_identifier: str = Field(..., min_length=1, description="模型标识符")
    status: str = Field(..., pattern="^(completed|failed)$", description="标注状态")
    annotation_result: Optional[str] = None
    error_message: Optional[str] = None

    def to_annotation_model(self) -> AnnotationModel:
        """转换为 AnnotationModel 实例"""
        now = datetime.now()
        return AnnotationModel(
            poem_id=self.poem_id,
            model_identifier=self.model_identifier,
            status=self.status,
            annotation_result=self.annotation_result,
            error_message=self.error_message,
            created_at=now,
            updated_at=now,
        )


class AnnotationUpdate(BaseModel):
    """
    标注更新数据模型
    """
    status: Optional[str] = Field(None, pattern="^(completed|failed)$")
    annotation_result: Optional[str] = None
    error_message: Optional[str] = None


class AnnotationStatistics(BaseModel):
    """
    标注统计信息模型
    """
    total_poems: int = Field(..., description="总诗词数")
    total_annotations: int = Field(..., description="总标注数")
    completed_annotations: int = Field(..., description="完成的标注数")
    failed_annotations: int = Field(..., description="失败的标注数")
    success_rate: float = Field(..., ge=0, le=100, description="成功率（百分比）")

    # 按模型统计
    by_model: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="按模型分组的统计"
    )

    # 按状态统计
    by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="按状态分组的统计"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_poems": 1000,
                "total_annotations": 2000,
                "completed_annotations": 1800,
                "failed_annotations": 200,
                "success_rate": 90.0,
                "by_model": {
                    "gpt-4o": {
                        "total": 1000,
                        "completed": 950,
                        "failed": 50,
                        "success_rate": 95.0
                    }
                },
                "by_status": {
                    "completed": 1800,
                    "failed": 200
                }
            }
        }

    @classmethod
    def create_empty(cls) -> 'AnnotationStatistics':
        """创建空的统计信息"""
        return cls(
            total_poems=0,
            total_annotations=0,
            completed_annotations=0,
            failed_annotations=0,
            success_rate=0.0,
        )
