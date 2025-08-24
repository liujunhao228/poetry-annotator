"""
《交际诗分析》项目专用数据处理插件
"""

import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.plugin_interface import ProcessingPlugin
from src.data.adapter import DatabaseAdapter
from src.data.separate_databases import SeparateDatabaseManager
from src.config.schema import PluginConfig

logger = logging.getLogger(__name__)

class SocialPoemAnalysisProcessingPlugin(ProcessingPlugin):
    """《交际诗分析》项目专用数据处理插件"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        super().__init__(config, separate_db_manager)
        self.name = "social_poem_analysis_processing"
        self.description = "《交际诗分析》项目专用数据处理插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def process_data(self, data: List[Dict[str, Any]], processing_type: str = "default") -> List[Dict[str, Any]]:
        """处理数据"""
        try:
            # 根据处理类型选择不同的处理方式
            if processing_type == "social_analysis":
                return self._process_social_analysis_results(data)
            else:
                logger.warning(f"不支持的数据处理类型: {processing_type}")
                return data
                
        except Exception as e:
            logger.error(f"处理数据时发生错误: {e}")
            return data
    
    def _process_social_analysis_results(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理社交分析结果"""
        try:
            processed_data = []
            
            # 处理每条数据
            for item in data:
                # 创建处理后的项
                processed_item = item.copy()
                
                # 解析communication_scene字段（JSON数组）
                communication_scene = item.get('context_analysis', {}).get('communication_scene', [])
                if isinstance(communication_scene, str):
                    try:
                        processed_item['communication_scene_list'] = json.loads(communication_scene)
                    except (json.JSONDecodeError, TypeError):
                        processed_item['communication_scene_list'] = []
                else:
                    processed_item['communication_scene_list'] = communication_scene
                
                # 添加场景描述
                scene_descriptions = {
                    "SC01": "密室私语",
                    "SC02": "沙龙展演", 
                    "SC03": "广场广播",
                    "SC04": "权力剧场"
                }
                
                processed_item['communication_scene_descriptions'] = [
                    scene_descriptions.get(scene, scene) 
                    for scene in processed_item['communication_scene_list']
                ]
                
                # 添加维度描述
                ra_descriptions = {
                    "RA01": "情感充值",
                    "RA02": "资源请求", 
                    "RA03": "身份认证",
                    "RA04": "危机公关",
                    "RA05": "价值展示",
                    "RA06": "权力应答",
                    "RA07": "加密传讯",
                    "RA08": "情绪爆破"
                }
                
                es_descriptions = {
                    "ES01": "暴雨式",
                    "ES02": "针灸式",
                    "ES03": "迷雾式",
                    "ES04": "糖衣式"
                }
                
                rs_descriptions = {
                    "RS01": "安全牌",
                    "RS02": "杠杆牌",
                    "RS03": "炸弹牌"
                }
                
                processed_item['relationship_action_description'] = ra_descriptions.get(
                    item.get('relationship_action'), 
                    item.get('relationship_action')
                )
                
                processed_item['emotional_strategy_description'] = es_descriptions.get(
                    item.get('emotional_strategy'), 
                    item.get('emotional_strategy')
                )
                
                processed_item['risk_level_description'] = rs_descriptions.get(
                    item.get('context_analysis', {}).get('risk_level'), 
                    item.get('context_analysis', {}).get('risk_level')
                )
                
                processed_data.append(processed_item)
            
            logger.info(f"成功处理 {len(processed_data)} 条社交分析结果")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理社交分析结果时发生错误: {e}")
            return data
    
    def aggregate_data(self, data: List[Dict[str, Any]], aggregation_type: str = "default") -> Dict[str, Any]:
        """聚合数据"""
        try:
            # 根据聚合类型选择不同的聚合方式
            if aggregation_type == "social_analysis_summary":
                return self._aggregate_social_analysis_summary(data)
            else:
                logger.warning(f"不支持的数据聚合类型: {aggregation_type}")
                return {}
                
        except Exception as e:
            logger.error(f"聚合数据时发生错误: {e}")
            return {}
    
    def _aggregate_social_analysis_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合社交分析摘要"""
        try:
            # 初始化计数器
            ra_counts = {}
            es_counts = {}
            sc_counts = {}
            rs_counts = {}
            
            # 统计各维度的分布
            for item in data:
                # 统计关系动作
                ra = item.get('relationship_action')
                if ra:
                    ra_counts[ra] = ra_counts.get(ra, 0) + 1
                
                # 统计情感策略
                es = item.get('emotional_strategy')
                if es:
                    es_counts[es] = es_counts.get(es, 0) + 1
                
                # 统计传播场景
                context_analysis = item.get('context_analysis', {})
                scenes = context_analysis.get('communication_scene', [])
                # 处理字符串格式的JSON数组
                if isinstance(scenes, str):
                    try:
                        scenes = json.loads(scenes)
                    except (json.JSONDecodeError, TypeError):
                        scenes = []
                
                for scene in scenes:
                    sc_counts[scene] = sc_counts.get(scene, 0) + 1
                
                # 统计风险等级
                rs = context_analysis.get('risk_level')
                if rs:
                    rs_counts[rs] = rs_counts.get(rs, 0) + 1
            
            # 构建聚合结果
            aggregation_result = {
                "total_count": len(data),
                "relationship_action_distribution": ra_counts,
                "emotional_strategy_distribution": es_counts,
                "communication_scene_distribution": sc_counts,
                "risk_level_distribution": rs_counts
            }
            
            logger.info("成功聚合社交分析摘要")
            return aggregation_result
            
        except Exception as e:
            logger.error(f"聚合社交分析摘要时发生错误: {e}")
            return {}