"""特定类型插件接口定义"""

import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from abc import abstractmethod
from src.plugin_system.base import BasePlugin


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
    def build_prompts(self, poem_data, emotion_schema, 
                     model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词"""
        # 在函数内部导入，避免循环导入
        from src.llm_services.schemas import PoemData, EmotionSchema
        # 类型检查
        assert isinstance(poem_data, PoemData)
        assert isinstance(emotion_schema, EmotionSchema)
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


class ResponseParsingAndValidationPlugin(BasePlugin):
    """响应解析和验证插件接口"""
    
    def parse_and_validate(self, text: str) -> List[Dict[str, Any]]:
        """
        从字符串中解析并验证JSON数组。
        
        Args:
            text: LLM返回的原始文本。
            
        Returns:
            一个经过完全验证的、包含标注信息的字典列表。
            
        Raises:
            ValueError, TypeError: 如果解析或验证失败。
        """
        pass

class ResponseValidatorPlugin(BasePlugin):
    """响应验证器插件接口"""
    
    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证标注列表的内容。
        
        Args:
            result_list: 解析后的标注列表。
            
        Returns:
            一个经过验证的、包含标注信息的字典列表。
            
        Raises:
            ValueError, TypeError: 如果验证失败。
        """
        pass


class LLMServicePlugin(BasePlugin):
    """LLM服务插件接口"""
    
    @abstractmethod
    async def annotate_poem(self, poem, emotion_schema) -> List[Dict[str, Any]]:
        """处理诗词标注请求"""
        # 在函数内部导入，避免循环导入
        from src.llm_services.schemas import PoemData, EmotionSchema
        # 类型检查
        assert isinstance(poem, PoemData)
        assert isinstance(emotion_schema, EmotionSchema)
        pass
    
    @abstractmethod
    async def annotate_poem_stream(self, poem, emotion_schema) -> str:
        """处理流式诗词标注请求"""
        # 在函数内部导入，避免循环导入
        from src.llm_services.schemas import PoemData, EmotionSchema
        # 类型检查
        assert isinstance(poem, PoemData)
        assert isinstance(emotion_schema, EmotionSchema)
        pass
    
    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        pass