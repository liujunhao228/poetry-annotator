"""
默认数据模型插件实现
"""
from src.data.plugin_interfaces.data_model import DataModelPlugin
from src.data.models import Poem, Author, Annotation


class DefaultDataModelPlugin(DataModelPlugin):
    """默认数据模型插件实现"""
    
    def get_name(self) -> str:
        return "default_data_model"
    
    def get_description(self) -> str:
        return "默认数据模型插件实现"
    
    def get_poem_model(self) -> type:
        return Poem
    
    def get_author_model(self) -> type:
        return Author
    
    def get_annotation_model(self) -> type:
        return Annotation