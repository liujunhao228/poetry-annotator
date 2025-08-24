"""
核心数据管理插件接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from src.data.models import Poem, Author, Annotation


class DataStoragePlugin(ABC):
    """数据存储插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def initialize_database_from_json(self, source_dir: str, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        pass
    
    @abstractmethod
    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息"""
        pass
    
    @abstractmethod
    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """批量插入诗词"""
        pass
    
    @abstractmethod
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                       annotation_result: Optional[str] = None, 
                       error_message: Optional[str] = None) -> bool:
        """保存标注结果"""
        pass


class DataQueryPlugin(ABC):
    """数据查询插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_poems_to_annotate(self, model_identifier: str, 
                             limit: Optional[int] = None, 
                             start_id: Optional[int] = None, 
                             end_id: Optional[int] = None,
                             force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词"""
        pass
    
    @abstractmethod
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息"""
        pass
    
    @abstractmethod
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息"""
        pass
    
    @abstractmethod
    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        pass
    
    @abstractmethod
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页"""
        pass
    
    @abstractmethod
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        """高效检查一组 poem_id 是否已被特定模型成功标注"""
        pass


class DataProcessingPlugin(ABC):
    """数据处理插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def load_data_from_json(self, source_dir: str, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        pass
    
    @abstractmethod
    def load_all_json_files(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据"""
        pass
    
    @abstractmethod
    def load_author_data(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载作者数据"""
        pass


class AnnotationManagementPlugin(ABC):
    """标注管理插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        pass
    
    @abstractmethod
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        pass