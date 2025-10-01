# src/llm_services/dashscope_adapter.py

import json
import logging
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
import asyncio

from .openai_service import OpenAIService
from .base_service import BaseLLMService
from .schemas import PoemData, EmotionSchema
from ..response_parsing.llm_response_parser import LLMResponseParser


class DashScopeAdapter(BaseLLMService):
    """
    阿里云百炼平台(DashScope) API服务适配器
    
    该适配器基于 OpenAIService 实现，负责处理 DashScope 特有的配置和参数，
    并将通用的 API 调用委托给 OpenAIService。
    """

    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser: Optional[LLMResponseParser] = None):
        """
        初始化并解析配置字典
        """
        # 调用基类构造函数，传递完整的config字典、模型配置名称和可选的response_parser实例
        super().__init__(config, model_config_name, response_parser)
        
        # 配置解析和验证逻辑
        self._parse_and_validate_config()
        
        # 初始化内部的 OpenAIService 实例
        # 我们需要传递一个修改过的配置，移除 DashScope 特有的参数
        openai_compatible_config = self._create_openai_compatible_config(config)
        self._openai_service = OpenAIService(openai_compatible_config, model_config_name)
        
        self._log_initialization()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 释放内部OpenAI服务的资源
        if hasattr(self, '_openai_service') and self._openai_service:
            await self._openai_service.__aexit__(exc_type, exc_val, exc_tb)
        # 调用父类的__aexit__
        await super().__aexit__(exc_type, exc_val, exc_tb)

    def _parse_and_validate_config(self):
        """集中处理 DashScope 特有配置的解析、类型转换和验证"""
        # DashScope特定参数
        self.enable_search = str(self.config.get('enable_search', 'false')).lower() == 'true'
        self.result_format = self.config.get('result_format', 'message')
        self.incremental_output = str(self.config.get('incremental_output', 'false')).lower() == 'true'
        self.enable_thinking = str(self.config.get('enable_thinking', 'false')).lower() == 'true'

        # 验证 result_format
        if self.result_format not in ['message', 'text']:
            raise ValueError(f"result_format 必须是 'message' 或 'text'，当前值: {self.result_format}")
            
        # 验证 enable_search 与模型的兼容性（如果需要）
        # 这里可以添加更复杂的验证逻辑

    def _create_openai_compatible_config(self, original_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        从原始配置中创建一个 OpenAI 兼容的配置字典
        移除 DashScope 特有的参数
        """
        openai_config = original_config.copy()
        
        # 移除 DashScope 特有的参数
        dashscope_specific_keys = [
            'enable_search', 'result_format', 'incremental_output', 'enable_thinking'
        ]
        for key in dashscope_specific_keys:
            openai_config.pop(key, None)
            
        return openai_config

    def _log_initialization(self):
        """记录简洁的初始化信息"""
        self.logger.info(f"[{self.provider.capitalize()}] 服务初始化完成 - 模型: {self.model}")
        params_summary = (
            f"enable_search: {self.enable_search}, result_format: {self.result_format}, "
            f"incremental_output: {self.incremental_output}, enable_thinking: {self.enable_thinking}"
        )
        # 复用 OpenAIService 的日志信息
        openai_info = self._openai_service.get_service_info()
        openai_params = (
            f"温度: {openai_info.get('temperature', 'N/A')}, "
            f"最大token: {openai_info.get('max_tokens', 'N/A')}, "
            f"超时: {openai_info.get('timeout', 'N/A')}s, "
            f"top_p: {openai_info.get('top_p', 'N/A')}, "
            f"presence_penalty: {openai_info.get('presence_penalty', 'N/A')}, "
            f"frequency_penalty: {openai_info.get('frequency_penalty', 'N/A')}, "
            f"n: {openai_info.get('n', 'N/A')}, "
            f"停止序列: {openai_info.get('stop', 'N/A')}, "
            f"响应格式: {openai_info.get('response_format', 'N/A')}"
        )
        self.logger.debug(f"[{self.provider.capitalize()}] 详细初始化参数: {params_summary}")
        self.logger.debug(f"[{self.provider.capitalize()}] OpenAI兼容参数: {openai_params}")

    async def health_check(self) -> Tuple[bool, str]:
        """
        委托给 OpenAIService 执行健康检查
        """
        self.logger.info(f"对模型 '{self.model}' 执行健康检查...")
        return await self._openai_service.health_check()

    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        实现基类的抽象方法，使用 OpenAIService 进行 API 调用，
        但在请求中添加 DashScope 特有的参数。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成"
        try:
            # 步骤 1: 使用基类方法准备提示词
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt
            
            # 步骤 2: 构建请求参数
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self._openai_service.max_tokens,
                "temperature": self._openai_service.temperature,
                "top_p": self._openai_service.top_p,
                "n": self._openai_service.n,
                "presence_penalty": self._openai_service.presence_penalty,
                "frequency_penalty": self._openai_service.frequency_penalty
            }
            
            if self._openai_service.stop: request_data["stop"] = self._openai_service.stop
            if self._openai_service.logit_bias: request_data["logit_bias"] = self._openai_service.logit_bias
            if self._openai_service.response_format: request_data["response_format"] = self._openai_service.response_format
            # 确保流式响应为 False
            request_data["stream"] = False
            
            # 添加 DashScope 特定的额外参数
            extra_body_params = {}
            if self.enable_search: 
                extra_body_params["enable_search"] = self.enable_search
            if self.result_format: 
                extra_body_params["result_format"] = self.result_format
            if self.incremental_output: 
                extra_body_params["incremental_output"] = self.incremental_output
            if self.enable_thinking: 
                extra_body_params["enable_thinking"] = self.enable_thinking
            
            if extra_body_params:
                request_data["extra_body"] = extra_body_params

            # 步骤 3: 记录和发送请求
            self.log_request_details(
                request_body=request_data,
                headers={"Authorization": f"Bearer {self._mask_api_key(self.api_key)}"},
                prompt=system_prompt
            )
            
            # --- 应用速率控制器 ---
            await self._ensure_rate_controller()  # 确保控制器已初始化
            if self.rate_controller:
                await self.rate_controller.acquire()
                self.logger.debug(f"[{self.provider.capitalize()}] 速率控制器：已获取执行权限，继续执行API请求。")
            
            # --- 应用请求间延迟 ---
            if self.request_delay > 0:
                self.logger.debug(f"[{self.provider.capitalize()}] 应用请求间延迟: {self.request_delay} 秒")
                await asyncio.sleep(self.request_delay)
            
            response = await self._openai_service.client.chat.completions.create(**request_data)
            
            # 步骤 4: 解析响应
            response_data = response.model_dump()
            
            self._openai_service._validate_openai_response(response_data)
            
            response_text = self._openai_service._extract_response_content(response_data)
            usage = response_data.get('usage', {})
            
            result = self._openai_service.validate_response(response_text)
            
            # 记录响应详情
            self.log_response_details(
                poem_id=poem.id,
                parsed_data=result,
                response_data=response_data,
                response_text=response_text,
                usage=usage
            )
            
            return result

        except Exception as e:
            self.logger.error(f"[{self.provider.capitalize()}] API调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            # 根据异常类型转换为更具体的内部异常
            if "rate_limit" in str(e).lower() or "429" in str(e):
                from .exceptions import LLMServiceRateLimitError
                raise LLMServiceRateLimitError(f"DashScope API 速率限制: {e}") from e
            elif "timeout" in str(e).lower() or "ConnectTimeout" in str(e):
                from .exceptions import LLMServiceTimeoutError
                raise LLMServiceTimeoutError(f"DashScope API 超时: {e}") from e
            else:
                from .exceptions import LLMServiceAPIError
                raise LLMServiceAPIError(f"DashScope API 调用失败: {e}") from e

    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> AsyncGenerator[str, None]:
        """
        实现基类的抽象方法，支持流式输出。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成"
        try:
            # 步骤 1: 使用基类方法准备提示词
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt

            # 步骤 2: 构建请求参数
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self._openai_service.max_tokens,
                "temperature": self._openai_service.temperature,
                "top_p": self._openai_service.top_p,
                "n": self._openai_service.n,
                "presence_penalty": self._openai_service.presence_penalty,
                "frequency_penalty": self._openai_service.frequency_penalty,
                "stream": True  # 启用流式输出
            }

            if self._openai_service.stop: request_data["stop"] = self._openai_service.stop
            if self._openai_service.logit_bias: request_data["logit_bias"] = self._openai_service.logit_bias
            if self._openai_service.response_format: request_data["response_format"] = self._openai_service.response_format

            # 添加 DashScope 特定的额外参数
            extra_body_params = {}
            if self.enable_search: 
                extra_body_params["enable_search"] = self.enable_search
            if self.result_format: 
                extra_body_params["result_format"] = self.result_format
            if self.incremental_output: 
                extra_body_params["incremental_output"] = self.incremental_output
            if self.enable_thinking: 
                extra_body_params["enable_thinking"] = self.enable_thinking

            if extra_body_params:
                request_data["extra_body"] = extra_body_params

            # 步骤 3: 记录和发送请求
            self.log_request_details(
                request_body=request_data,
                headers={"Authorization": f"Bearer {self._mask_api_key(self.api_key)}"},
                prompt=system_prompt
            )

            # --- 应用速率控制器 ---
            await self._ensure_rate_controller()  # 确保控制器已初始化
            if self.rate_controller:
                await self.rate_controller.acquire()
                self.logger.debug(f"[{self.provider.capitalize()}] 速率控制器：已获取执行权限，继续执行API请求。")

            # --- 应用请求间延迟 ---
            if self.request_delay > 0:
                self.logger.debug(f"[{self.provider.capitalize()}] 应用请求间延迟: {self.request_delay} 秒")
                await asyncio.sleep(self.request_delay)

            # 发送流式请求
            stream = await self._openai_service.client.chat.completions.create(**request_data)

            # 步骤 4: 逐块 yield 响应内容
            async for chunk in stream:
                # 解析DashScope特定格式并提取内容
                chunk_dict = chunk.model_dump()
                choices = chunk_dict.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        yield content 

        except Exception as e:
            self.logger.error(f"[{self.provider.capitalize()}] 流式 API 调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            # 根据异常类型转换为更具体的内部异常
            if "rate_limit" in str(e).lower() or "429" in str(e):
                from .exceptions import LLMServiceRateLimitError
                raise LLMServiceRateLimitError(f"DashScope API 速率限制: {e}") from e
            elif "timeout" in str(e).lower() or "ConnectTimeout" in str(e):
                from .exceptions import LLMServiceTimeoutError
                raise LLMServiceTimeoutError(f"DashScope API 超时: {e}") from e
            else:
                from .exceptions import LLMServiceAPIError
                raise LLMServiceAPIError(f"DashScope API 调用失败: {e}") from e

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        info = self._openai_service.get_service_info()
        info["provider"] = self.provider
        info["enable_search"] = self.enable_search
        info["result_format"] = self.result_format
        info["incremental_output"] = self.incremental_output
        info["enable_thinking"] = self.enable_thinking
        return self._mask_sensitive_data(info)
