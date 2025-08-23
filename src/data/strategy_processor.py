"""
策略标注数据处理模块
"""
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import json

from src.data.models import Annotation, SentenceAnnotation
from src.data.models_sentence_strategy_link import SentenceStrategyLink


class StrategyAnnotationProcessor:
    """策略标注数据处理器"""
    
    @staticmethod
    def create_annotation_record(poem_id: int, model_identifier: str, status: str = "completed") -> Annotation:
        """
        创建标注记录
        
        Args:
            poem_id: 诗词ID
            model_identifier: 模型标识符
            status: 标注状态
            
        Returns:
            Annotation: 标注记录对象
        """
        return Annotation(
            id=None,
            poem_id=poem_id,
            model_identifier=model_identifier,
            status=status
        )
    
    @staticmethod
    def create_sentence_annotations(annotation_id: int, poem_id: int, sentences: List[Dict[str, Any]]) -> List[SentenceAnnotation]:
        """
        创建句子标注记录
        
        Args:
            annotation_id: 标注ID
            poem_id: 诗词ID
            sentences: 句子数据列表，每个元素包含'id'和'sentence'键
            
        Returns:
            List[SentenceAnnotation]: 句子标注记录列表
        """
        sentence_annotations = []
        for sentence_data in sentences:
            sentence_annotation = SentenceAnnotation(
                id=None,
                annotation_id=annotation_id,
                poem_id=poem_id,
                sentence_uid=sentence_data["id"],
                sentence_text=sentence_data["sentence"]
            )
            sentence_annotations.append(sentence_annotation)
        
        return sentence_annotations
    
    @staticmethod
    def create_strategy_links(sentence_annotation_id: int, strategy_data: Dict[str, Any]) -> List[SentenceStrategyLink]:
        """
        创建句子策略链接记录
        
        Args:
            sentence_annotation_id: 句子标注ID
            strategy_data: 策略数据，包含relationship_action, emotional_strategy, context_analysis等字段
            
        Returns:
            List[SentenceStrategyLink]: 句子策略链接记录列表
        """
        strategy_links = []
        
        # 关系动作
        if "relationship_action" in strategy_data:
            link = SentenceStrategyLink(
                sentence_annotation_id=sentence_annotation_id,
                strategy_id=strategy_data["relationship_action"],
                strategy_type="relationship_action",
                is_primary=True
            )
            strategy_links.append(link)
        
        # 情感策略
        if "emotional_strategy" in strategy_data:
            link = SentenceStrategyLink(
                sentence_annotation_id=sentence_annotation_id,
                strategy_id=strategy_data["emotional_strategy"],
                strategy_type="emotional_strategy",
                is_primary=True
            )
            strategy_links.append(link)
        
        # 传播场景
        if "context_analysis" in strategy_data and "communication_scene" in strategy_data["context_analysis"]:
            for scene in strategy_data["context_analysis"]["communication_scene"]:
                link = SentenceStrategyLink(
                    sentence_annotation_id=sentence_annotation_id,
                    strategy_id=scene,
                    strategy_type="communication_scene",
                    is_primary=(scene == strategy_data["context_analysis"]["communication_scene"][0])
                )
                strategy_links.append(link)
        
        # 风险等级
        if "context_analysis" in strategy_data and "risk_level" in strategy_data["context_analysis"]:
            link = SentenceStrategyLink(
                sentence_annotation_id=sentence_annotation_id,
                strategy_id=strategy_data["context_analysis"]["risk_level"],
                strategy_type="risk_level",
                is_primary=True
            )
            strategy_links.append(link)
        
        return strategy_links
    
    @staticmethod
    def convert_to_annotation_result(sentence_annotations: List[SentenceAnnotation], 
                                   strategy_links: List[SentenceStrategyLink]) -> str:
        """
        将句子标注和策略链接转换为标注结果JSON字符串
        
        Args:
            sentence_annotations: 句子标注记录列表
            strategy_links: 句子策略链接记录列表
            
        Returns:
            str: 标注结果JSON字符串
        """
        # 构建句子标注ID到策略链接的映射
        links_by_sentence = {}
        for link in strategy_links:
            if link.sentence_annotation_id not in links_by_sentence:
                links_by_sentence[link.sentence_annotation_id] = []
            links_by_sentence[link.sentence_annotation_id].append(link)
        
        # 构建结果数据
        result_sentences = []
        for sentence_annotation in sentence_annotations:
            sentence_data = {
                "id": sentence_annotation.sentence_uid,
                "sentence": sentence_annotation.sentence_text
            }
            
            # 添加策略数据
            if sentence_annotation.id in links_by_sentence:
                links = links_by_sentence[sentence_annotation.id]
                
                # 关系动作
                relationship_actions = [link.strategy_id for link in links if link.strategy_type == "relationship_action"]
                if relationship_actions:
                    sentence_data["relationship_action"] = relationship_actions[0]
                
                # 情感策略
                emotional_strategies = [link.strategy_id for link in links if link.strategy_type == "emotional_strategy"]
                if emotional_strategies:
                    sentence_data["emotional_strategy"] = emotional_strategies[0]
                
                # 传播场景和风险等级
                communication_scenes = [link.strategy_id for link in links if link.strategy_type == "communication_scene"]
                risk_levels = [link.strategy_id for link in links if link.strategy_type == "risk_level"]
                
                if communication_scenes or risk_levels:
                    sentence_data["context_analysis"] = {}
                    
                    if communication_scenes:
                        sentence_data["context_analysis"]["communication_scene"] = communication_scenes
                    
                    if risk_levels:
                        sentence_data["context_analysis"]["risk_level"] = risk_levels[0]
            
            result_sentences.append(sentence_data)
        
        return json.dumps(result_sentences, ensure_ascii=False, indent=2)