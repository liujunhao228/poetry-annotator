from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
import json
import logging
import os
from pathlib import Path
from src.llm_response_parser import llm_response_parser, ILLMResponseParser
from src.config.custom_json_validator import CustomJSONValidator, CustomValidationError # 新增导入
from src.config import config_manager
from src.utils.rate_limiter import AsyncTokenBucket
from src.utils.rate_controller import RateLimitConfig as InternalRateLimitConfig, create_rate_controller
from src.utils.rate_monitor import rate_monitor
from src.prompt_builder import prompt_builder
from .llm_response_logger import LLMResponseLogger
from .stream_reassembler import StreamReassembler
from .schemas import PoemData, EmotionSchema
from .exceptions import LLMServiceConfigError, LLMServiceResponseError


class BaseLLMService(ABC):
    """LLM服务抽象基类 (已重构)"""
    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser: Optional[ILLMResponseParser] = None):
        """
        构造函数现在接收完整的配置字典
        """
        self.config = config
        self.model_config_name = model_config_name
        self.logger = logging.getLogger(self.__class__.__name__)
        self.provider = self.config.get('provider', 'unknown')
        self.model = self.config.get('model_name')
        self.api_key = self.config.get('api_key')
        # --- 初始化响应解析器 ---
        # 如果传入了 response_parser 实例，则使用它；否则使用默认的全局实例
        # 这为未来通过工厂或配置注入不同的解析器提供了可能
        self.response_parser: ILLMResponseParser = response_parser or llm_response_parser
        self.base_url = self.config.get('base_url')
        if not self.model or not self.api_key:
            raise LLMServiceConfigError(f"模型配置 '{model_config_name}' 必须包含 'model_name' 和 'api_key' 字段。")
        if self.api_key in ['your_gemini_api_key_here', 'your_siliconflow_api_key_here', '']:
            raise LLMServiceConfigError(f"模型配置 '{model_config_name}' 的API密钥未正确配置。 ")

        # --- 延迟初始化速率控制器 ---
        self.rate_controller = None
        self.rate_limit_config = None
        
        # 解析速率限制配置
        rate_limit_qps_str = self.config.get('rate_limit_qps')
        rate_limit_rpm_str = self.config.get('rate_limit_rpm')
        max_concurrent_str = self.config.get('max_concurrent')
        rate_limit_burst_str = self.config.get('rate_limit_burst')
        request_delay_str = self.config.get('request_delay')
        
        # 构建速率限制配置
        if rate_limit_qps_str or rate_limit_rpm_str or max_concurrent_str:
            try:
                qps = float(rate_limit_qps_str) if rate_limit_qps_str else None
                rpm = float(rate_limit_rpm_str) if rate_limit_rpm_str else None
                max_concurrent = int(max_concurrent_str) if max_concurrent_str else None
                burst = int(float(rate_limit_burst_str)) if rate_limit_burst_str else None
                
                self.rate_limit_config = InternalRateLimitConfig(
                    qps=qps,
                    rpm=rpm,
                    max_concurrent=max_concurrent,
                    burst=burst
                )
                
                self.logger.info(
                    f"为模型 '{self.model_config_name}' 配置速率限制: "
                    f"QPS={qps}, RPM={rpm}, 最大并发={max_concurrent}, 突发容量={burst}"
                )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"无法为模型 '{self.model_config_name}' 解析速率限制配置，将不启用。错误: {e}"
                )

        # --- 请求间延迟 ---
        self.request_delay: float = 0.0
        if request_delay_str:
            try:
                delay = float(request_delay_str)
                if delay >= 0:
                    self.request_delay = delay
                    self.logger.info(
                        f"为模型 '{self.model_config_name}' 配置请求间延迟: {delay} 秒"
                    )
                else:
                    self.logger.warning(
                        f"请求间延迟配置值无效（必须>=0）: {delay}，将使用默认值 0 秒"
                    )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"无法为模型 '{self.model_config_name}' 解析请求间延迟配置，将不启用。错误: {e}"
                )

        # --- 初始化Prompt构建器 ---
        self.prompt_builder = prompt_builder
        
        # --- 初始化LLM响应日志记录器 ---
        self.llm_response_logger = LLMResponseLogger(self.model_config_name)
        
        # --- 初始化流式响应重组器 ---
        self.stream_reassembler = StreamReassembler(self.provider)
        
        # --- 初始化自定义校验器 ---
        config_root = Path(__file__).parent.parent / "config"
        self.custom_validator = CustomJSONValidator(config_root / "custom_validation_rules.yaml")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 基类不实现具体资源清理，由子类负责
        pass

    # --- 按需创建速率控制器的辅助方法 ---
    async def _ensure_rate_controller(self):
        """在首次使用时，于异步上下文中初始化速率控制器。"""
        # 只有在配置了速率限制且实例尚未创建时才执行
        if self.rate_limit_config is not None and self.rate_controller is None:
            self.logger.debug("首次异步调用，正在初始化速率控制器...")
            self.rate_controller = create_rate_controller(self.rate_limit_config)
            # 注册到监控器
            await rate_monitor.register_controller(self.model_config_name, self.rate_controller)
            self.logger.info("速率控制器已成功初始化。")

    # 移除_load_prompt_templates方法，因为现在使用插件化Prompt构建器

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

    def _load_template_file(self, template_path: str) -> str:
        """
        加载模板文件内容
        """
        raise NotImplementedError("模板文件加载功能已移除，现在使用插件化Prompt构建器")

    # 移除_build_system_prompt和_build_user_prompt方法，因为现在使用插件化Prompt构建器

    def _generate_sentences_with_id(self, paragraphs: List[str]) -> List[Dict[str, str]]:
        """
        为句子生成ID并构建JSON格式（从Annotator迁移而来）
        """
        return [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(paragraphs)]

    def prepare_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema) -> Tuple[str, str]:
        """
        集中化的提示词构建逻辑。
        这是服务类提供给外部的核心能力之一。
        [修改] 使用 poem_data.title, poem_data.paragraphs, emotion_schema.text
        """
        # 使用统一的Prompt构建器构建Prompt
        system_prompt, user_prompt = self.prompt_builder.build_prompts(
            poem_data, emotion_schema, self.model_config_name
        )
        
        return system_prompt, user_prompt

    @abstractmethod
    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        [修改] 抽象方法签名已更新，使用 DTO。
        现在接收 PoemData 和 EmotionSchema DTO，负责完整的标注流程。
        !! 重要 !!
        子类在实现此方法时，应在发起实际网络请求前，先调用 self._ensure_rate_limiter()，
        然后再检查并调用速率限制器：
        
        await self._ensure_rate_controller()  # 确保控制器已初始化
        if self.rate_controller:
            await self.rate_controller.acquire()
            # 如果使用了并发控制器，需要在完成后释放
            if hasattr(self.rate_controller, 'release'):
                # 在子类中需要调用 self.rate_controller.release() 来释放资源
                pass
        
        # ... 之后是 httpx.AsyncClient.post(...) 等网络请求代码 ...
        Args:
            poem: 包含诗词信息的 PoemData DTO。
            emotion_schema: 情感分类体系的 EmotionSchema DTO。
        Returns:
            一个经过验证的、包含标注信息的字典列表。
        """
        pass

    @abstractmethod
    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> AsyncGenerator[str, None]:
        """
        [新增] 抽象方法，用于支持流式响应。
        子类需要实现此方法以返回一个异步生成器，逐块产生响应内容。
        Args:
            poem: 包含诗词信息的 PoemData DTO。
            emotion_schema: 情感分类体系的 EmotionSchema DTO。
        Yields:
            响应内容的字符串块。
        """
        yield

    async def annotate_poem_stream_with_validation(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        流式标注诗词并返回验证后的完整结果
        
        Args:
            poem: 诗词数据
            emotion_schema: 情感分类体系
            
        Returns:
            验证后的标注结果列表
        """
        self.logger.info(f"[{self.provider}] 开始流式标注并验证诗词 {poem.id}")
        
        # 获取流式响应生成器
        stream_generator = self.annotate_poem_stream(poem, emotion_schema)
        
        # 重组完整响应
        complete_response = await self.stream_reassembler.parse_stream_chunks(stream_generator)
        
        # 验证完整响应
        validated_result = self.stream_reassembler.validate_complete_response(complete_response)
        
        self.logger.info(f"[{self.provider}] 完成流式标注和验证，获得 {len(validated_result)} 条结果")
        return validated_result

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

    def log_response_details(self, poem_id: str, parsed_data: Any, response_data: Dict[str, Any], response_text: str, usage: Optional[Dict[str, Any]] = None):
        """记录响应详情，长文本使用DEBUG级别，并可选地记录完整响应到独立日志"""
        # [保持] 简洁的 INFO 日志
        self.logger.info(f"成功接收并解析了来自 [{self.provider.upper()}] 的响应。")

        # [修改] 移除原来的 DEBUG 打印完整响应的逻辑

        # [新增] 如果配置要求保存完整响应，则使用专门的 logger 记录
        llm_config = config_manager.get_llm_config()
        save_full_response = llm_config.get('save_full_response', False)
        if save_full_response:
            self.llm_response_logger.log_response(
                poem_id=poem_id,
                response_data=response_data,  # 完整的响应数据字典
                response_text=response_text,  # 纯文本内容
                usage=usage                   # Token使用情况
            )
            self.logger.debug(f"[{self.provider.upper()}] 已将完整响应记录到独立日志文件。")

    def log_error_details(self, poem_id: str, error: Exception, request_data: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None):
        """记录错误详情，并可选地记录完整错误信息到独立日志"""
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

        # [新增] 如果配置要求保存完整响应（包括错误），则使用专门的 logger 记录错误
        llm_config = config_manager.get_llm_config()
        save_full_response = llm_config.get('save_full_response', False)
        if save_full_response:
            self.llm_response_logger.log_error(
                poem_id=poem_id,
                error=error,
                request_data=self._mask_sensitive_data(request_data) if request_data else None
            )
            self.logger.debug(f"[{self.provider.upper()}] 已将错误详情记录到独立日志文件。")

    def validate_response(self, response_text: str, save_full_response: bool = False) -> List[Dict[str, Any]]:
        """
        [已增强] 使用注入的解析器实例，对LLM响应进行原子化的解析与验证。
        此方法现在完全委托 `self.response_parser` 来完成所有工作。
        解析器会尝试多种策略从文本中提取一个JSON数组，并立即验证其内容
        是否符合业务规范（包含'id', 'primary', 'secondary'等字段和正确类型）。
        在基础验证通过后，再使用自定义校验器根据配置文件进行二次校验。
        只有完全通过所有验证的结果才会被返回。
        Args:
            response_text: LLM的原始响应文本。
            save_full_response: 是否保存完整响应内容。
        Returns:
            一个经过完全验证的、包含标注信息的字典列表。
        Raises:
            LLMServiceResponseError: 如果响应无法被解析，或者解析/校验后的所有内容都不符合规范。
        """
        try:
            self.logger.debug("开始使用注入的解析器统一解析并验证响应...")
            # 使用实例变量 self.response_parser 而不是全局变量
            validated_list = self.response_parser.parse(response_text)
            
            # [新增] 在基础验证通过后，进行自定义规则的二次校验
            try:
                # 使用自定义校验器进行二次校验
                custom_validated_list = self.custom_validator.validate(validated_list)
                self.logger.info(f"响应解析、内容验证及自定义规则校验均成功，共 {len(custom_validated_list)} 条标注记录。规则集: '{self.custom_validator.active_ruleset_name}'")
            except CustomValidationError as custom_e:
                self.logger.error(f"响应通过基础解析验证，但自定义规则校验失败: {custom_e}")
                raise LLMServiceResponseError(f"响应自定义规则校验失败: {custom_e}") from custom_e

            # [新增] 如果配置要求保存完整响应，则记录完整响应内容
            if save_full_response:
                self.logger.debug(f"完整响应内容(前500字符): {response_text[:500]}{'...' if len(response_text) > 500 else ''}")
            
            return validated_list # 返回原始列表，其内容已被自定义校验器确认
        except (ValueError, TypeError) as e:
            # 捕获解析器抛出的最终错误
            self.logger.error(f"响应统一解析验证失败: {e}", exc_info=True)
            # 将原始响应内容记录在 DEBUG 级别，避免在控制台输出大段错误文本
            self.logger.debug(f"导致失败的原始响应内容: {response_text}")
            raise LLMServiceResponseError(f"响应解析验证失败: {e}") from e # 将异常向上抛出，由调用方(例如 Annotator)捕获并处理

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
