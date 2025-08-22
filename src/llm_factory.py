# src/llm_factory.py
from typing import Dict, Any, Optional
import logging
from .config import config_manager
from .llm_services.base_service import BaseLLMService
from .llm_services.siliconflow_service import SiliconFlowService
from .llm_services.gemini_service import GeminiService
from .llm_services.openai_service import OpenAIService
from .llm_services.dashscope_adapter import DashScopeAdapter

from pybreaker import CircuitBreaker

class LLMFactory:
    """LLM服务工厂"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # 将创建函数的映射改为类本身的映射，更符合工厂模式
        self.providers: Dict[str, type[BaseLLMService]] = {
            'siliconflow': SiliconFlowService,
            'gemini': GeminiService,
            'openai': OpenAIService,
            'dashscope': DashScopeAdapter,  # 使用适配器
            # 未来可以添加更多提供商
        }
        # --- 熔断器管理 ---
        self.breakers: Dict[str, CircuitBreaker] = {}
        try:
            llm_config = config_manager.get_llm_config()
            # 从配置中读取熔断器参数，并提供默认值
            self.breaker_fail_max = llm_config.get('breaker_fail_max', 5)
            self.breaker_reset_timeout = llm_config.get('breaker_reset_timeout', 60)
            self.logger.info(f"熔断器配置加载: fail_max={self.breaker_fail_max}, reset_timeout={self.breaker_reset_timeout}")
        except Exception as e:
            self.logger.warning(f"加载LLM配置失败，将使用默认熔断器参数: {e}")
            self.breaker_fail_max = 5
            self.breaker_reset_timeout = 60

    def get_breaker(self, config_name: str) -> CircuitBreaker:
        """为指定的模型配置获取或创建熔断器实例"""
        if config_name not in self.breakers:
            # 使用从配置加载的参数创建熔断器
            self.breakers[config_name] = CircuitBreaker(
                fail_max=self.breaker_fail_max,
                reset_timeout=self.breaker_reset_timeout,
                # 为熔断器命名，方便在日志中识别
                name=f"Breaker-{config_name}"
            )
            self.logger.info(f"为模型 '{config_name}' 创建了新的熔断器实例。")
        return self.breakers[config_name]
    
    def get_llm_service(self, config_name: str) -> BaseLLMService:
        """
        根据模型配置别名创建LLM服务实例
        """
        try:
            if not config_name:
                raise ValueError("必须提供模型配置名称")
            model_config = config_manager.get_model_config(config_name)
            provider = model_config.get('provider')
            if not provider:
                raise ValueError(f"模型配置 '{config_name}' 必须包含 'provider' 字段")
            provider = provider.lower()
            
            if provider not in self.providers:
                supported_providers = list(self.providers.keys())
                raise ValueError(f"不支持的提供商: {provider}。支持的提供商: {supported_providers}")
            
            service_class = self.providers[provider]
            service = service_class(
                config=model_config,
                model_config_name=config_name
            )
            
            self.logger.info(f"成功创建 {provider} 服务实例, 配置: {config_name}, 模型: {service.model}")
            return service
            
        except Exception as e:
            self.logger.error(f"创建LLM服务失败: {e}")
            raise ValueError(f"创建LLM服务实例 '{config_name}' 失败: {e}") from e
    
    def list_configured_models(self) -> Dict[str, Dict[str, str]]:
        """列出在config.ini中所有已配置的模型"""
        configured_models = {}
        config_names = config_manager.list_model_configs()
        for name in config_names:
            try:
                cfg = config_manager.get_model_config(name)
                configured_models[name] = {
                    'provider': cfg.get('provider', 'N/A'),
                    'model_name': cfg.get('model_name', 'N/A')
                }
            except Exception as e:
                self.logger.warning(f"加载模型配置 '{name}' 时出错: {e}")
        return configured_models
    
    def validate_config_name(self, config_name: str) -> bool:
        """
        验证模型配置名称是否有效（即是否存在于config.ini中）
        """
        return config_name in config_manager.list_model_configs()
    
    async def get_llm_service_async(self, config_name: str) -> BaseLLMService:
        """
        根据模型配置别名创建LLM服务实例（异步版本）
        """
        try:
            if not config_name:
                raise ValueError("必须提供模型配置名称")
            model_config = config_manager.get_model_config(config_name)
            provider = model_config.get('provider')
            if not provider:
                raise ValueError(f"模型配置 '{config_name}' 必须包含 'provider' 字段")
            provider = provider.lower()
            
            if provider not in self.providers:
                supported_providers = list(self.providers.keys())
                raise ValueError(f"不支持的提供商: {provider}。支持的提供商: {supported_providers}")
            
            service_class = self.providers[provider]
            service = service_class(
                config=model_config,
                model_config_name=config_name
            )
            
            self.logger.info(f"成功创建 {provider} 服务实例, 配置: {config_name}, 模型: {service.model}")
            return service
            
        except Exception as e:
            self.logger.error(f"创建LLM服务失败: {e}")
            raise ValueError(f"创建LLM服务实例 '{config_name}' 失败: {e}") from e


# 全局LLM工厂实例
llm_factory = LLMFactory()
