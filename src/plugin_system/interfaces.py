"""
特定类型插件接口定义
"""

import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from abc import abstractmethod
from src.plugin_system.base import BasePlugin
from src.llm_services.schemas import PoemData, EmotionSchema


class QueryPlugin(BasePlugin):
    """数据查询插件接口"""
    
    @abstractmethod
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询操作"""
        pass
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """获取必需参数列表"""
        pass


class PreprocessingPlugin(BasePlugin):
    """数据预处理插件接口"""
    
    @abstractmethod
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行预处理操作"""
        pass


class PromptBuilderPlugin(BasePlugin):
    """Prompt构建插件接口"""
    
    @abstractmethod
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                     model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词"""
        pass


class LabelParserPlugin(BasePlugin):
    """标签解析插件接口"""
    
    @abstractmethod
    def get_categories(self) -> Dict[str, Any]:
        """获取插件提供的额外分类信息"""
        pass
    
    def extend_category_data(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """扩展分类数据"""
        extended = categories.copy()
        plugin_categories = self.get_categories()
        
        # 合并分类信息
        for category_id, category_data in plugin_categories.items():
            if category_id not in extended:
                extended[category_id] = category_data
            else:
                # 合并现有分类和插件分类信息
                extended[category_id].update(category_data)
        
        return extended


class DatabaseInitPlugin(BasePlugin):
    """数据库初始化插件接口"""
    
    @abstractmethod
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库"""
        pass
    
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法"""
        pass


class DataStoragePlugin(BasePlugin):
    """数据存储插件接口"""
    pass


class DataQueryPlugin(BasePlugin):
    """数据查询插件接口"""
    pass


class DataProcessingPlugin(BasePlugin):
    """数据处理插件接口"""
    pass


class AnnotationManagementPlugin(BasePlugin):
    """标注管理插件接口"""
    pass