"""
句子策略链接数据模型
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SentenceStrategyLink:
    """句子策略链接模型"""
    sentence_annotation_id: int
    strategy_id: str
    strategy_type: str  # relationship_action, emotional_strategy, communication_scene, risk_level
    is_primary: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentenceStrategyLink':
        """从字典创建SentenceStrategyLink实例"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'sentence_annotation_id': self.sentence_annotation_id,
            'strategy_id': self.strategy_id,
            'strategy_type': self.strategy_type,
            'is_primary': self.is_primary
        }