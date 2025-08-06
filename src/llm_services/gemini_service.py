import asyncio
import json
import logging
from typing import Dict, Any, Optional, List

# 使用新的库和类型定义
from google import genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base_service import BaseLLMService


class GeminiService(BaseLLMService):
    """Google Gemini API服务实现（已重构）"""
    
    def __init__(self, provider: str, api_key: str, base_url: str, model: str, 
                 temperature: float = 0.3, max_tokens: int = 1000,
                 timeout: int = 30, top_p: float = 1.0, top_k: int = 40,
                 candidate_count: int = 1, stop_sequences: Optional[List[str]] = None,
                 model_config_name: str = None, **kwargs): # 使用kwargs接收未知参数
        super().__init__(provider, api_key, base_url, model, model_config_name)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.top_p = top_p
        self.top_k = top_k
        self.candidate_count = candidate_count
        self.stop_sequences = stop_sequences or []
        
        # 处理 thinking_budget 参数 - 仅支持 gemini-2.5-pro 模型
        self.thinking_budget = None
        if 'thinking_budget' in kwargs:
            if model == "models/gemini-2.5-pro":
                self.thinking_budget = kwargs['thinking_budget']
                self.logger.info(f"GeminiService: 为 gemini-2.5-pro 模型设置 thinking_budget: {self.thinking_budget}")
            else:
                self.logger.warning(f"GeminiService: 'thinking_budget' 参数仅支持 gemini-2.5-pro 模型，当前模型 {model} 将忽略此参数。")
        
        # 配置Gemini API
        genai.configure(api_key=api_key)
        
        # 初始化Gemini模型
        try:
            # 使用字典构建生成配置 (更现代的方式)
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "candidate_count": self.candidate_count,
            }
            
            # 如果有停止序列，添加到配置中
            if self.stop_sequences:
                generation_config["stop_sequences"] = self.stop_sequences
            
            # 为诗词分析设置宽松的安全策略，防止误判
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            self.genai_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            self.logger.error(f"初始化Gemini模型失败: {e}")
            raise
        
        self.logger.info(f"Gemini服务初始化完成 - 模型: {model}, 温度: {temperature}, 最大token: {max_tokens}, top_p: {top_p}, top_k: {top_k}")

    async def annotate_poem(self, prompt: str) -> Dict[str, Any]:
        """
        使用Gemini API标注诗词（采用原生异步方法）
        
        Args:
            prompt: 包含诗词内容的提示词
            
        Returns:
            包含标注结果的字典
        """
        request_data = None # 在try块之外初始化
        try:
            self.logger.debug(f"开始调用Gemini API (原生异步) - 模型: {self.genai_model.model_name}")
            
            # 构建请求数据用于日志记录
            request_data = {
                "model": self.genai_model.model_name,
                "generation_config": self.genai_model.generation_config,
                "safety_settings": self.genai_model.safety_settings,
                "contents": prompt
            }
            self.log_request_details(request_data, prompt)
            
            # 构建请求选项
            request_options = {'timeout': self.timeout}
            
            # 如果是 gemini-2.5-pro 模型且设置了 thinking_budget，添加到请求选项中
            if self.thinking_budget is not None and self.model == "models/gemini-2.5-pro":
                request_options['thinking_budget'] = self.thinking_budget
            
            # 直接使用原生异步方法，不再需要 chat session 和 asyncio.to_thread
            response = await self.genai_model.generate_content_async(
                prompt,
                request_options=request_options
            )
            
            # 提取响应内容
            response_text = response.text
            
            # 构建响应数据用于日志记录
            response_data = {
                "text": response_text,
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": part.text} for part in response.parts]
                        },
                        "finish_reason": candidate.finish_reason.name,
                        "index": candidate.index,
                        "token_count": candidate.token_count
                    }
                    for candidate in response.candidates
                ],
                "usage_metadata": response.usage_metadata
            }
            
            # 记录完整的响应详情
            usage = response.usage_metadata
            self.log_response_details(response_data, response_text, usage)
            
            self.logger.debug(f"Gemini API调用成功")
            
            # 统一调用基类的验证和解析方法
            return self.validate_response(response_text)
            
        except Exception as e:
            self.logger.error(f"Gemini API调用失败: {e}", exc_info=True)
            # 记录错误详情
            self.log_error_details(e, request_data, prompt)
            # 根据tenacity的策略，这里重新抛出异常以触发重试
            raise
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        config = self.genai_model.generation_config
        service_info = {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": config.get("temperature"),
            "max_tokens": config.get("max_output_tokens"),
            "timeout": self.timeout,
            "top_p": config.get("top_p"),
            "top_k": config.get("top_k"),
            "candidate_count": config.get("candidate_count"),
            "stop_sequences": config.get("stop_sequences"),
        }
        
        # 如果是 gemini-2.5-pro 模型且设置了 thinking_budget，添加到服务信息中
        if self.thinking_budget is not None and self.model == "models/gemini-2.5-pro":
            service_info["thinking_budget"] = self.thinking_budget
            
        return service_info
