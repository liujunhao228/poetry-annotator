"""
默认数据管理插件实现
"""
from typing import List, Dict, Any, Optional
from src.data.plugin_interfaces.data_manager import DataManagerPlugin
from src.data.models import Poem, Author, Annotation
from src.data.manager import DataManager


class DefaultDataManagerPlugin(DataManagerPlugin):
    """默认数据管理插件实现"""
    
    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        self.data_manager = DataManager(db_name=db_name)
    
    def get_name(self) -> str:
        return "default_data_manager"
    
    def get_description(self) -> str:
        return "默认数据管理插件实现"
    
    def initialize_database_from_json(self, clear_existing: bool = False) -> Dict[str, int]:
        return self.data_manager.initialize_database_from_json(clear_existing)
    
    def get_poems_to_annotate(self, model_identifier: str, 
                               limit: Optional[int] = None, 
                               start_id: Optional[int] = None, 
                               end_id: Optional[int] = None,
                               force_rerun: bool = False) -> List[Poem]:
        return self.data_manager.get_poems_to_annotate(
            model_identifier, limit, start_id, end_id, force_rerun
        )
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        return self.data_manager.get_poem_by_id(poem_id)
    
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        return self.data_manager.get_poems_by_ids(poem_ids)
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None, 
                        error_message: Optional[str] = None) -> bool:
        return self.data_manager.save_annotation(
            poem_id, model_identifier, status, annotation_result, error_message
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        return self.data_manager.get_statistics()
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        return self.data_manager.get_annotation_statistics()
    
    def get_all_authors(self) -> List[Author]:
        return self.data_manager.get_all_authors()
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        return self.data_manager.search_poems(author, title, page, per_page)
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> set[int]:
        return self.data_manager.get_completed_poem_ids(poem_ids, model_identifier)