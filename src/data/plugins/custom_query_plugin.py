"""
自定义查询插件示例
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.plugin_interface import QueryPlugin
from src.config.schema import PluginConfig


class CustomQueryPlugin(QueryPlugin):
    """自定义查询插件示例"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional['SeparateDatabaseManager'] = None):
        super().__init__(config, separate_db_manager)
        self.name = "custom_query"
        self.description = "自定义查询示例"
    
    def get_name(self) -> str:
        return self.name
    
    def get_description(self) -> str:
        return self.description
    
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行自定义查询"""
        # 检查是否提供了分离数据库管理器
        if not self.separate_db_manager:
            raise ValueError("未提供分离数据库管理器")
        
        # 获取参数
        query_type = params.get('type') if params else 'poem'
        
        # 根据查询类型选择不同的数据库
        if query_type == 'annotation':
            # 查询标注数据
            db_adapter = self.separate_db_manager.annotation_db
            query = "SELECT * FROM annotations LIMIT 10"
        elif query_type == 'emotion':
            # 查询情感分类数据
            db_adapter = self.separate_db_manager.emotion_db
            query = "SELECT * FROM emotion_categories LIMIT 10"
        else:
            # 默认查询原始数据
            db_adapter = self.separate_db_manager.raw_data_db
            query = "SELECT id, title, author FROM poems LIMIT 10"
        
        # 执行查询
        rows = db_adapter.execute_query(query)
        
        # 转换为DataFrame
        if rows:
            columns = list(rows[0].keys()) if hasattr(rows[0], 'keys') else [f"col_{i}" for i in range(len(rows[0]))]
            df = pd.DataFrame([dict(row) for row in rows], columns=columns)
        else:
            df = pd.DataFrame()
            
        return df
    
    def get_required_params(self) -> List[str]:
        return []