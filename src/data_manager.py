"""
数据管理器 - 重构版

基于 Repository 模式和 StorageEngine 架构的数据管理层
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from .models.poetry import PoetryModel, PoetryCreate, AuthorModel, AuthorCreate
from .models.annotation import AnnotationModel, AnnotationStatistics
from .models.common import StatisticsResult, InitResult, QueryResult, DataFilter, ExportFormat
from .storage.engine import StorageEngine
from .storage.sqlite_engine import SQLiteEngine
from .repositories import (
    PoetryRepository, PoetryRepositoryImpl,
    AuthorRepository, AuthorRepositoryImpl,
    AnnotationRepository, AnnotationRepositoryImpl,
)
from .utils.id_generator import IDGenerator

logger = logging.getLogger(__name__)


class DataManager:
    """
    数据管理器 - 业务逻辑协调层
    
    使用 Repository 模式组织数据访问，提供高层业务接口
    """

    def __init__(
        self,
        db_path: str,
        source_dir: str,
        output_dir: str,
        db_name_alias: str = "default"
    ):
        """
        初始化数据管理器
        
        Args:
            db_path: 数据库文件路径
            source_dir: 数据源目录（JSON 文件所在目录）
            output_dir: 输出目录
            db_name_alias: 数据库别名（用于 ID 前缀设置）
        """
        self.db_path = db_path
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.db_name = db_name_alias

        logger.info(f"数据管理器初始化 - 数据库：{self.db_path}, 数据源：{self.source_dir}, 输出：{self.output_dir}")

        # 初始化存储引擎
        self._storage_engine: StorageEngine = SQLiteEngine(db_path)

        # 初始化 ID 生成器
        self._id_generator = IDGenerator(db_name_alias)

        # 初始化 Repository 层
        self._poetry_repo: PoetryRepository = PoetryRepositoryImpl(self._storage_engine.connect)
        self._author_repo: AuthorRepository = AuthorRepositoryImpl(self._storage_engine.connect)
        self._annotation_repo: AnnotationRepository = AnnotationRepositoryImpl(self._storage_engine.connect)

        # 初始化数据库表结构
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        logger.info("开始初始化数据库表结构...")
        self._storage_engine.init_schema()
        logger.info("数据库表结构初始化完成")

    # ==================== 作者数据操作 ====================

    def load_author_data(self) -> List[Dict[str, Any]]:
        """
        加载作者数据（从 JSON 文件）
        
        Returns:
            作者数据列表
        """
        if not self.source_dir.exists():
            logger.warning(f"数据源目录不存在：{self.source_dir}")
            return []

        all_authors = []
        author_files = list(self.source_dir.glob('authors.*.json')) + list(self.source_dir.glob('author.*.json'))
        author_files.sort()

        if not author_files:
            logger.warning("未找到作者文件")
            return []

        logger.info(f"找到 {len(author_files)} 个作者文件")

        for author_file in author_files:
            try:
                with open(author_file, 'r', encoding='utf-8') as f:
                    authors = json.load(f)
                all_authors.extend(authors)
                logger.debug(f"从 {author_file.name} 加载了 {len(authors)} 位作者")
            except Exception as e:
                logger.error(f"加载作者文件 {author_file.name} 时出错：{e}")

        logger.info(f"所有作者文件加载完成，总计 {len(all_authors)} 位作者")
        return all_authors

    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """
        批量插入作者信息
        
        Args:
            authors_data: 作者数据列表
            
        Returns:
            插入的作者数量
        """
        logger.info(f"开始批量插入 {len(authors_data)} 位作者...")

        models = []
        for data in authors_data:
            try:
                author = AuthorCreate(
                    name=data.get('name', ''),
                    desc=data.get('desc', ''),  # 兼容旧格式
                    description=data.get('description'),
                    short_description=data.get('short_description'),
                )
                models.append(author.to_author_model())
            except Exception as e:
                logger.error(f"创建作者模型失败 {data.get('name', 'Unknown')}: {e}")

        if models:
            self._author_repo.add_batch(models)
            logger.info(f"成功插入 {len(models)} 位作者")
        return len(models)

    def get_all_authors(self) -> List[AuthorModel]:
        """获取所有作者信息"""
        return self._author_repo.get_all()

    # ==================== 诗词数据操作 ====================

    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """
        加载所有 JSON 文件的数据
        
        Returns:
            诗词数据列表
        """
        if not self.source_dir.exists():
            raise FileNotFoundError(f"数据源目录不存在：{self.source_dir}")

        all_data = []
        poet_files = list(self.source_dir.glob('poet.*.*.json'))
        ci_files = list(self.source_dir.glob('ci.*.*.json'))
        json_files = sorted(poet_files + ci_files)

        logger.info(f"找到 {len(json_files)} 个 JSON 文件 ({len(poet_files)} 个 poet 文件，{len(ci_files)} 个 ci 文件)")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
                logger.debug(f"文件 {json_file.name} 处理完成，包含 {len(data)} 条记录")
            except Exception as e:
                logger.error(f"处理文件 {json_file.name} 时出错：{e}")

        logger.info(f"所有 JSON 文件加载完成，总计 {len(all_data)} 条记录")
        return all_data

    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """
        批量插入诗词到数据库
        
        Args:
            poems_data: 诗词数据列表
            start_id: 起始 ID（可选，默认使用 ID 生成器）
            
        Returns:
            插入的诗词数量
        """
        logger.info(f"开始批量插入 {len(poems_data)} 首诗词...")

        models = []
        current_id = start_id if start_id else 0

        for data in poems_data:
            try:
                # 标准化数据（处理 title/rhythmic 字段差异）
                normalized = self._normalize_poem_data(data)
                
                if start_id:
                    poem_id = current_id
                    current_id += 1
                else:
                    poem_id = self._id_generator.generate()

                paragraphs = normalized.get('paragraphs', [])
                if isinstance(paragraphs, str):
                    try:
                        paragraphs = json.loads(paragraphs)
                    except (json.JSONDecodeError, ValueError):
                        paragraphs = [paragraphs] if paragraphs else []

                poem = PoetryCreate(
                    title=normalized.get('title', ''),
                    author=normalized.get('author', ''),
                    paragraphs=paragraphs,
                    author_desc=normalized.get('author_desc'),
                )
                models.append(poem.to_poetry_model(poem_id))
            except Exception as e:
                logger.error(f"创建诗词模型失败：{e}")

        if models:
            self._poetry_repo.add_batch(models)
            logger.info(f"成功插入 {len(models)} 首诗词")
        return len(models)

    def _normalize_poem_data(self, poem_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化诗词数据，处理字段命名差异"""
        normalized = poem_data.copy()

        # 处理 title/rhythmic 字段差异
        if 'rhythmic' in normalized and 'title' not in normalized:
            normalized['title'] = normalized['rhythmic']
        elif 'title' in normalized and 'rhythmic' not in normalized:
            normalized['rhythmic'] = normalized['title']

        return normalized

    def get_poems_to_annotate(
        self,
        model_identifier: str,
        limit: Optional[int] = None,
        start_id: Optional[int] = None,
        end_id: Optional[int] = None,
        force_rerun: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取待标注的诗词
        
        Args:
            model_identifier: 模型标识符
            limit: 限制数量
            start_id: 起始 ID
            end_id: 结束 ID
            force_rerun: 是否强制重跑（忽略已标注的）
            
        Returns:
            诗词列表（字典格式）
        """
        id_range = None
        if start_id is not None or end_id is not None:
            id_range = (start_id or 0, end_id or float('inf'))

        models = self._poetry_repo.get_to_annotate(
            model_identifier=model_identifier,
            limit=limit,
            id_range=id_range,
            exclude_annotated=not force_rerun
        )

        return [self._model_to_dict(m) for m in models]

    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Dict[str, Any]]:
        """根据 ID 列表获取诗词"""
        if not poem_ids:
            return []

        models = self._poetry_repo.get_by_ids(poem_ids)
        return [self._model_to_dict(m) for m in models]

    def get_poem_by_id(self, poem_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单首诗词"""
        model = self._poetry_repo.get_by_id(poem_id)
        if model:
            return self._model_to_dict(model)
        return None

    def _model_to_dict(self, model: PoetryModel) -> Dict[str, Any]:
        """将 PoetryModel 转换为字典"""
        return {
            'id': model.id,
            'title': model.title,
            'author': model.author,
            'paragraphs': model.paragraphs,
            'full_text': model.full_text,
            'author_desc': model.author_desc,
        }

    def search_poems(
        self,
        author: Optional[str] = None,
        title: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """搜索诗词"""
        models, total = self._poetry_repo.search(
            author=author,
            title=title,
            page=page,
            per_page=per_page
        )

        return {
            "poems": [self._model_to_dict(m) for m in models],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    # ==================== 标注结果操作 ====================

    def save_annotation(
        self,
        poem_id: int,
        model_identifier: str,
        status: str,
        annotation_result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        保存标注结果（UPSERT）
        
        Args:
            poem_id: 诗词 ID
            model_identifier: 模型标识符
            status: 状态 (completed/failed)
            annotation_result: 标注结果（JSON 字符串）
            error_message: 错误信息
            
        Returns:
            是否成功
        """
        logger.debug(f"保存标注结果 - 诗词 ID: {poem_id}, 模型：{model_identifier}, 状态：{status}")

        try:
            success = self._annotation_repo.update_or_insert(
                poem_id=poem_id,
                model_identifier=model_identifier,
                status=status,
                annotation_result=annotation_result,
                error_message=error_message
            )
            if success:
                logger.debug(f"标注结果保存成功 - 诗词 ID: {poem_id}, 模型：{model_identifier}")
            return success
        except Exception as e:
            logger.error(f"保存标注结果失败 - 诗词 ID: {poem_id}, 模型：{model_identifier}, 错误：{e}")
            return False

    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> set:
        """
        高效检查一组 poem_id 是否已被特定模型成功标注
        
        Args:
            poem_ids: 诗词 ID 列表
            model_identifier: 模型标识符
            
        Returns:
            已成功标注的 ID 集合
        """
        if not poem_ids:
            return set()
        return self._poetry_repo.get_completed_ids(poem_ids, model_identifier)

    # ==================== 统计与导出 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        logger.debug("开始获取数据库统计信息...")

        stats = self._annotation_repo.get_statistics()

        # 格式化按模型统计
        stats_by_model = {}
        for model, data in stats.by_model.items():
            stats_by_model[model] = {
                'completed': data.get('completed', 0),
                'failed': data.get('failed', 0),
                'total_annotated': data.get('total', 0)
            }

        return {
            'total_poems': stats.total_poems,
            'total_authors': self._author_repo.count(),
            'stats_by_model': stats_by_model
        }

    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        stats = self._annotation_repo.get_statistics()
        return {
            'overall': {
                'total_poems': stats.total_poems,
                'total_annotations': stats.total_annotations,
                'completed_annotations': stats.completed_annotations,
                'failed_annotations': stats.failed_annotations,
                'success_rate': stats.success_rate
            },
            'by_model': stats.by_model,
            'by_status': stats.by_status
        }

    def export_results(
        self,
        output_format: str = 'jsonl',
        output_file: Optional[str] = None,
        model_filter: Optional[str] = None
    ) -> str:
        """
        导出标注结果
        
        Args:
            output_format: 导出格式 (jsonl/json/csv)
            output_file: 输出文件路径
            model_filter: 模型过滤器
            
        Returns:
            输出文件路径
        """
        # 获取所有标注
        annotations = self._annotation_repo.get_all()

        # 应用过滤器
        if model_filter:
            annotations = [a for a in annotations if a.model_identifier == model_filter]

        # 确定输出文件路径
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_suffix = f"_{model_filter}" if model_filter else ""
            output_file = str(self.output_dir / f"export_{timestamp}{model_suffix}.{output_format}")

        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 导出为 JSONL
        if output_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for anno in annotations:
                    poem = self._poetry_repo.get_by_id(anno.poem_id)
                    result_dict = {
                        'poem_id': anno.poem_id,
                        'title': poem.title if poem else '',
                        'author': poem.author if poem else '',
                        'paragraphs': poem.paragraphs if poem else [],
                        'full_text': poem.full_text if poem else '',
                        'author_desc': poem.author_desc if poem else '',
                        'model_identifier': anno.model_identifier,
                        'status': anno.status,
                        'annotation_result': anno.annotation_result,
                        'error_message': anno.error_message,
                        'created_at': anno.created_at.isoformat(),
                        'updated_at': anno.updated_at.isoformat()
                    }
                    f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')

        return str(output_file)

    # ==================== 数据库初始化 ====================

    def initialize_database_from_json(self, clear_existing: bool = False) -> Dict[str, int]:
        """
        从 JSON 文件初始化数据库
        
        Args:
            clear_existing: 是否清空现有数据
            
        Returns:
            初始化结果 {authors: count, poems: count}
        """
        logger.info("开始初始化数据库...")

        if clear_existing:
            logger.info("清空现有数据...")
            # 注意：SQLite 不支持 TRUNCATE，使用 DELETE
            self._storage_engine.execute_update("DELETE FROM annotations")
            self._storage_engine.execute_update("DELETE FROM poems")
            self._storage_engine.execute_update("DELETE FROM authors")
            logger.info("现有数据已清空")

        # 加载并插入作者数据
        authors = self.load_author_data()
        author_count = 0
        if authors:
            author_count = self.batch_insert_authors(authors)

        # 加载并插入诗词数据
        poems = self.load_all_json_files()
        poem_count = 0
        if poems:
            poem_count = self.batch_insert_poems(poems, start_id=1)

        logger.info(f"数据库初始化完成 - 作者：{author_count}, 诗词：{poem_count}")
        return {
            'authors': author_count,
            'poems': poem_count
        }

    # ==================== 资源管理 ====================

    def close(self) -> None:
        """关闭数据库连接"""
        self._storage_engine.disconnect()
        logger.info("数据库连接已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
