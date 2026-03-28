"""
标注服务 - 封装标注业务逻辑

Annotation service - encapsulates annotation business logic
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 兼容两种导入方式：作为包导入和作为独立模块导入
try:
    from src.models.poetry import PoetryModel
    from src.models.annotation import AnnotationResult, AnnotationStatistics
    from src.repositories import PoetryRepository, AnnotationRepository
except ImportError:
    from models.poetry import PoetryModel
    from models.annotation import AnnotationResult, AnnotationStatistics
    from repositories import PoetryRepository, AnnotationRepository

logger = logging.getLogger(__name__)


@dataclass
class AnnotationTask:
    """
    标注任务数据类
    
    表示单个标注任务
    """
    poem_id: int
    title: str
    author: str
    paragraphs: List[str]
    model_identifier: str
    status: str = "pending"
    annotation_result: Optional[List[AnnotationResult]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_poetry_dict(self) -> Dict[str, Any]:
        """转换为诗词字典格式（供 Annotator 使用）"""
        return {
            'id': self.poem_id,
            'title': self.title,
            'author': self.author,
            'paragraphs': self.paragraphs,
            'full_text': '\n'.join(self.paragraphs),
            'author_desc': '',
        }


class AnnotationService:
    """
    标注服务
    
    封装标注相关的业务逻辑，协调 Repository 层操作
    """

    def __init__(
        self,
        poetry_repo: PoetryRepository,
        annotation_repo: AnnotationRepository
    ):
        """
        初始化标注服务
        
        Args:
            poetry_repo: 诗词仓库
            annotation_repo: 标注结果仓库
        """
        self._poetry_repo = poetry_repo
        self._annotation_repo = annotation_repo

    def get_pending_tasks(
        self,
        model_identifier: str,
        limit: Optional[int] = None,
        id_range: Optional[tuple] = None,
        exclude_annotated: bool = True
    ) -> List[AnnotationTask]:
        """
        获取待标注的任务列表
        
        Args:
            model_identifier: 模型标识符
            limit: 限制数量
            id_range: ID 范围 (start_id, end_id)
            exclude_annotated: 是否排除已标注的
            
        Returns:
            标注任务列表
        """
        poems = self._poetry_repo.get_to_annotate(
            model_identifier=model_identifier,
            limit=limit,
            id_range=id_range,
            exclude_annotated=exclude_annotated
        )

        tasks = []
        for poem in poems:
            tasks.append(AnnotationTask(
                poem_id=poem.id,
                title=poem.title,
                author=poem.author,
                paragraphs=poem.paragraphs,
                model_identifier=model_identifier,
            ))

        logger.debug(f"获取到 {len(tasks)} 个待标注任务")
        return tasks

    def get_tasks_by_ids(self, poem_ids: List[int], model_identifier: str) -> List[AnnotationTask]:
        """
        根据 ID 列表获取标注任务
        
        Args:
            poem_ids: 诗词 ID 列表
            model_identifier: 模型标识符
            
        Returns:
            标注任务列表
        """
        if not poem_ids:
            return []

        poems = self._poetry_repo.get_by_ids(poem_ids)
        tasks = []
        for poem in poems:
            tasks.append(AnnotationTask(
                poem_id=poem.id,
                title=poem.title,
                author=poem.author,
                paragraphs=poem.paragraphs,
                model_identifier=model_identifier,
            ))

        return tasks

    def save_result(self, task: AnnotationTask) -> bool:
        """
        保存标注结果
        
        Args:
            task: 标注任务（包含结果）
            
        Returns:
            是否成功
        """
        import json

        if task.annotation_result:
            annotation_json = json.dumps(
                [r.to_dict() for r in task.annotation_result],
                ensure_ascii=False
            )
        else:
            annotation_json = None

        return self._annotation_repo.update_or_insert(
            poem_id=task.poem_id,
            model_identifier=task.model_identifier,
            status=task.status,
            annotation_result=annotation_json,
            error_message=task.error_message
        )

    def get_statistics(self) -> AnnotationStatistics:
        """获取标注统计信息"""
        return self._annotation_repo.get_statistics()

    def get_completed_ids(self, poem_ids: List[int], model_identifier: str) -> set:
        """
        获取已成功标注的 ID 集合
        
        Args:
            poem_ids: 诗词 ID 列表
            model_identifier: 模型标识符
            
        Returns:
            已成功标注的 ID 集合
        """
        return self._poetry_repo.get_completed_ids(poem_ids, model_identifier)

    def validate_annotation(
        self,
        original_sentences: List[Dict[str, str]],
        llm_output: List[Dict[str, Any]]
    ) -> List[AnnotationResult]:
        """
        验证 LLM 响应与输入的一致性，并转换为 AnnotationResult 列表
        
        Args:
            original_sentences: 原始句子列表（带 ID）
            llm_output: LLM 输出
            
        Returns:
            验证后的标注结果列表
            
        Raises:
            ValueError: 验证失败时抛出
        """
        if not isinstance(llm_output, list) or not llm_output:
            raise ValueError(f"LLM 输出必须是一个非空列表，但实际是：{llm_output}")

        input_ids = {item['id'] for item in original_sentences}
        output_ids = {item['id'] for item in llm_output}

        if input_ids != output_ids:
            missing = sorted(list(input_ids - output_ids))
            extra = sorted(list(output_ids - input_ids))
            error_msg = "LLM 返回的句子 ID 与输入不匹配!"
            if missing:
                error_msg += f" 缺失 ID: {missing}."
            if extra:
                error_msg += f" 多余 ID: {extra}."
            raise ValueError(error_msg)

        # 转换为 AnnotationResult 列表
        annotations_by_id = {item['id']: item for item in llm_output}
        results = []
        for original_item in original_sentences:
            anno = annotations_by_id[original_item['id']]
            results.append(AnnotationResult(
                sentence_id=original_item['id'],
                sentence_text=original_item['sentence'],
                primary_emotion=anno['primary'],
                secondary_emotions=anno.get('secondary', []),
            ))

        logger.debug(f"验证通过，共 {len(results)} 条标注结果")
        return results
