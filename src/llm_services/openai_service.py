# src/llm_services/openai_service.py

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple, AsyncGenerator
import httpx
from openai import AsyncOpenAI
from .base_service import BaseLLMService
from .schemas import PoemData, EmotionSchema
from .exceptions import LLMServiceAPIError, LLMServiceRateLimitError, LLMServiceTimeoutError
from ..response_parsing.llm_response_parser import LLMResponseParser


class OpenAIService(BaseLLMService):
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'client') and self.client:
            # OpenAI的AsyncClient需要调用close方法
            await self.client.close()
        # 调用父类的__aexit__
        await super().__aexit__(exc_type, exc_val, exc_tb)
    """
    OpenAI API服务实现
    
    此类负责解析和验证其自身的配置，并实现 BaseLLMService 定义的统一接口。
    """

    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser: Optional[LLMResponseParser] = None):
        """
        初始化并解析配置字典
        """
        # 调用基类构造函数，传递完整的config字典、模型配置名称和可选的response_parser实例
        super().__init__(config, model_config_name, response_parser)
        
        # 配置解析和验证逻辑
        self._parse_and_validate_config()
        
        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=0  # 禁用sdk内置重试，由外部统一处理
        )
        
        self._log_initialization()

    def _parse_and_validate_config(self):
        """集中处理配置的解析、类型转换和验证"""
        # 基础参数
        self.temperature = float(self.config.get('temperature', 0.3))
        self.max_tokens = int(self.config.get('max_tokens', 1000))
        self.timeout = int(self.config.get('timeout', 30))
        self.top_p = float(self.config.get('top_p', 1.0))
        self.n = int(self.config.get('n', 1))

        if not (0 <= self.temperature <= 2): raise ValueError("temperature必须在0-2之间")
        if self.max_tokens <= 0: raise ValueError("max_tokens必须大于0")
        if self.timeout <= 0: raise ValueError("timeout必须大于0")
        if not (0 <= self.top_p <= 1): raise ValueError("top_p必须在0-1之间")
        if self.n <= 0: raise ValueError("n必须大于0")

        # 高级参数
        self.presence_penalty = float(self.config.get('presence_penalty', 0.0))
        self.frequency_penalty = float(self.config.get('frequency_penalty', 0.0))
        self.logit_bias = self.config.get('logit_bias')
        if self.logit_bias:
            try:
                self.logit_bias = json.loads(self.logit_bias)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析logit_bias配置为JSON: '{self.logit_bias}'。将忽略此配置。")
                self.logit_bias = None

        # 停止序列
        stop_raw = self.config.get('stop')
        self.stop = [s.strip() for s in stop_raw.split(',') if s.strip()] if stop_raw else None

        # 响应格式
        response_format_raw = self.config.get('response_format')
        if response_format_raw:
            try:
                self.response_format = json.loads(response_format_raw)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析response_format配置为JSON: '{response_format_raw}'。将忽略此配置。")
                self.response_format = None
        else:
            self.response_format = None
            
        if self.response_format:
             if not isinstance(self.response_format, dict) or 'type' not in self.response_format or self.response_format['type'] not in ['json_object', 'text']:
                raise ValueError("response_format 格式不正确，必须是包含'type'键的字典，且'type'为'json_object'或'text'。")

        # 特殊参数
        self.stream = self.config.get('stream', 'false').lower() == 'true'

    def _log_initialization(self):
        """记录简洁的初始化信息"""
        self.logger.info(f"[{self.provider.capitalize()}] 服务初始化完成 - 模型: {self.model}")
        params_summary = (
            f"温度: {self.temperature}, 最大token: {self.max_tokens}, 超时: {self.timeout}s, "
            f"top_p: {self.top_p}, presence_penalty: {self.presence_penalty}, "
            f"frequency_penalty: {self.frequency_penalty}, n: {self.n}, stream: {self.stream}, "
            f"停止序列: {self.stop}, 响应格式: {self.response_format}"
        )
        self.logger.debug(f"[{self.provider.capitalize()}] 详细初始化参数: {params_summary}")

    async def health_check(self) -> Tuple[bool, str]:
        self.logger.info(f"对模型 '{self.model}' 执行健康检查...")
        try:
            # 构建一个非常轻量级的请求
            response = await self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=1
            )
            
            if response.status_code == 200:
                self.logger.info("健康检查成功: API连接和密钥有效。")
                return True, "API connection and key are valid."
            else:
                error_message = f"健康检查失败: HTTP {response.status_code}."
                self.logger.error(error_message)
                return False, error_message
                
        except Exception as e:
            error_message = f"健康检查失败: 发生未知错误 - {type(e).__name__}: {e}"
            self.logger.error(error_message, exc_info=True)
            return False, error_message

    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        实现基类的抽象方法，使用OpenAI SDK进行API调用。
        
        Args:
            poem: 诗词数据 DTO。
            emotion_schema: 情感体系 DTO。
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
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": self.n,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty
            }
            
            if self.stop: request_data["stop"] = self.stop
            if self.logit_bias: request_data["logit_bias"] = self.logit_bias
            if self.response_format: request_data["response_format"] = self.response_format
            # 确保流式响应为 False
            request_data["stream"] = False

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
            
            response = await self.client.chat.completions.create(**request_data)
            
            # 步骤 4: 解析响应
            response_data = response.model_dump()
            
            self._validate_openai_response(response_data)
            
            response_text = self._extract_response_content(response_data)
            usage = response_data.get('usage', {})
            
            result = self.validate_response(response_text)
            
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
                raise LLMServiceRateLimitError(f"OpenAI API 速率限制: {e}") from e
            elif "timeout" in str(e).lower() or "ConnectTimeout" in str(e):
                raise LLMServiceTimeoutError(f"OpenAI API 超时: {e}") from e
            else:
                raise LLMServiceAPIError(f"OpenAI API 调用失败: {e}") from e

    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> AsyncGenerator[str, None]:
        """
        [新增] 实现流式响应方法。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成"
        try:
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt

            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": self.n,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "stream": True  # 关键: 启用流式响应
            }
            if self.stop: request_data["stop"] = self.stop
            if self.logit_bias: request_data["logit_bias"] = self.logit_bias
            if self.response_format: request_data["response_format"] = self.response_format

            self.log_request_details(
                request_body=request_data,
                headers={"Authorization": f"Bearer {self._mask_api_key(self.api_key)}"},
                prompt=system_prompt
            )

            await self._ensure_rate_controller()
            if self.rate_controller:
                await self.rate_controller.acquire()
            
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            stream = await self.client.chat.completions.create(**request_data)
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        
        except Exception as e:
            self.logger.error(f"[{self.provider.capitalize()}] 流式API调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise LLMServiceRateLimitError(f"OpenAI API 速率限制: {e}") from e
            elif "timeout" in str(e).lower() or "ConnectTimeout" in str(e):
                raise LLMServiceTimeoutError(f"OpenAI API 超时: {e}") from e
            else:
                raise LLMServiceAPIError(f"OpenAI API 流式调用失败: {e}") from e

    def _validate_openai_response(self, response_data: Dict[str, Any]):
        """验证 OpenAI API响应结构"""
        if not isinstance(response_data, dict):
            raise ValueError("响应数据必须是字典格式")
        
        required_fields = ['id', 'object', 'created', 'model', 'choices']
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"响应缺少必需字段: {field}")
        
        choices = response_data.get('choices', [])
        if not isinstance(choices, list) or not choices:
            raise ValueError("choices字段必须是非空数组")
        
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError("choice必须是字典格式")
        
        if 'message' not in choice:
            raise ValueError("choice缺少message字段")
        
        message = choice['message']
        if not isinstance(message, dict):
            raise ValueError("message必须是字典格式")
        
        if 'role' not in message or 'content' not in message:
            raise ValueError("message缺少必需字段: role, content")
        
        if message['role'] != 'assistant':
            raise ValueError(f"message.role必须是'assistant'，当前为: {message['role']}")

    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """从响应数据中提取主要内容"""
        choices = response_data.get('choices', [])
        if not choices:
            raise ValueError("响应中没有找到choices")
        
        choice = choices[0]
        message = choice.get('message', {})
        content = message.get('content', '')
        
        if not content:
            self.logger.warning(f"[{self.provider.capitalize()}] 响应内容为空")
        
        return content

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        info = {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "response_format": self.response_format,
            "stream": self.stream,
            "n": self.n
        }
        
        if self.response_format:
            info["response_format_info"] = {
                "type": self.response_format.get("type"),
                "description": "JSON对象格式" if self.response_format.get("type") == "json_object" else "文本格式"
            }
        
        return info
