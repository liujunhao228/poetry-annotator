"""
《交际诗分析》项目专用标注管理插件
"""

import json
import logging
from typing import List, Dict, Any, Optional
from src.data.plugin_interface import AnnotationManagementPlugin
from src.data.adapter import DatabaseAdapter
from src.data.separate_databases import SeparateDatabaseManager
from src.config.schema import PluginConfig

logger = logging.getLogger(__name__)

class SocialPoemAnalysisAnnotationManagementPlugin(AnnotationManagementPlugin):
    """《交际诗分析》项目专用标注管理插件"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        super().__init__(config, separate_db_manager)
        self.name = "social_poem_analysis_annotation_management"
        self.description = "《交际诗分析》项目专用标注管理插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def save_annotations(self, poem_id: int, annotations: List[Dict[str, Any]]) -> bool:
        """保存标注结果"""
        try:
            # 获取标注数据库适配器
            db_adapter = self.separate_db_manager.annotation_db
            
            # 开始事务
            db_adapter.begin_transaction()
            
            # 删除已存在的标注（避免重复）
            delete_sql = "DELETE FROM social_analysis_results WHERE poem_id = ?"
            db_adapter.execute_update(delete_sql, (poem_id,))
            
            # 准备插入语句
            insert_sql = """
            INSERT INTO social_analysis_results 
            (poem_id, sentence_id, relationship_action, emotional_strategy, 
             communication_scene, risk_level, rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            # 插入新的标注
            for annotation in annotations:
                sentence_id = annotation.get('id')
                relationship_action = annotation.get('relationship_action')
                emotional_strategy = annotation.get('emotional_strategy')
                
                # 处理context_analysis字段
                context_analysis = annotation.get('context_analysis', {})
                communication_scene = json.dumps(context_analysis.get('communication_scene', []))
                risk_level = context_analysis.get('risk_level')
                
                rationale = annotation.get('brief_rationale')
                
                # 执行插入
                db_adapter.execute_update(
                    insert_sql,
                    (poem_id, sentence_id, relationship_action, emotional_strategy,
                     communication_scene, risk_level, rationale)
                )
            
            # 提交事务
            db_adapter.commit()
            logger.info(f"成功保存诗歌 {poem_id} 的 {len(annotations)} 条标注结果")
            return True
            
        except Exception as e:
            logger.error(f"保存标注结果时发生错误: {e}")
            db_adapter.rollback()
            return False
    
    def get_annotations(self, poem_id: int) -> List[Dict[str, Any]]:
        """获取标注结果"""
        try:
            # 获取标注数据库适配器
            db_adapter = self.separate_db_manager.annotation_db
            
            # 查询SQL
            query_sql = """
            SELECT 
                id,
                sentence_id,
                relationship_action,
                emotional_strategy,
                communication_scene,
                risk_level,
                rationale,
                created_at
            FROM social_analysis_results 
            WHERE poem_id = ?
            ORDER BY sentence_id
            """
            
            # 执行查询
            rows = db_adapter.execute_query(query_sql, (poem_id,))
            
            # 转换为字典列表
            annotations = []
            for row in rows:
                # 解析communication_scene字段
                try:
                    communication_scene = json.loads(row['communication_scene'])
                except (json.JSONDecodeError, TypeError):
                    communication_scene = []
                
                annotation = {
                    'id': row['sentence_id'],
                    'relationship_action': row['relationship_action'],
                    'emotional_strategy': row['emotional_strategy'],
                    'context_analysis': {
                        'communication_scene': communication_scene,
                        'risk_level': row['risk_level']
                    },
                    'brief_rationale': row['rationale'],
                    'created_at': row['created_at']
                }
                annotations.append(annotation)
            
            logger.info(f"成功获取诗歌 {poem_id} 的 {len(annotations)} 条标注结果")
            return annotations
            
        except Exception as e:
            logger.error(f"获取标注结果时发生错误: {e}")
            return []
    
    def delete_annotations(self, poem_id: int) -> bool:
        """删除标注结果"""
        try:
            # 获取标注数据库适配器
            db_adapter = self.separate_db_manager.annotation_db
            
            # 删除SQL
            delete_sql = "DELETE FROM social_analysis_results WHERE poem_id = ?"
            
            # 执行删除
            db_adapter.execute_update(delete_sql, (poem_id,))
            
            logger.info(f"成功删除诗歌 {poem_id} 的标注结果")
            return True
            
        except Exception as e:
            logger.error(f"删除标注结果时发生错误: {e}")
            return False
    
    def update_annotation_status(self, poem_id: int, status: str) -> bool:
        """更新标注状态（如需要）"""
        # 在当前实现中，我们没有单独的标注状态表
        # 如果需要可以扩展此功能
        logger.info(f"更新诗歌 {poem_id} 的标注状态为 {status}（此功能暂未实现）")
        return True
    
    def get_annotation_status(self, poem_id: int) -> str:
        """获取标注状态（如需要）"""
        # 在当前实现中，我们没有单独的标注状态表
        # 如果需要可以扩展此功能
        logger.info(f"获取诗歌 {poem_id} 的标注状态（此功能暂未实现）")
        return "unknown"