"""
默认标注管理插件实现
"""
import logging
from typing import List, Dict, Any, Optional
from src.data.plugin_interfaces.core import AnnotationManagementPlugin
from src.data.separate_databases import get_separate_db_manager


class DefaultAnnotationManagementPlugin(AnnotationManagementPlugin):
    """默认标注管理插件实现"""
    
    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)
        # 获取分离数据库管理器
        self.separate_db_manager = get_separate_db_manager(db_name)
    
    def get_name(self) -> str:
        return "default_annotation_management"
    
    def get_description(self) -> str:
        return "默认标注管理插件实现"
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        self.logger.debug("开始获取数据库统计信息...")
        
        # 总诗词数量
        rows = self.separate_db_manager.raw_data_db.execute_query("SELECT COUNT(*) FROM poems")
        total_poems = rows[0][0]
        
        # 总作者数
        rows = self.separate_db_manager.raw_data_db.execute_query("SELECT COUNT(*) FROM authors")
        total_authors = rows[0][0]
        
        # 按模型和状态统计标注数量
        rows = self.separate_db_manager.annotation_db.execute_query("""
            SELECT model_identifier, status, COUNT(*) 
            FROM annotations 
            GROUP BY model_identifier, status
        """)
        model_status_counts = rows
        
        # 格式化模型统计
        stats_by_model = {}
        for model, status, count in model_status_counts:
            if model not in stats_by_model:
                stats_by_model[model] = {'completed': 0, 'failed': 0, 'total_annotated': 0}
            stats_by_model[model][status] = count
            stats_by_model[model]['total_annotated'] += count
        
        self.logger.debug(f"统计信息获取完成 - 诗词: {total_poems}, 作者: {total_authors}, 模型数: {len(stats_by_model)}")
        
        return {
            'total_poems': total_poems,
            'total_authors': total_authors,
            'stats_by_model': stats_by_model
        }
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        # 获取总体统计
        rows = self.separate_db_manager.raw_data_db.execute_query("""
            SELECT 
                COUNT(DISTINCT p.id) as total_poems,
                COUNT(a.id) as total_annotations,
                COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_annotations,
                COUNT(CASE WHEN a.status = 'failed' THEN 1 END) as failed_annotations
            FROM poems p
            LEFT JOIN annotations a ON p.id = a.poem_id
        """)
        
        overall_stats = rows[0]
        
        # 按模型统计
        model_stats = self.separate_db_manager.annotation_db.execute_query("""
            SELECT 
                model_identifier,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM annotations
            GROUP BY model_identifier
            ORDER BY model_identifier
        """)
        
        # 按状态统计
        status_stats = self.separate_db_manager.annotation_db.execute_query("""
            SELECT 
                status,
                COUNT(*) as count
            FROM annotations
            GROUP BY status
        """)
        
        return {
            'overall': {
                'total_poems': overall_stats[0],
                'total_annotations': overall_stats[1],
                'completed_annotations': overall_stats[2],
                'failed_annotations': overall_stats[3],
                'success_rate': (overall_stats[2] / overall_stats[1] * 100) if overall_stats[1] > 0 else 0
            },
            'by_model': {
                model: {
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'success_rate': (completed / total * 100) if total > 0 else 0
                }
                for model, total, completed, failed in model_stats
            },
            'by_status': {
                status: count for status, count in status_stats
            }
        }