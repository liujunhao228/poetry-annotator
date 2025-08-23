"""
增强型数据管理器，支持SQLAlchemy和插件化查询
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.models_sqlalchemy import init_db, get_db, Poem, Author, Annotation
from src.data.plugin_query_manager import PluginBasedQueryManager


class EnhancedDataManager:
    """增强型数据管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        # 初始化SQLAlchemy
        init_db(db_path)
        # 初始化插件化查询管理器
        self.plugin_query_manager = PluginBasedQueryManager(db_path)
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取诗词"""
        with get_db() as db:
            poem = db.query(Poem).filter(Poem.id == poem_id).first()
            if poem:
                return {
                    'id': poem.id,
                    'title': poem.title,
                    'author': poem.author,
                    'paragraphs': poem.paragraphs,
                    'full_text': poem.full_text,
                    'author_desc': poem.author_desc,
                    'data_status': poem.data_status,
                    'pre_classification': poem.pre_classification,
                    'created_at': poem.created_at,
                    'updated_at': poem.updated_at
                }
            return None
    
    def get_annotations_by_poem_id(self, poem_id: int) -> List[Dict[str, Any]]:
        """获取指定诗词的所有标注"""
        with get_db() as db:
            annotations = db.query(Annotation).filter(Annotation.poem_id == poem_id).all()
            return [
                {
                    'id': ann.id,
                    'poem_id': ann.poem_id,
                    'model_identifier': ann.model_identifier,
                    'status': ann.status,
                    'annotation_result': ann.annotation_result,
                    'error_message': ann.error_message,
                    'created_at': ann.created_at,
                    'updated_at': ann.updated_at
                }
                for ann in annotations
            ]
    
    def execute_plugin_query(self, plugin_name: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行插件化查询"""
        return self.plugin_query_manager.execute_query(plugin_name, params)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return self.plugin_query_manager.list_plugins()