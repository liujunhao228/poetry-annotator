# src/llm_factory.py

from typing import Dict, Any, Optional
import logging
from .config_manager import config_manager
# 在文件顶部导入所有具体服务类
from .llm_services.base_service import BaseLLMService
from .llm_services.siliconflow_service import SiliconFlowService
from .llm_services.gemini_service import GeminiService


class LLMFactory:
    """LLM服务工厂"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # [修改] 将创建函数的映射改为类本身的映射，更符合工厂模式
        self.providers: Dict[str, type[BaseLLMService]] = {
            'siliconflow': SiliconFlowService,
            'gemini': GeminiService,
            # 未来可以添加更多提供商
        }
    
    def get_llm_service(self, config_name: str) -> BaseLLMService:
        """
        根据模型配置别名创建LLM服务实例
        
        Args:
            config_name: config.ini中定义的模型别名 (例如 'gpt-4o')
            
        Returns:
            LLM服务实例
            
        Raises:
            ValueError: 当配置别名无效或配置内容不完整时
        """
        try:
            if not config_name:
                raise ValueError("必须提供模型配置名称")

            # 获取模型特定的配置字典
            try:
                model_config = config_manager.get_model_config(config_name)
            except ValueError as e:
                raise ValueError(f"获取模型 '{config_name}' 配置失败: {e}")
            
            # 提取提供商
            provider = model_config.get('provider')
            if not provider:
                raise ValueError(f"模型配置 '{config_name}' 必须包含 'provider' 字段")
            
            provider = provider.lower()
            
            # [修改] 使用类映射动态创建实例
            if provider not in self.providers:
                supported_providers = list(self.providers.keys())
                raise ValueError(f"不支持的提供商: {provider}。支持的提供商: {supported_providers}")
            
            # 获取服务类
            service_class = self.providers[provider]
            
            # [修改] 将完整的配置字典直接传递给服务类的构造函数
            # 服务类自己负责解析和验证配置
            service = service_class(
                config=model_config,
                model_config_name=config_name
            )
            
            self.logger.info(f"成功创建 {provider} 服务实例, 配置: {config_name}, 模型: {service.model}")
            return service
            
        except Exception as e:
            self.logger.error(f"创建LLM服务失败: {e}")
            # 重新抛出更具体的异常
            raise ValueError(f"创建LLM服务实例 '{config_name}' 失败: {e}") from e

    # [已移除] _create_siliconflow_service 和 _create_gemini_service 方法
    # 它们的逻辑现在已经内聚到各自的服务类中。

    # [已移除] _validate_model_config 方法
    # 验证逻辑也已内聚到服务类中。
    
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
    
    def get_service_info(self, config_name: str) -> Dict[str, Any]:
        """
        获取服务信息
        """
        try:
            service = self.get_llm_service(config_name)
            info = service.get_service_info()
            info['config_name'] = config_name
            return info
        except Exception as e:
            try:
                # 如果服务创建失败，从配置文件回退
                model_config = config_manager.get_model_config(config_name)
                model_config['error'] = str(e)
                model_config['config_name'] = config_name
                return model_config
            except Exception as e2:
                return {
                    'error': f"获取服务和配置信息失败: {e}, {e2}",
                    'config_name': config_name
                }


# 全局LLM工厂实例
llm_factory = LLMFactory()
