from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import json
import logging
import os
from pathlib import Path
import sys
import os

# Ensure the project root is in sys.path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    # print(f"Added {project_root} to sys.path for absolute imports.") # Commented out to reduce log noise

try:
    from src.llm_response_parser import llm_response_parser
    from src.config_manager import ConfigManager
    from src.utils.rate_limiter import AsyncTokenBucket
except ImportError as e:
    print(f"Failed to import core modules absolutely: {e}")
    raise # Re-raise the exception to stop execution


class BaseLLMService(ABC):
    """LLM服务抽象基类 (已重构)"""
    def __init__(self, config: Dict[str, Any], model_config_name: str):
        """
        构造函数现在接收完整的配置字典
        """
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
            raise ValueError(f"模型配置 '{model_config_name}' 的API密钥未正确配置。 ")

        # --- 延迟初始化速率限制器 ---
        self.rate_limiter: Optional[AsyncTokenBucket] = None
        self._rate_limit_qps: Optional[float] = None
        self._rate_limit_burst: Optional[int] = None
        rate_limit_qps_str = self.config.get('rate_limit_qps')
        if rate_limit_qps_str:
            try:
                qps = float(rate_limit_qps_str)
                burst_str = self.config.get('rate_limit_burst', str(qps * 2))
                burst = int(float(burst_str))
                # 仅保存参数，不创建实例
                self._rate_limit_qps = qps
                self._rate_limit_burst = burst
                self.logger.info(
                    f"为模型 '{self.model_config_name}' 配置速率限制: "
                    f"QPS={qps}, 突发容量={burst} (将在首次异步调用时初始化)"
                )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"无法为模型 '{self.model_config_name}' 解析速率限制配置，将不启用。错误: {e}"
                )

        # Prompt templates are no longer loaded in the base service.
        # This is now handled by the project-specific PromptBuilder.

    # --- 按需创建速率限制器的辅助方法 ---
    async def _ensure_rate_limiter(self):
        """在首次使用时，于异步上下文中初始化速率限制器。"""
        # 只有在配置了QPS且实例尚未创建时才执行
        if self._rate_limit_qps is not None and self.rate_limiter is None:
            self.logger.debug("首次异步调用，正在初始化 AsyncTokenBucket...")
            self.rate_limiter = AsyncTokenBucket(self._rate_limit_qps, self._rate_limit_burst)
            self.logger.info("AsyncTokenBucket 速率限制器已成功初始化。")

    def _mask_api_key(self, text: str) -> str:
        """对API密钥进行掩码处理"""
        if not text or not isinstance(text, str):
            return text
            
        # 如果是Bearer token格式
        if text.startswith('Bearer '):
            key = text[7:]  # 获取Bearer后面的部分
            if len(key) > 8:
                return f"Bearer {key[:4]}...{key[-4:]}"
            return "Bearer ****"
            
        # 普通API密钥
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
            elif isinstance(value, str) and 'api' in key.lower() and 'key' in key.lower():
                masked_data[key] = self._mask_api_key(value)
        return masked_data


    @abstractmethod
    async def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Gets a completion from the LLM service using pre-built prompts.

        Args:
            system_prompt: The system prompt.
            user_prompt: The user prompt.

        Returns:
            The raw string response from the LLM.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """
        [新] 执行对LLM服务的健康检查。

        用于验证API密钥、网络连接和基础配置是否有效。
        子类应实现一个轻量级的API调用（例如，获取模型列表或一个非常短的完成）。

        Returns:
            一个元组 (is_healthy: bool, message: str)。
            is_healthy 为 True 表示健康，False 表示不健康。
            message 提供了检查结果的详细信息。
        """
        pass

    def log_request_details(self, request_body: Dict[str, Any], headers: Dict[str, Any], prompt: Optional[str] = None):
        """记录完整的请求详情，长文本使用DEBUG级别"""
        # 注释掉记录发送的请求信息（请求体与请求头）的逻辑
        # masked_body = self._mask_sensitive_data(request_body)
        # masked_headers = self._mask_sensitive_data(headers)
        
        # 所有详细、冗长的日志都使用 DEBUG 级别
        # self.logger.debug("=" * 80)
        # self.logger.debug(f"[{self.provider.upper()}] 请求详情")
        # self.logger.debug(f"请求体 (Payload):\n{json.dumps(masked_body, ensure_ascii=False, indent=2)}")
        # self.logger.debug(f"请求头 (Headers):\n{json.dumps(masked_headers, ensure_ascii=False, indent=2)}")
        # if prompt:
        #     # 提示词长度对于用户意义不大，属于调试信息
        #     self.logger.debug(f"[{self.provider.upper()}] 系统提示词长度: {len(prompt)}")
        # self.logger.debug("=" * 80)

        # [新增] 添加一条简洁的 INFO 日志，让用户知道程序在做什么
        self.logger.info(f"向 [{self.provider.upper()}] 发送API请求...")

    def log_response_details(self, parsed_data: Any, usage: Optional[Dict[str, Any]] = None):
        """记录响应详情，长文本使用DEBUG级别"""
        # 注释掉记录"完整响应详情"的逻辑
        # self.logger.debug("=" * 80)
        # self.logger.debug(f"[{self.provider.upper()}] 完整响应详情:")
        # self.logger.debug(f"响应状态: 成功")
        # if usage:
        #     self.logger.debug(f"Token使用情况: {usage}")
        
        # 将详细的解析结果改为 DEBUG
        # self.logger.debug(f"[{self.provider.upper()}] 解析结果:\n{json.dumps(parsed_data, ensure_ascii=False, indent=2)}")
        # self.logger.debug("=" * 80)

        # [新增] 在此添加一条简洁的 INFO 日志
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
            # [保持DEBUG] 这里的日志原本就是DEBUG，非常合理
            self.logger.debug("=" * 80)
            self.logger.debug(f"[{self.provider.upper()}] 错误详情:")
            self.logger.debug(f"错误信息:\n{json.dumps(error_info, ensure_ascii=False, indent=2)}")
            if prompt:
                self.logger.debug(f"用户提示词: {prompt}")
            self.logger.debug("=" * 80)
        except Exception as e:
            self.logger.warning(f"记录错误详情时发生错误: {e}")

    def validate_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        [已重构] 使用集成了验证逻辑的解析器，对LLM响应进行原子化的解析与验证。
        此方法现在完全委托 `llm_response_parser` 来完成所有工作。
        解析器会尝试多种策略从文本中提取一个JSON数组，并立即验证其内容
        是否符合业务规范（包含'id', 'primary', 'secondary'等字段和正确类型）。
        只有完全通过验证的结果才会被返回。
        Args:
            response_text: LLM的原始响应文本。
        Returns:
            一个经过完全验证的、包含标注信息的字典列表。
        Raises:
            ValueError: 如果响应无法被解析，或者解析后的所有内容都不符合业务规范。
        """
        try:
            self.logger.debug("开始使用LLMResponseParser统一解析并验证响应...")
            # 只需要调用一次 parse，它会处理所有解析和验证的复杂逻辑
            validated_list = llm_response_parser.parse(response_text)
            
            # 将原有的 INFO 日志细化
            self.logger.info(f"响应解析及内容验证成功，共 {len(validated_list)} 条标注记录。") # 保留这条简洁的INFO
            # 注释掉记录"详细验证内容"的逻辑
            # self.logger.debug(f"详细验证内容: {json.dumps(validated_list, ensure_ascii=False, indent=2)}") # 增加一条DEBUG用于追溯
            
            return validated_list
        except (ValueError, TypeError) as e:
            # 捕获解析器抛出的最终错误
            self.logger.error(f"响应统一解析验证失败: {e}", exc_info=True)
            # 将原始响应内容记录在 DEBUG 级别，避免在控制台输出大段错误文本
            self.logger.debug(f"导致失败的原始响应内容: {response_text}")
            raise # 将异常向上抛出，由调用方(例如 Annotator)捕获并处理

    # [已移除] _validate_annotation_list_content 方法已被移除，
    # 其功能已完全整合进 llm_response_parser.py 中，实现了解析与验证的统一。

    def format_error_response(self, error: str) -> Dict[str, Any]:
        """
        格式化标准化的错误响应。
        Args:
            error: 错误信息。
        Returns:
            一个包含错误信息的字典。
        """
        return {
            "error": str(error)
        }

    def log_annotation(self, poem_id: int, success: bool,
                      result: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None):
        """记录标注日志"""
        if success:
            primary_emotion = result.get('primary_emotion', '未知') if result is not None else '未知'
            # [保持INFO] 这条日志简洁、对用户有意义，保留
            self.logger.info(f"诗词 {poem_id} 标注成功: {primary_emotion}")
        else:
            # [保持ERROR] 这是明确的错误信息，保留
            self.logger.error(f"诗词 {poem_id} 标注失败: {error}")

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        service_info = {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key  # 原始API密钥会被_mask_sensitive_data处理
        }
        return self._mask_sensitive_data(service_info)
