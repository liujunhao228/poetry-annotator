# src/llm_services/schemas.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# --- Data Transfer Objects (DTOs) for LLM Services ---

@dataclass
class PoemData:
    """诗词数据传输对象"""
    id: str
    author: str
    title: str
    paragraphs: List[str]

@dataclass
class EmotionSchema:
    """情感分类体系数据传输对象"""
    text: str

@dataclass
class AnnotationResult:
    """标准化的标注结果"""
    poem_id: str
    status: str # 'completed' or 'failed'
    results: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None

# --- Configuration Schemas ---

@dataclass
class BaseLLMConfig:
    """基础LLM配置"""
    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    qps: Optional[float] = None
    rpm: Optional[float] = None
    max_concurrent: Optional[int] = None
    burst: Optional[int] = None

@dataclass
class OpenAIConfig(BaseLLMConfig):
    """OpenAI兼容API的配置"""
    temperature: float = 0.3
    max_tokens: int = 1000
    timeout: int = 30
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    n: int = 1
    stop: Optional[List[str]] = None
    response_format: Optional[Dict[str, str]] = None
    stream: bool = False
    logit_bias: Optional[Dict[str, float]] = None
    rate_limit: Optional[RateLimitConfig] = None
    request_delay: float = 0.0

@dataclass
class GeminiConfig(BaseLLMConfig):
    """Gemini API的配置"""
    temperature: float = 0.3
    max_tokens: int = 65535
    timeout: int = 120
    top_p: float = 1.0
    top_k: int = 40
    candidate_count: int = 1
    stop_sequences: Optional[List[str]] = None
    thinking_budget: Optional[int] = None
    rate_limit: Optional[RateLimitConfig] = None
    request_delay: float = 0.0

@dataclass
class DashScopeConfig(OpenAIConfig):
    """DashScope API的配置 (继承自OpenAI)"""
    enable_search: bool = False
    result_format: str = "message"
    incremental_output: bool = False
    enable_thinking: bool = False

@dataclass
class SiliconFlowConfig(OpenAIConfig):
    """SiliconFlow API的配置 (继承自OpenAI)"""
    top_k: Optional[int] = None
    seed: Optional[int] = None
    response_adapter: Optional[str] = None

# --- Service Response Schemas ---

@dataclass
class ServiceHealth:
    """服务健康检查响应"""
    is_healthy: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceInfo:
    """服务信息响应"""
    provider: str
    model: str
    base_url: Optional[str]
    # Add other common fields as needed
    extra_info: Dict[str, Any] = field(default_factory=dict)
