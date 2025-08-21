# src/llm_services/exceptions.py

class LLMServiceError(Exception):
    """LLM服务基础异常类"""
    pass

class LLMServiceConfigError(LLMServiceError):
    """LLM服务配置错误"""
    pass

class LLMServiceAuthError(LLMServiceError):
    """LLM服务认证错误"""
    pass

class LLMServiceAPIError(LLMServiceError):
    """LLM服务API调用错误"""
    pass

class LLMServiceRateLimitError(LLMServiceAPIError):
    """LLM服务速率限制错误"""
    pass

class LLMServiceTimeoutError(LLMServiceAPIError):
    """LLM服务超时错误"""
    pass

class LLMServiceResponseError(LLMServiceError):
    """LLM服务响应解析/验证错误"""
    pass