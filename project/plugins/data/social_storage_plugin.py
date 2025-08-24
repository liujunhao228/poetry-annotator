"""
《交际诗分析》项目专用数据存储插件
"""

import json
import logging
from typing import List, Dict, Any, Optional
from src.data.plugin_interface import StoragePlugin
from src.data.adapter import DatabaseAdapter
from src.data.separate_databases import SeparateDatabaseManager
from src.config.schema import PluginConfig

logger = logging.getLogger(__name__)

class SocialPoemAnalysisStoragePlugin(StoragePlugin):
    """《交际诗分析》项目专用数据存储插件"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        super().__init__(config, separate_db_manager)
        self.name = "social_poem_analysis_storage"
        self.description = "《交际诗分析》项目专用数据存储插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def save_data(self, data: List[Dict[str, Any]], data_type: str = "default") -> bool:
        """保存数据到数据库"""
        try:
            # 获取标注数据库适配器
            db_adapter = self.separate_db_manager.annotation_db
            
            # 根据数据类型选择不同的处理方式
            if data_type == "social_analysis":
                return self._save_social_analysis_results(db_adapter, data)
            else:
                logger.warning(f"不支持的数据类型: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"保存数据时发生错误: {e}")
            return False
    
    def _save_social_analysis_results(self, db_adapter: DatabaseAdapter, data: List[Dict[str, Any]]) -> bool:
        """保存社交分析结果"""
        # 准备插入语句
        insert_sql = """
        INSERT INTO social_analysis_results 
        (poem_id, sentence_id, relationship_action, emotional_strategy, 
         communication_scene, risk_level, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        # 获取数据库连接
        conn = db_adapter.get_connection()
        cursor = conn.cursor()
        
        try:
            # 批量插入数据
            for item in data:
                # 从item中提取所需字段
                poem_id = item.get('poem_id')
                sentence_id = item.get('id')
                relationship_action = item.get('relationship_action')
                emotional_strategy = item.get('emotional_strategy')
                
                # 处理context_analysis字段
                context_analysis = item.get('context_analysis', {})
                communication_scene = json.dumps(context_analysis.get('communication_scene', []))
                risk_level = context_analysis.get('risk_level')
                
                rationale = item.get('brief_rationale')
                
                # 执行插入
                cursor.execute(
                    insert_sql,
                    (poem_id, sentence_id, relationship_action, emotional_strategy,
                     communication_scene, risk_level, rationale)
                )
            
            # 提交事务
            conn.commit()
            logger.info(f"成功保存 {len(data)} 条社交分析结果")
            return True
            
        except Exception as e:
            logger.error(f"保存社交分析结果时发生错误: {e}")
            conn.rollback()
            return False
        finally:
            # 关闭数据库连接
            db_adapter.close_connection(conn)