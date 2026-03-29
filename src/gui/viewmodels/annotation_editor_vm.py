"""标注编辑器 ViewModel - Schema 驱动版本，纯逻辑层"""

from typing import Optional, List, Dict, Any, Callable
from copy import deepcopy

from ..models.annotation_state import AnnotationState, SentenceState
from ..models.schema_definition import ProjectSchema, SchemaField


class AnnotationEditorViewModel:
    """
    标注编辑器 ViewModel - Schema 驱动版本

    纯逻辑层，不包含任何 UI 代码。
    负责管理标注状态、处理用户操作、数据验证。
    
    核心特性：
    - 基于 ProjectSchema 动态支持任意项目类型
    - 不再硬编码特定字段（如 relationship_action）
    - 通用的字段操作方法

    使用模式:
        schema = ProjectSchema.from_project_type("social_analysis")
        vm = AnnotationEditorViewModel(project_schema=schema)
        vm.load_poem_data(poem_data)

        # 响应用户操作
        vm.select_next_sentence()
        vm.set_annotation_value("relationship_action", "RA03")
        vm.set_annotation_value("emotional_strategy", "ES02")

        # 保存
        result = vm.get_annotation_result()
    """

    def __init__(
        self,
        project_schema: Optional[ProjectSchema] = None,
        on_state_change: Optional[Callable[[], None]] = None,
    ):
        """
        初始化 ViewModel

        Args:
            project_schema: 项目 Schema 定义
            on_state_change: 状态变化回调
        """
        self._schema = project_schema
        self._state: Optional[AnnotationState] = None
        self._on_state_change = on_state_change

    @property
    def state(self) -> Optional[AnnotationState]:
        """获取当前状态"""
        return self._state

    @property
    def schema(self) -> Optional[ProjectSchema]:
        """获取项目 Schema"""
        return self._schema

    @property
    def schema_fields(self) -> Dict[str, SchemaField]:
        """获取 Schema 字段定义"""
        return self._schema.fields if self._schema else {}

    @property
    def schema_field_ids(self) -> List[str]:
        """获取 Schema 定义的字段 ID 列表"""
        return self._schema.field_ids if self._schema else []

    def _notify_change(self) -> None:
        """通知状态变化"""
        if self._state:
            self._state.mark_dirty()
        if self._on_state_change:
            self._on_state_change()

    def load_poem_data(self, poem_data: Dict[str, Any]) -> None:
        """
        加载诗词数据

        Args:
            poem_data: 诗词数据字典
        """
        self._state = AnnotationState.from_poem_data(
            poem_data,
            schema=self._schema
        )
        self._state.mark_clean()
        self._notify_change()

    def get_current_sentence(self) -> Optional[SentenceState]:
        """获取当前选中的句子"""
        if not self._state:
            return None
        return self._state.get_selected_sentence()

    def get_selected_sentence_id(self) -> Optional[str]:
        """获取当前选中的句子 ID"""
        if not self._state:
            return None
        return self._state.selected_sentence_id

    # ==================== Schema 相关方法 ====================

    def get_field_definition(self, field_id: str) -> Optional[SchemaField]:
        """获取指定字段的 Schema 定义"""
        if not self._schema:
            return None
        return self._schema.get_field(field_id)

    def get_field_name_zh(self, field_id: str) -> str:
        """获取字段中文名称"""
        field_def = self.get_field_definition(field_id)
        return field_def.name_zh if field_def else field_id

    def get_field_categories(self, field_id: str) -> List[Dict[str, Any]]:
        """获取字段的可选分类列表"""
        field_def = self.get_field_definition(field_id)
        return field_def.categories if field_def else []

    def is_valid_field_value(self, field_id: str, value: Any) -> bool:
        """验证字段值是否有效"""
        if not self._schema:
            return True
        return self._schema.is_valid_value(field_id, value)

    # ==================== 句子选择 ====================

    def select_sentence(self, sentence_id: str) -> bool:
        """选择指定句子"""
        if not self._state:
            return False
        self._state.selected_sentence_id = sentence_id
        self._notify_change()
        return True

    def select_first(self) -> bool:
        """选择第一个句子"""
        if not self._state:
            return False
        self._state.select_first()
        self._notify_change()
        return True

    def select_next(self) -> bool:
        """选择下一个句子"""
        if not self._state:
            return False
        result = self._state.select_next()
        self._notify_change()
        return result

    def select_prev(self) -> bool:
        """选择上一个句子"""
        if not self._state:
            return False
        result = self._state.select_prev()
        self._notify_change()
        return result

    def select_by_index(self, index: int) -> bool:
        """按索引选择句子"""
        if not self._state or index < 0 or index >= len(self._state.sentences):
            return False
        self._state.selected_sentence_id = self._state.sentences[index].sentence_id
        self._notify_change()
        return True

    # ==================== 通用标注操作 ====================

    def get_annotation_value(self, field_id: str) -> Any:
        """获取当前句子指定字段的标注值"""
        sentence = self.get_current_sentence()
        if not sentence:
            return None
        return sentence.get_annotation(field_id)

    def set_annotation_value(
        self, 
        field_id: str, 
        value: Any, 
        notify: bool = True
    ) -> bool:
        """
        设置当前句子指定字段的标注值

        Args:
            field_id: 字段 ID（如 relationship_action）
            value: 字段值
            notify: 是否触发状态变化回调

        Returns:
            是否成功设置
        """
        sentence = self.get_current_sentence()
        if not sentence:
            return False

        # 验证值的有效性
        if not self.is_valid_field_value(field_id, value):
            return False

        sentence.set_annotation(field_id, value)
        if notify:
            self._notify_change()
        return True

    def clear_annotation(self, field_id: str, notify: bool = True) -> None:
        """清空当前句子指定字段的标注"""
        sentence = self.get_current_sentence()
        if not sentence:
            return
        sentence.set_annotation(field_id, None)
        if notify:
            self._notify_change()

    def get_annotation_status(self, field_id: str) -> str:
        """获取当前句子指定字段的标注状态"""
        sentence = self.get_current_sentence()
        if not sentence:
            return "empty"
        return sentence.get_annotation_status(field_id)

    # ==================== 批量操作 ====================

    def copy_current_annotation(self) -> Dict[str, Any]:
        """复制当前句子的完整标注"""
        sentence = self.get_current_sentence()
        if not sentence:
            return {}
        return deepcopy(sentence.annotations)

    def paste_annotation(
        self, 
        annotation: Dict[str, Any], 
        sentence_ids: Optional[List[str]] = None
    ) -> int:
        """
        粘贴标注到指定句子

        Args:
            annotation: 标注数据字典
            sentence_ids: 目标句子 ID 列表，None 表示全部句子

        Returns:
            成功粘贴的句子数量
        """
        if not self._state:
            return 0

        targets = sentence_ids or [s.sentence_id for s in self._state.sentences]
        count = 0

        for sentence in self._state.sentences:
            if sentence.sentence_id in targets:
                for field_id, value in annotation.items():
                    if self.is_valid_field_value(field_id, value):
                        sentence.set_annotation(field_id, value)
                count += 1

        self._notify_change()
        return count

    def apply_current_to_all(self) -> int:
        """将当前句子的标注应用到全部句子"""
        annotation = self.copy_current_annotation()
        if not annotation:
            return 0
        return self.paste_annotation(annotation)

    def apply_field_value_to_all(self, field_id: str, value: Any) -> int:
        """
        将指定字段的值应用到全部句子

        Args:
            field_id: 字段 ID
            value: 字段值

        Returns:
            成功应用的句子数量
        """
        if not self._state:
            return 0

        if not self.is_valid_field_value(field_id, value):
            return 0

        count = 0
        for sentence in self._state.sentences:
            sentence.set_annotation(field_id, value)
            count += 1

        self._notify_change()
        return count

    def clear_all_field_values(self, field_id: str) -> int:
        """
        清空所有句子指定字段的值

        Args:
            field_id: 字段 ID

        Returns:
            清空的句子数量
        """
        if not self._state:
            return 0

        count = 0
        for sentence in self._state.sentences:
            current_value = sentence.get_annotation(field_id)
            if current_value is not None:
                sentence.set_annotation(field_id, None)
                count += 1

        self._notify_change()
        return count

    # ==================== 验证 ====================

    def validate(self) -> List[str]:
        """
        验证标注数据

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        if not self._state:
            errors.append("未加载诗词数据")
            return errors

        # 检查所有 Schema 定义的必填字段
        required_fields = self.schema_field_ids

        for sentence in self._state.sentences:
            for field_id in required_fields:
                value = sentence.get_annotation(field_id)
                if value is None or (isinstance(value, list) and len(value) == 0):
                    field_name = self.get_field_name_zh(field_id)
                    errors.append(f"{sentence.sentence_id}: 未设置 {field_name}")

        return errors

    # ==================== 保存 ====================

    def get_annotation_result(self) -> Optional[List[Dict[str, Any]]]:
        """获取标注结果（用于保存）"""
        if not self._state:
            return None
        return self._state.to_annotation_result()

    def mark_saved(self) -> None:
        """标记为已保存"""
        if self._state:
            self._state.mark_clean()

    def is_dirty(self) -> bool:
        """检查是否有未保存的修改"""
        return self._state.is_dirty if self._state else False

    # ==================== 状态导出 ====================

    def get_overview_data(self) -> List[Dict[str, Any]]:
        """
        获取概览视图数据

        Returns:
            列表，每个元素包含句子信息和所有字段的标注值
        """
        if not self._state:
            return []

        result = []
        for sentence in self._state.sentences:
            row = {
                "sentence_id": sentence.sentence_id,
                "sentence_text": sentence.sentence_text,
                "is_selected": sentence.sentence_id == self._state.selected_sentence_id,
            }
            # 添加所有字段的值
            for field_id in self.schema_field_ids:
                value = sentence.get_annotation(field_id)
                row[field_id] = value if value is not None else "-"
            result.append(row)
        return result

    def get_annotation_summary(self) -> Dict[str, Any]:
        """获取标注摘要统计"""
        if not self._state:
            return {}
        return self._state.get_annotation_summary()
