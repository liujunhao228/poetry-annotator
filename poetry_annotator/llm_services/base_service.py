"""
LLM 服务抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import json
import logging

from ..utils.rate_limiter import AsyncTokenBucket


class BaseLLMService(ABC):
    """LLM 服务抽象基类"""

    def __init__(self, config: Dict[str, Any], model_config_name: str):
        self.config = config
        self.model_config_name = model_config_name
        self.logger = logging.getLogger(self.__class__.__name__)
        self.provider = self.config.get('provider', 'unknown')
        self.model = self.config.get('model_name')
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url')

        if not self.model or not self.api_key:
            raise ValueError(f"模型配置 '{model_config_name}' 必须包含 'model_name' 和 'api_key' 字段。")
        if self.api_key in ['your_gemini_api_key_here', 'your_siliconflow_api_key_here', '']:
            raise ValueError(f"模型配置 '{model_config_name}' 的 API 密钥未正确配置。")

        # 延迟初始化速率限制器
        self.rate_limiter: Optional[AsyncTokenBucket] = None
        self._rate_limit_qps: Optional[float] = None
        self._rate_limit_burst: Optional[int] = None

        rate_limit_qps_str = self.config.get('rate_limit_qps')
        if rate_limit_qps_str:
            try:
                qps = float(rate_limit_qps_str)
                burst_str = self.config.get('rate_limit_burst', str(qps * 2))
                burst = int(float(burst_str))
                self._rate_limit_qps = qps
                self._rate_limit_burst = burst
                self.logger.info(
                    f"为模型 '{self.model_config_name}' 配置速率限制：QPS={qps}, 突发容量={burst}"
                )
            except (ValueError, TypeError) as e:
                self.logger.warning(f"无法解析速率限制配置：{e}")

    async def _ensure_rate_limiter(self):
        """在首次使用时初始化速率限制器"""
        if self._rate_limit_qps is not None and self.rate_limiter is None:
            self.rate_limiter = AsyncTokenBucket(self._rate_limit_qps, self._rate_limit_burst)
            self.logger.info("AsyncTokenBucket 速率限制器已初始化。")

    def _mask_api_key(self, text: str) -> str:
        """对 API 密钥进行掩码处理"""
        if not text or not isinstance(text, str):
            return text
        if text.startswith('Bearer '):
            key = text[7:]
            if len(key) > 8:
                return f"Bearer {key[:4]}...{key[-4:]}"
            return "Bearer ****"
        if len(text) > 8:
            return f"{text[:4]}...{text[-4:]}"
        return "****"

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归处理字典中的敏感信息"""
        masked_data = data.copy()
        sensitive_keys = {'api_key', 'key', 'token', 'authorization', 'auth'}
        for key, value in masked_data.items():
            if isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, str) and key.lower() in sensitive_keys:
                masked_data[key] = self._mask_api_key(value)
        return masked_data

    @abstractmethod
    async def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """获取 LLM 完成响应"""
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """执行健康检查"""
        pass

    def log_request_details(self, request_body: Dict[str, Any], headers: Dict[str, Any], prompt: Optional[str] = None):
        """记录请求详情"""
        self.logger.info(f"向 [{self.provider.upper()}] 发送 API 请求...")

    def log_response_details(self, parsed_data: Any, usage: Optional[Dict[str, Any]] = None):
        """记录响应详情"""
        self.logger.info(f"成功接收并解析了来自 [{self.provider.upper()}] 的响应。")

    def log_error_details(self, error: Exception, request_data: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None):
        """记录错误详情"""
        try:
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'request_data': self._mask_sensitive_data(request_data) if request_data else None,
                'prompt_length': len(prompt) if prompt else None
            }
            self.logger.debug(f"[{self.provider.upper()}] 错误详情：{json.dumps(error_info, ensure_ascii=False)}")
        except Exception as e:
            self.logger.warning(f"记录错误详情时发生错误：{e}")

    def validate_response(self, response_text: str) -> List[Dict[str, Any]]:
        """验证并解析 LLM 响应"""
        from ..llm_response_parser import llm_response_parser
        try:
            self.logger.debug("开始解析并验证响应...")
            validated_list = llm_response_parser.parse(response_text)
            self.logger.info(f"响应解析成功，共 {len(validated_list)} 条标注记录。")
            return validated_list
        except (ValueError, TypeError) as e:
            self.logger.error(f"响应解析验证失败：{e}", exc_info=True)
            self.logger.debug(f"失败原始响应：{response_text[:500]}...")
            raise

    def format_error_response(self, error: str) -> Dict[str, Any]:
        """格式化错误响应"""
        return {"error": str(error)}

    def log_annotation(self, poem_id: int, success: bool,
                      result: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None):
        """记录标注日志"""
        if success:
            primary_emotion = result.get('primary_emotion', '未知') if result else '未知'
            self.logger.info(f"诗词 {poem_id} 标注成功：{primary_emotion}")
        else:
            self.logger.error(f"诗词 {poem_id} 标注失败：{error}")

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        service_info = {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key
        }
        return self._mask_sensitive_data(service_info)
