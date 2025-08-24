"""
《交际诗分析》项目专用数据查询插件
"""

import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.plugin_interface import QueryPlugin
from src.data.adapter import DatabaseAdapter
from src.data.separate_databases import SeparateDatabaseManager
from src.config.schema import PluginConfig

logger = logging.getLogger(__name__)

class SocialPoemAnalysisQueryPlugin(QueryPlugin):
    """《交际诗分析》项目专用数据查询插件"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        super().__init__(config, separate_db_manager)
        self.name = "social_poem_analysis_query"
        self.description = "《交际诗分析》项目专用数据查询插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询"""
        try:
            # 获取标注数据库适配器
            db_adapter = self.separate_db_manager.annotation_db
            
            # 获取查询参数
            query_type = params.get('type', 'social_analysis') if params else 'social_analysis'
            poem_id = params.get('poem_id') if params else None
            
            # 根据查询类型构建SQL查询
            if query_type == "social_analysis":
                return self._query_social_analysis_results(db_adapter, poem_id)
            else:
                logger.warning(f"不支持的查询类型: {query_type}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"查询数据时发生错误: {e}")
            return pd.DataFrame()
    
    def _query_social_analysis_results(self, db_adapter: DatabaseAdapter, poem_id: Optional[int] = None) -> pd.DataFrame:
        """查询社交分析结果"""
        try:
            # 构建基础查询SQL
            base_sql = """
            SELECT 
                sar.id,
                sar.poem_id,
                p.title as poem_title,
                p.author as poem_author,
                sar.sentence_id,
                sar.relationship_action,
                ra.name_zh as relationship_action_name,
                sar.emotional_strategy,
                es.name_zh as emotional_strategy_name,
                sar.communication_scene,
                sar.risk_level,
                rl.name_zh as risk_level_name,
                sar.rationale,
                sar.created_at
            FROM social_analysis_results sar
            LEFT JOIN poems p ON sar.poem_id = p.id
            LEFT JOIN relationship_actions ra ON sar.relationship_action = ra.code
            LEFT JOIN emotional_strategies es ON sar.emotional_strategy = es.code
            LEFT JOIN risk_levels rl ON sar.risk_level = rl.code
            """
            
            # 如果提供了poem_id，则添加WHERE条件
            if poem_id is not None:
                sql = base_sql + " WHERE sar.poem_id = ?"
                rows = db_adapter.execute_query(sql, (poem_id,))
            else:
                sql = base_sql
                rows = db_adapter.execute_query(sql)
            
            # 转换为DataFrame
            if rows:
                # 处理communication_scene字段（JSON数组）
                for row in rows:
                    try:
                        row['communication_scene'] = json.loads(row['communication_scene'])
                    except (json.JSONDecodeError, TypeError):
                        row['communication_scene'] = []
                
                df = pd.DataFrame([dict(row) for row in rows])
            else:
                df = pd.DataFrame()
                
            logger.info(f"成功查询到 {len(df)} 条社交分析结果")
            return df
            
        except Exception as e:
            logger.error(f"查询社交分析结果时发生错误: {e}")
            return pd.DataFrame()
    
    def get_required_params(self) -> List[str]:
        """获取必需的参数列表"""
        # 这个插件没有必需的参数
        return []