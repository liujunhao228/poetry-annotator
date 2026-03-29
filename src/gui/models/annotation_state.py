"""标注状态模型 - 支持动态字段的 Schema 驱动版本"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from copy import deepcopy

from .schema_definition import ProjectSchema


@dataclass
class SentenceState:
    """
    单个句子的标注状态 - 动态字段版本
    
    不再硬编码字段，而是使用通用数据容器存储所有标注维度。
    
    Attributes:
        sentence_id: 句子 ID (如 "S1", "S2")
        sentence_text: 句子原文
        annotations: 动态标注数据字典，存储所有项目类型定义的标注维度
            - 社会分析项目示例:
              {
                  "relationship_action": "RA03",
                  "emotional_strategy": "ES02",
                  "communication_scene": ["SC01", "SC02"],
                  "risk_level": "RS01"
              }
    """
    sentence_id: str
    sentence_text: str
    annotations: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（数据库格式）"""
        return {
            "id": self.sentence_id,
            "sentence": self.sentence_text,
            **self.annotations  # 展开所有标注字段
        }
    
    @classmethod
    def from_dict(
        cls, 
        data: Dict[str, Any], 
        schema_field_ids: Optional[List[str]] = None
    ) -> "SentenceState":
        """
        从字典创建（数据库格式）
        
        Args:
            data: 数据库格式的数据字典
            schema_field_ids: Schema 字段 ID 列表，用于提取标注字段
                              如果为 None，则提取所有非 id/sentence 的字段
        """
        sentence_id = data.get("id", "")
        sentence_text = data.get("sentence", "")
        annotations = {}
        
        # 确定要提取的字段
        if schema_field_ids:
            # 只提取 Schema 定义的字段
            for field_id in schema_field_ids:
                if field_id in data:
                    annotations[field_id] = data[field_id]
        else:
            # 提取所有非保留字段
            reserved_keys = {"id", "sentence"}
            for key, value in data.items():
                if key not in reserved_keys:
                    annotations[key] = value
        
        return cls(
            sentence_id=sentence_id,
            sentence_text=sentence_text,
            annotations=annotations,
        )
    
    def get_annotation(self, field_id: str) -> Any:
        """获取指定字段的标注值"""
        return self.annotations.get(field_id)
    
    def set_annotation(self, field_id: str, value: Any) -> None:
        """设置指定字段的标注值"""
        self.annotations[field_id] = value
    
    def is_annotated(self, field_id: Optional[str] = None) -> bool:
        """
        检查是否已标注
        
        Args:
            field_id: 如果指定，检查该字段是否已标注
                      如果为 None，检查是否所有字段都已标注
        """
        if field_id:
            return self.annotations.get(field_id) is not None
        
        # 检查所有字段是否都有值
        return all(v is not None for v in self.annotations.values())
    
    def get_annotation_status(self, field_id: str) -> str:
        """
        获取字段的标注状态
        
        Returns:
            "annotated" | "partial" | "empty"
        """
        value = self.annotations.get(field_id)
        if value is None:
            return "empty"
        if isinstance(value, list) and len(value) == 0:
            return "empty"
        return "annotated"
    
    def copy(self) -> "SentenceState":
        """深拷贝"""
        return deepcopy(self)


@dataclass
class AnnotationState:
    """
    标注编辑器整体状态 - Schema 驱动版本
    
    Attributes:
        poem_id: 诗词 ID
        model_identifier: 模型标识符
        title: 诗词标题
        author: 作者
        full_text: 诗词全文
        status: 标注状态 (completed/failed/unannotated)
        sentences: 句子标注状态列表
        schema: 项目 Schema 定义
        is_dirty: 是否已修改（未保存）
        is_saving: 是否正在保存
        error: 错误信息
        selected_sentence_id: 当前选中的句子 ID
    """
    poem_id: int = 0
    model_identifier: str = ""
    title: str = ""
    author: str = ""
    full_text: str = ""
    status: str = "unannotated"
    sentences: List[SentenceState] = field(default_factory=list)
    schema: Optional[ProjectSchema] = None
    is_dirty: bool = False
    is_saving: bool = False
    error: Optional[str] = None
    selected_sentence_id: Optional[str] = None
    
    @property
    def selected_index(self) -> int:
        """获取当前选中句子的索引"""
        if not self.selected_sentence_id:
            return -1
        for i, s in enumerate(self.sentences):
            if s.sentence_id == self.selected_sentence_id:
                return i
        return -1
    
    @property
    def schema_field_ids(self) -> List[str]:
        """获取 Schema 定义的字段 ID 列表"""
        if self.schema:
            return self.schema.field_ids
        return []
    
    def get_selected_sentence(self) -> Optional[SentenceState]:
        """获取当前选中的句子状态"""
        if not self.selected_sentence_id:
            return None
        for s in self.sentences:
            if s.sentence_id == self.selected_sentence_id:
                return s
        return None
    
    def select_first(self) -> None:
        """选择第一个句子"""
        if self.sentences:
            self.selected_sentence_id = self.sentences[0].sentence_id
    
    def select_next(self) -> bool:
        """选择下一个句子，返回是否成功"""
        if not self.sentences:
            return False
        idx = self.selected_index
        if idx < 0:
            self.select_first()
            return True
        if idx < len(self.sentences) - 1:
            self.selected_sentence_id = self.sentences[idx + 1].sentence_id
            return True
        return False
    
    def select_prev(self) -> bool:
        """选择上一个句子，返回是否成功"""
        if not self.sentences:
            return False
        idx = self.selected_index
        if idx < 0:
            self.select_first()
            return True
        if idx > 0:
            self.selected_sentence_id = self.sentences[idx - 1].sentence_id
            return True
        return False
    
    def mark_dirty(self) -> None:
        """标记为已修改"""
        self.is_dirty = True
    
    def mark_clean(self) -> None:
        """标记为未修改"""
        self.is_dirty = False
    
    def to_annotation_result(self) -> List[Dict[str, Any]]:
        """转换为标注结果格式（用于保存）"""
        return [s.to_dict() for s in self.sentences]
    
    @classmethod
    def from_poem_data(
        cls, 
        poem_data: Dict[str, Any],
        schema: Optional[ProjectSchema] = None
    ) -> "AnnotationState":
        """
        从诗词数据创建状态
        
        Args:
            poem_data: 诗词数据字典，包含 poem_id, title, author,
                       paragraphs, annotation_result, model_identifier, status
            schema: 项目 Schema 定义（可选）
        """
        state = cls(
            poem_id=poem_data.get("poem_id", 0),
            model_identifier=poem_data.get("model_identifier", ""),
            title=poem_data.get("title", ""),
            author=poem_data.get("author", ""),
            status=poem_data.get("status", "unannotated"),
            schema=schema,
        )
        
        # 构建全文
        paragraphs = poem_data.get("paragraphs", [])
        state.full_text = poem_data.get("full_text", "\n".join(paragraphs))
        
        # 解析标注结果（JSON 字符串或列表）
        annotation_result = poem_data.get("annotation_result")
        annotation_result = cls._parse_annotation_result(annotation_result)
        
        # 构建 ID 到标注的映射
        annotation_map: Dict[str, Any] = {}
        for item in (annotation_result or []):
            sentence_id = item.get("id", "")
            annotation_map[sentence_id] = item
        
        # 获取 Schema 字段 ID 列表
        schema_field_ids = schema.field_ids if schema else None
        
        # 为每个句子创建状态
        for i, sentence in enumerate(paragraphs):
            sentence_id = f"S{i + 1}"
            annotation = annotation_map.get(sentence_id, {})

            # 确保 sentence_id 被正确设置
            annotation["id"] = sentence_id
            
            sentence_state = SentenceState.from_dict(
                annotation,
                schema_field_ids=schema_field_ids
            )
            # 如果没有句子文本，使用原文
            if not sentence_state.sentence_text:
                sentence_state.sentence_text = sentence
            state.sentences.append(sentence_state)
        
        # 默认选中第一个句子
        state.select_first()
        
        return state
    
    @staticmethod
    def _parse_annotation_result(annotation_result: Any) -> Optional[List[Dict[str, Any]]]:
        """解析标注结果（处理 JSON 字符串）"""
        if annotation_result is None:
            return None
        
        if isinstance(annotation_result, str):
            import json
            try:
                return json.loads(annotation_result)
            except (json.JSONDecodeError, ValueError):
                return []
        
        if isinstance(annotation_result, list):
            return annotation_result
        
        return []
    
    def get_annotation_summary(self) -> Dict[str, Any]:
        """
        获取标注摘要统计
        
        Returns:
            {
                "total_sentences": int,
                "annotated_count": int,
                "progress_percentage": float,
                "field_stats": {field_id: {"annotated": int, "empty": int}}
            }
        """
        total = len(self.sentences)
        if total == 0:
            return {
                "total_sentences": 0,
                "annotated_count": 0,
                "progress_percentage": 0.0,
                "field_stats": {},
            }
        
        # 统计每个字段的标注情况
        field_stats = {}
        for field_id in self.schema_field_ids:
            field_stats[field_id] = {"annotated": 0, "empty": 0}
        
        # 统计完全标注的句子数量（所有字段都有值）
        fully_annotated = 0
        
        for sentence in self.sentences:
            all_annotated = True
            for field_id in self.schema_field_ids:
                if sentence.get_annotation(field_id) is not None:
                    field_stats[field_id]["annotated"] += 1
                else:
                    field_stats[field_id]["empty"] += 1
                    all_annotated = False
            
            if all_annotated:
                fully_annotated += 1
        
        return {
            "total_sentences": total,
            "annotated_count": fully_annotated,
            "progress_percentage": (fully_annotated / total) * 100 if total > 0 else 0.0,
            "field_stats": field_stats,
        }
    
    def copy(self) -> "AnnotationState":
        """深拷贝"""
        return deepcopy(self)
