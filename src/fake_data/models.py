"""假数据模型定义"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from src.llm_services.schemas import PoemData, EmotionSchema


@dataclass
class FakeAnnotation:
    """假的标注结果"""
    id: str
    primary: str
    secondary: List[str]


@dataclass
class FakeLLMConfig:
    """假LLM配置"""
    response_delay: float = 0.1  # 模拟响应延迟(秒)
    error_rate: float = 0.0      # 模拟错误率(0.0-1.0)
    fixed_response: Optional[List[FakeAnnotation]] = None  # 固定响应，如果提供则总是返回此响应