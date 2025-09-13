# src/llm_services/gemini_service.py

import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
import httpx

# 使用新的 Google Gemini Python SDK
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from google.api_core import exceptions as google_exceptions

from .base_service import BaseLLMService
from .schemas import PoemData, EmotionSchema
from .exceptions import LLMServiceAPIError, LLMServiceTimeoutError, LLMServiceRateLimitError
from ..response_parsing.llm_response_parser import LLMResponseParser


class GeminiService(BaseLLMService):
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # Gemini SDK不需要显式关闭连接
        # 调用父类的__aexit__
        await super().__aexit__(exc_type, exc_val, exc_tb)
    """
    Google Gemini API 服务实现 (已重构)
    
    此类与项目架构对齐，负责解析、验证和管理自身的配置，
    并实现 BaseLLMService 定义的统一接口。
    """


    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser: Optional[LLMResponseParser] = None):

        super().__init__(config, model_config_name, response_parser)
        self._parse_and_validate_config()
        self._initialize_gemini_model()
        self._log_initialization()

    def _parse_and_validate_config(self):
        self.temperature = float(self.config.get('temperature', 0.3))
        self.max_tokens = int(self.config.get('max_tokens', 65535))
        self.timeout = int(self.config.get('timeout', 120))
        self.top_p = float(self.config.get('top_p', 1.0))
        self.top_k = int(self.config.get('top_k', 40))
        self.candidate_count = int(self.config.get('candidate_count', 1))

        if not (0.0 <= self.temperature <= 2.0): raise ValueError("temperature 必须在 0.0 和 2.0 之间。")
        if self.max_tokens <= 0: raise ValueError("max_tokens 必须大于 0。")
        if self.timeout <= 0: raise ValueError("timeout 必须大于 0。")

        stop_raw = self.config.get('stop_sequences')
        self.stop_sequences = [s.strip() for s in stop_raw.split(',') if s.strip()] if stop_raw else None

        self.thinking_budget = self.config.get('thinking_budget')
        if self.thinking_budget:
            self.thinking_budget = int(self.thinking_budget)
            if "gemini-2.5-pro" not in self.model: # Note: This check might be too simple
                self.logger.warning(f"'thinking_budget' 参数仅建议用于 gemini-2.5-pro，当前模型为 '{self.model}'。")
                
    def _initialize_gemini_model(self):
        try:
            genai.configure(api_key=self.api_key)
            
            self.generation_config_dict = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "candidate_count": self.candidate_count,
            }
            if self.stop_sequences:
                self.generation_config_dict["stop_sequences"] = self.stop_sequences

            self.generation_config = genai.types.GenerationConfig(**self.generation_config_dict)

            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            self.safety_settings_dict = {k.name: v.name for k, v in safety_settings.items()}

            self.genai_model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self.generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            self.logger.error(f"初始化 Gemini 模型失败: {e}", exc_info=True)
            raise ValueError(f"初始化Gemini模型时出错: {e}") from e
            
    def _log_initialization(self):
        self.logger.info(f"[Gemini] 服务初始化完成 - 模型: {self.model}")
        params_summary = (
            f"温度: {self.temperature}, 最大token: {self.max_tokens}, 超时: {self.timeout}s, "
            f"top_p: {self.top_p}, top_k: {self.top_k}, 停止序列: {self.stop_sequences}, "
            f"thinking_budget: {self.thinking_budget or 'N/A'}"
        )
        self.logger.debug(f"[Gemini] 详细初始化参数: {params_summary}")

    async def health_check(self) -> Tuple[bool, str]:
        self.logger.info(f"对模型 '{self.model}' 执行健康检查...")
        try:
            # 使用一个非常轻量级的API调用来测试连通性
            # Gemini 的 countTokens 是一个很好的选择
            async with httpx.AsyncClient() as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:countTokens?key={self.api_key}"
                response = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": "hello"}]}]},
                    headers={"Content-Type": "application/json"},
                    timeout=10  # 使用较短的超时
                )
                response.raise_for_status() # 检查是否有HTTP错误
                self.logger.info("健康检查成功: API连接和密钥有效。")
                return True, "API connection and key are valid."
        except httpx.HTTPStatusError as e:
            error_message = f"健康检查失败: HTTP {e.response.status_code}. 响应: {e.response.text}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"健康检查失败: 发生未知错误 - {type(e).__name__}: {e}"
            self.logger.error(error_message, exc_info=True)
            return False, error_message

    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        使用 Gemini API 标注一首诗词。
        """
        request_data_for_log = None
        full_prompt = "提示词未生成"
        try:
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            request_options = {'timeout': self.timeout}
            if self.thinking_budget:
                request_options['thinking_budget'] = self.thinking_budget
            
            request_data_for_log = {
                "model_name": self.genai_model.model_name,
                "generation_config": self.generation_config_dict,
                "safety_settings": self.safety_settings_dict,
                "request_options": request_options
            }
            self.log_request_details(request_data_for_log, headers={"Authorization": f"Bearer {self._mask_api_key(self.api_key)}"}, prompt=full_prompt)

            # --- 应用速率控制器 ---
            await self._ensure_rate_controller()
            if self.rate_controller:
                await self.rate_controller.acquire()
            
            # --- 应用请求间延迟 ---
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            response = await self.genai_model.generate_content_async(
                full_prompt,
                request_options=request_options
            )
            
            response_text = response.text
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count,
                }
            
            self.log_response_details(
                poem_id=poem.id,
                parsed_data=None, # In non-stream, this would be the result
                response_data=response.to_dict(),
                response_text=response_text,
                usage=usage
            )

            return self.validate_response(response_text)
            
        except (google_exceptions.RetryError, google_exceptions.DeadlineExceeded) as e:
            self.logger.warning(f"[Gemini] API 连接/超时错误: {e}")
            self.log_error_details(poem.id, e, request_data_for_log, full_prompt)
            raise LLMServiceTimeoutError(f"Gemini API 超时: {e}") from e
        
        except google_exceptions.ResourceExhausted as e:
            self.logger.warning(f"[Gemini] API 速率限制错误: {e}")
            self.log_error_details(poem.id, e, request_data_for_log, full_prompt)
            raise LLMServiceRateLimitError(f"Gemini API 速率限制: {e}") from e

        except (google_exceptions.GoogleAPICallError, google_exceptions.InvalidArgument) as e:
            self.logger.error(f"[Gemini] API 不可重试错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data_for_log, full_prompt)
            raise LLMServiceAPIError(f"Gemini API 调用失败: {e}") from e

        except Exception as e:
            self.logger.error(f"[Gemini] API 调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data_for_log, full_prompt)
            raise LLMServiceAPIError(f"Gemini 未知错误: {e}") from e

    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> AsyncGenerator[str, None]:
        """
        [新增] 使用 Gemini API 流式标注一首诗词。
        """
        request_data_for_log = None
        full_prompt = "提示词未生成"
        try:
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            request_options = {'timeout': self.timeout}
            
            request_data_for_log = {
                "model_name": self.genai_model.model_name,
                "generation_config": self.generation_config_dict,
                "safety_settings": self.safety_settings_dict,
                "request_options": request_options,
                "stream": True
            }
            self.log_request_details(request_data_for_log, headers={"Authorization": f"Bearer {self._mask_api_key(self.api_key)}"}, prompt=full_prompt)

            await self._ensure_rate_controller()
            if self.rate_controller:
                await self.rate_controller.acquire()
            
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            response_stream = await self.genai_model.generate_content_async(
                full_prompt,
                stream=True,
                request_options=request_options
            )
            
            async for chunk in response_stream:
                yield chunk.text

        except Exception as e:
            self.logger.error(f"[Gemini] 流式API调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data_for_log, full_prompt)
            if "rate limit" in str(e).lower():
                raise LLMServiceRateLimitError(f"Gemini API 速率限制: {e}") from e
            elif isinstance(e, (google_exceptions.RetryError, google_exceptions.DeadlineExceeded)):
                raise LLMServiceTimeoutError(f"Gemini API 超时: {e}") from e
            else:
                raise LLMServiceAPIError(f"Gemini API 流式调用失败: {e}") from e

    def get_service_info(self) -> Dict[str, Any]:
        """获取当前服务的详细配置信息。"""
        info = super().get_service_info()
        info.update({
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "candidate_count": self.candidate_count,
            "stop_sequences": self.stop_sequences,
            "thinking_budget": self.thinking_budget,
            "safety_settings": self.safety_settings_dict,
        })
        return self._mask_sensitive_data(info)
