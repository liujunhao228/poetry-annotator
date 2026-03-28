"""
SiliconFlow API 服务实现
"""

import asyncio
import json
import re
from typing import Dict, Any, Optional, List, Tuple
import httpx

from .base_service import BaseLLMService


class SiliconFlowService(BaseLLMService):
    """SiliconFlow API 服务实现"""

    def __init__(self, config: Dict[str, Any], model_config_name: str):
        super().__init__(config, model_config_name)
        self._parse_and_validate_config()
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        self._log_initialization()

    def _parse_and_validate_config(self):
        self.temperature = float(self.config.get('temperature', 0.3))
        self.max_tokens = int(self.config.get('max_tokens', 1000))
        self.timeout = int(self.config.get('timeout', 30))
        self.top_p = float(self.config.get('top_p', 1.0))
        self.n = int(self.config.get('n', 1))

        if not (0 <= self.temperature <= 2):
            raise ValueError("temperature 必须在 0-2 之间")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0")
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        if not (0 <= self.top_p <= 1):
            raise ValueError("top_p 必须在 0-1 之间")
        if self.n <= 0:
            raise ValueError("n 必须大于 0")

        self.top_k = int(self.config['top_k']) if self.config.get('top_k') else None
        self.seed = int(self.config['seed']) if self.config.get('seed') else None

        if self.top_k is not None and self.top_k <= 0:
            raise ValueError("top_k 必须大于 0")
        if self.seed is not None and self.seed < 0:
            raise ValueError("seed 必须大于等于 0")

        stop_raw = self.config.get('stop')
        self.stop = [s.strip() for s in stop_raw.split(',') if s.strip()] if stop_raw else None

        response_format_raw = self.config.get('response_format')
        if response_format_raw:
            try:
                self.response_format = json.loads(response_format_raw)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析 response_format 配置：'{response_format_raw}'")
                self.response_format = None
        else:
            self.response_format = None

        self.stream = self.config.get('stream', 'false').lower() == 'true'
        self.response_adapter = self.config.get('response_adapter')

    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def build_request_body(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        request_body = {
            "model": self.model,
            "messages": self._build_messages(system_prompt, user_prompt),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n
        }
        if self.top_k is not None:
            request_body["top_k"] = self.top_k
        if self.stop is not None:
            request_body["stop"] = self.stop
        if self.seed is not None:
            request_body["seed"] = self.seed
        if self.response_format is not None:
            request_body["response_format"] = self.response_format
        if self.stream:
            request_body["stream"] = self.stream
        return request_body

    def _log_initialization(self):
        self.logger.info(f"[{self.provider.capitalize()}] 服务初始化完成 - 模型：{self.model}")

    def _adapt_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """响应格式适配器"""
        if self.response_adapter == 'ollama':
            try:
                message = response_data.get('choices', [{}])[0].get('message')
                if not message or not isinstance(message, dict):
                    return response_data
                content = message.get('content', '')
                match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if match:
                    message['reasoning_content'] = match.group(1).strip()
            except (KeyError, IndexError, AttributeError) as e:
                self.logger.warning(f"Ollama 响应格式转换失败：{e}")
        return response_data

    async def health_check(self) -> Tuple[bool, str]:
        try:
            request_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Health check"}],
                "max_tokens": 1
            }
            timeout = httpx.Timeout(10.0)
            response = await self.client.post(f"{self.base_url}", json=request_data, timeout=timeout)
            response.raise_for_status()
            response.json()
            return True, "API connection and key are valid."
        except httpx.HTTPStatusError as e:
            return False, f"HTTP {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    async def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        request_data = None
        try:
            request_data = self.build_request_body(system_prompt, user_prompt)

            await self._ensure_rate_limiter()
            if self.rate_limiter:
                await self.rate_limiter.acquire()

            response = await self.client.post(f"{self.base_url}", json=request_data)
            response.raise_for_status()

            response_data = response.json()
            adapted_response_data = self._adapt_response(response_data)
            self._validate_siliconflow_response(adapted_response_data)

            return self._extract_response_content(adapted_response_data)

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            self.log_error_details(e, request_data, user_prompt)
            if status_code in [429, 500, 502, 503, 504]:
                raise
            else:
                raise ValueError(f"API HTTP Error (status: {status_code}): {e.response.text}") from e
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            self.log_error_details(e, request_data, user_prompt)
            raise
        except Exception as e:
            self.log_error_details(e, request_data, user_prompt)
            raise ValueError(f"An unexpected error occurred: {e}") from e

    def _validate_siliconflow_response(self, response_data: Dict[str, Any]):
        """验证响应结构"""
        if not isinstance(response_data, dict):
            raise ValueError("响应数据必须是字典格式")
        required_fields = ['id', 'object', 'created', 'model', 'choices']
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"响应缺少必需字段：{field}")
        choices = response_data.get('choices', [])
        if not isinstance(choices, list) or not choices:
            raise ValueError("choices 字段必须是非空数组")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError("choice 必须是字典格式")
        if 'message' not in choice:
            raise ValueError("choice 缺少 message 字段")
        message = choice['message']
        if not isinstance(message, dict):
            raise ValueError("message 必须是字典格式")
        if 'role' not in message or 'content' not in message:
            raise ValueError("message 缺少必需字段")
        if message['role'] != 'assistant':
            raise ValueError(f"message.role 必须是'assistant'，当前为：{message['role']}")

    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """从响应数据中提取主要内容"""
        choices = response_data.get('choices', [])
        if not choices:
            raise ValueError("响应中没有找到 choices")
        choice = choices[0]
        message = choice.get('message', {})
        content = message.get('content', '')
        return content

    def get_service_info(self) -> Dict[str, Any]:
        info = {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "stop": self.stop,
            "seed": self.seed,
            "response_format": self.response_format,
            "stream": self.stream,
            "n": self.n
        }
        if self.response_format:
            info["response_format_info"] = {
                "type": self.response_format.get("type"),
                "description": "JSON 对象格式" if self.response_format.get("type") == "json_object" else "文本格式"
            }
        return self._mask_sensitive_data(info)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
