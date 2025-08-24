"""
插件化数据管理器
负责协调和管理所有数据相关的插件
"""
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from src.data.plugin_interfaces.core import (
    DataStoragePlugin, 
    DataQueryPlugin, 
    DataProcessingPlugin, 
    AnnotationManagementPlugin
)
from src.data.models import Poem, Author, Annotation
from src.component_system import get_component_system, ComponentType


class PluginBasedDataManager:
    """插件化数据管理器"""
    
    def __init__(self, project_root: Path, db_name: str = "default", source_dir: str = "data/source_json"):
        self.project_root = project_root
        self.db_name = db_name
        self.source_dir = source_dir
        self.logger = logging.getLogger(__name__)
        self.component_system = get_component_system(project_root)
        
        # 获取所有必需的插件
        self._load_plugins()
    
    def _load_plugins(self):
        """加载所有必需的插件"""
        try:
            # 获取数据存储插件
            self.storage_plugin: DataStoragePlugin = self.component_system.get_component(
                "data_storage", db_name=self.db_name
            )
        except Exception as e:
            self.logger.warning(f"无法加载数据存储插件，使用默认实现: {e}")
            from src.data.plugins.default_storage import DefaultStoragePlugin
            self.storage_plugin = DefaultStoragePlugin(self.db_name)
        
        try:
            # 获取数据查询插件
            self.query_plugin: DataQueryPlugin = self.component_system.get_component(
                "data_query", db_name=self.db_name
            )
        except Exception as e:
            self.logger.warning(f"无法加载数据查询插件，使用默认实现: {e}")
            from src.data.plugins.default_query import DefaultQueryPlugin
            self.query_plugin = DefaultQueryPlugin(self.db_name)
        
        try:
            # 获取数据处理插件
            self.processing_plugin: DataProcessingPlugin = self.component_system.get_component(
                "data_processing"
            )
        except Exception as e:
            self.logger.warning(f"无法加载数据处理插件，使用默认实现: {e}")
            from src.data.plugins.default_processing import DefaultProcessingPlugin
            self.processing_plugin = DefaultProcessingPlugin()
        
        try:
            # 获取标注管理插件
            self.annotation_plugin: AnnotationManagementPlugin = self.component_system.get_component(
                "annotation_management", db_name=self.db_name
            )
        except Exception as e:
            self.logger.warning(f"无法加载标注管理插件，使用默认实现: {e}")
            from src.data.plugins.default_annotation_management import DefaultAnnotationManagementPlugin
            self.annotation_plugin = DefaultAnnotationManagementPlugin(self.db_name)
    
    # 数据存储相关方法
    def initialize_database_from_json(self, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        # 首先使用数据处理插件加载数据
        authors = self.processing_plugin.load_author_data(self.source_dir)
        poems = self.processing_plugin.load_all_json_files(self.source_dir)
        
        # 然后使用数据存储插件保存数据
        author_count = self.storage_plugin.batch_insert_authors(authors) if authors else 0
        poem_count = self.storage_plugin.batch_insert_poems(poems, start_id=1) if poems else 0
        
        return {
            'authors': author_count,
            'poems': poem_count
        }
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None, 
                        error_message: Optional[str] = None) -> bool:
        """保存标注结果"""
        return self.storage_plugin.save_annotation(
            poem_id, model_identifier, status, annotation_result, error_message
        )
    
    # 数据查询相关方法
    def get_poems_to_annotate(self, model_identifier: str, 
                             limit: Optional[int] = None, 
                             start_id: Optional[int] = None, 
                             end_id: Optional[int] = None,
                             force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词"""
        return self.query_plugin.get_poems_to_annotate(
            model_identifier, limit, start_id, end_id, force_rerun
        )
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息"""
        return self.query_plugin.get_poem_by_id(poem_id)
    
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息"""
        return self.query_plugin.get_poems_by_ids(poem_ids)
    
    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        return self.query_plugin.get_all_authors()
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页"""
        return self.query_plugin.search_poems(author, title, page, per_page)
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        """高效检查一组 poem_id 是否已被特定模型成功标注"""
        return self.query_plugin.get_completed_poem_ids(poem_ids, model_identifier)
    
    # 标注管理相关方法
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.annotation_plugin.get_statistics()
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        return self.annotation_plugin.get_annotation_statistics()
    
    # 数据处理相关方法
    def load_data_from_json(self, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        return self.processing_plugin.load_data_from_json(self.source_dir, json_file)
    
    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据"""
        return self.processing_plugin.load_all_json_files(self.source_dir)
    
    def load_author_data(self) -> List[Dict[str, Any]]:
        """加载作者数据"""
        return self.processing_plugin.load_author_data(self.source_dir)