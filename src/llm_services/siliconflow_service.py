# src/llm_services/siliconflow_service.py

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
import httpx
from .base_service import BaseLLMService


class SiliconFlowService(BaseLLMService):
    """SiliconFlow API服务实现 (已重构)
    
    此类现在负责解析和验证其自身的配置。
    """
    
    # [修改] __init__ 方法签名已更改，接收完整的配置字典
    def __init__(self, config: Dict[str, Any], model_config_name: str):
        """
        [修改] 初始化并解析配置字典
        """
        # [修改] 调用基类构造函数，传递完整的config字典和模型配置名称
        super().__init__(config, model_config_name)
        
        # [新] 配置解析和验证逻辑，从 LLMFactory 和旧的 __init__ 移入此类
        self._parse_and_validate_config()
        
        # 初始化HTTP客户端，使用通过配置解析得到的超时时间和API密钥
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
        """[新] 集中处理配置的解析、类型转换和验证"""
        # 基础参数
        # 注意：get() 用于提供默认值，而 'key' in self.config 或 get('key') 用于判断是否存在
        self.temperature = float(self.config.get('temperature', 0.3))
        self.max_tokens = int(self.config.get('max_tokens', 1000))
        self.timeout = int(self.config.get('timeout', 30))
        self.top_p = float(self.config.get('top_p', 1.0))
        # 基础参数
        self.n = int(self.config.get('n', 1))

        if not (0 <= self.temperature <= 2): raise ValueError("temperature必须在0-2之间")
        if self.max_tokens <= 0: raise ValueError("max_tokens必须大于0")
        if self.timeout <= 0: raise ValueError("timeout必须大于0")
        if not (0 <= self.top_p <= 1): raise ValueError("top_p必须在0-1之间")
        if self.n <= 0: raise ValueError("n必须大于0")

        # 高级参数
        self.top_k = int(self.config['top_k']) if self.config.get('top_k') else None
        self.seed = int(self.config['seed']) if self.config.get('seed') else None
        
        if self.top_k is not None and self.top_k <= 0: raise ValueError("top_k必须大于0")
        if self.seed is not None and self.seed < 0: raise ValueError("seed必须大于等于0")

        # 停止序列
        stop_raw = self.config.get('stop')
        # 如果 stop_raw 是空字符串，split(',') 会得到 ['']，所以需要过滤空字符串
        self.stop = [s.strip() for s in stop_raw.split(',') if s.strip()] if stop_raw else None

        # 响应格式
        response_format_raw = self.config.get('response_format')
        if response_format_raw:
            try:
                # 使用 json.loads 解析 JSON 字符串，更安全和规范
                self.response_format = json.loads(response_format_raw)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析response_format配置为JSON: '{response_format_raw}'。将忽略此配置。请确保其是有效的JSON字符串 (例如 '{{\"type\": \"json_object\"}}')。")
                self.response_format = None
            except Exception as e:
                self.logger.warning(f"解析response_format配置时发生未知错误: '{response_format_raw}', 错误: {e}。将忽略此配置。")
                self.response_format = None
        else:
            self.response_format = None # 如果没有配置，则为 None
            
        if self.response_format:
             if not isinstance(self.response_format, dict) or 'type' not in self.response_format or self.response_format['type'] not in ['json_object', 'text']:
                # 提供更具体的错误信息，帮助调试
                raise ValueError("response_format 格式不正确，必须是包含'type'键的字典，且'type'为'json_object'或'text'。")

        # 特殊参数
        self.stream = self.config.get('stream', 'false').lower() == 'true'

    # [已移除] _validate_basic_params, _validate_advanced_params, _validate_stop_sequences, 
    #         _validate_special_params, _validate_response_format 方法，其逻辑已移至 _parse_and_validate_config。

    # [已移除] _build_system_prompt 和 _build_user_prompt 方法，其功能已上移至 BaseLLMService。
    
    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """
        构建消息列表
        (此方法逻辑保持不变，但其调用位置和参数来源在标注流程中已改变)
        """
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        return messages
    
    def build_request_body(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        构建完整的请求体
        请求格式参考：https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
        """
        # 基础必需参数
        request_body = {
            "model": self.model,
            "messages": self._build_messages(system_prompt, user_prompt),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n
        }
        
        # 可选采样参数
        if self.top_k is not None:
            request_body["top_k"] = self.top_k
        
        # 停止序列
        if self.stop is not None:
            request_body["stop"] = self.stop
        
        # 随机种子
        if self.seed is not None:
            request_body["seed"] = self.seed
        
        # 响应格式
        if self.response_format is not None:
            request_body["response_format"] = self.response_format
        
        # 流式响应
        if self.stream:
            request_body["stream"] = self.stream
        
        return request_body
    
    def _log_initialization(self):
        """记录初始化信息"""
        self.logger.info(f"SiliconFlow服务初始化完成 - 模型: {self.model}")
        self.logger.info(f"基础参数 - 温度: {self.temperature}, 最大token: {self.max_tokens}, 超时: {self.timeout}s")
        self.logger.info(f"采样参数 - top_p: {self.top_p}, top_k: {self.top_k}")
        self.logger.info(f"生成参数 - n: {self.n}")
        self.logger.info(f"特殊参数 - stream: {self.stream}")
        if self.response_format:
            self.logger.info(f"响应格式: {self.response_format}")
        if self.stop:
            self.logger.info(f"停止序列: {self.stop}")
        if self.seed is not None:
            self.logger.info(f"随机种子: {self.seed}")
    
    # [修改] 实现基类的新抽象方法。取代了旧的 annotate_poem 和 annotate_poem_with_templates。
    async def annotate_poem(self, poem: Dict[str, Any], emotion_schema: str) -> Dict[str, Any]:
        """
        [修改] 实现基类的新抽象方法。
        此方法现在是唯一的API调用入口，负责完整的处理流程。
        
        Args:
            poem: 包含诗词信息的字典。
            emotion_schema: 情感分类体系的文本。
            
        Returns:
            包含标注结果的字典。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成" # 用于在异常处理时记录提示词
        try:
            self.logger.debug(f"开始调用SiliconFlow API - 模型: {self.model}")

            # 步骤 1: 使用基类方法 prepare_prompts 准备提示词。
            # 这替代了旧方法中手动构建 system_prompt 和 user_prompt 的逻辑。
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt # 赋值以便在异常时进行日志记录
            
            # 步骤 2: 构建请求体
            request_data = self.build_request_body(system_prompt, user_prompt)
            
            # 步骤 3: 记录和发送请求
            # 记录完整请求信息
            self.log_request_details(
                request_body=request_data,
                headers=dict(self.client.headers.items()),
                prompt=user_prompt_for_logging
            )
            
            response = await self.client.post(f"{self.base_url}", json=request_data)
            response.raise_for_status() # 检查HTTP响应状态码
            
            # 步骤 4: 解析和验证响应
            response_data = response.json()
            self._validate_siliconflow_response(response_data) # 验证SiliconFlow特有的响应结构
            
            response_text = self._extract_response_content(response_data) # 提取LLM返回的内容文本
            usage = response_data.get('usage', {})
            
            self.log_response_details(response_data, usage)
            self._log_token_usage_details(usage)
            
            # 统一调用基类的 validate_response 方法进行通用解析和业务内容验证
            result = self.validate_response(response_text)
            if isinstance(result, list):
                return result[0] if result else {}
            return result

        except httpx.HTTPStatusError as e:
            # 重新抛出错误处理逻辑，以触发 tenacity 的重试
            status_code = e.response.status_code
            if status_code in [429, 500, 502, 503, 504]:
                # 可重试的错误：429(限流)、500(服务器错误)、502(网关错误)、503(服务不可用)、504(网关超时)
                self.logger.warning(f"SiliconFlow API可重试HTTP错误 (status: {status_code}): {e}")
                self.log_error_details(e, request_data, user_prompt_for_logging)
                raise # 重新抛出以触发tenacity重试
            else:
                # 不可重试的错误：400(请求错误)、401(认证失败)、404(资源不存在)
                self.logger.error(f"SiliconFlow API不可重试HTTP错误 (status: {status_code}): {e}", exc_info=True)
                self.log_error_details(e, request_data, user_prompt_for_logging)
                return self.format_error_response(f"API HTTP错误 (status: {status_code}): {e.response.text}")
                
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # 连接和超时错误是可重试的
            self.logger.warning(f"SiliconFlow API连接/超时错误: {e}")
            self.log_error_details(e, request_data, user_prompt_for_logging)
            raise # 重新抛出以触发tenacity重试
            
        except Exception as e:
            # 捕获其他所有非预期的、不可重试的错误（如JSON解析、业务内容验证失败等）
            self.logger.error(f"SiliconFlow API调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(e, request_data, user_prompt_for_logging)
            return self.format_error_response(str(e))

    # [已移除] annotate_poem_with_templates 和 _annotate_with_templates 方法，其功能已整合到 annotate_poem 中。
    
    def _validate_siliconflow_response(self, response_data: Dict[str, Any]):
        """
        验证 SiliconFlow API 响应结构
        (此方法逻辑保持不变)
        """
        if not isinstance(response_data, dict):
            raise ValueError("响应数据必须是字典格式")
        
        # 检查必需字段
        required_fields = ['id', 'object', 'created', 'model', 'choices']
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"响应缺少必需字段: {field}")
        
        # 验证 choices 数组
        choices = response_data.get('choices', [])
        if not isinstance(choices, list) or not choices:
            raise ValueError("choices字段必须是非空数组")
        
        # 验证第一个 choice
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
        """
        从响应数据中提取主要内容
        (此方法逻辑保持不变)
        """
        choices = response_data.get('choices', [])
        if not choices:
            raise ValueError("响应中没有找到choices")
        
        choice = choices[0]
        message = choice.get('message', {})
        content = message.get('content', '')
        
        if not content:
            self.logger.warning("响应内容为空")
        
        return content
    
    def _extract_reasoning_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从响应数据中提取推理内容
        (此方法逻辑保持不变)
        """
        choices = response_data.get('choices', [])
        if not choices:
            return None
        
        choice = choices[0]
        message = choice.get('message', {})
        reasoning_content = message.get('reasoning_content')
        
        return reasoning_content
    
    def _log_token_usage_details(self, usage: Dict[str, Any]):
        """
        记录详细的token使用情况
        (此方法逻辑保持不变)
        """
        if not usage:
            self.logger.debug("未获取到token使用情况")
            return
        
        # 基础token信息
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        self.logger.debug(f"Token使用情况 - 提示: {prompt_tokens}, 完成: {completion_tokens}, 总计: {total_tokens}")
        
        # 详细的完成token信息
        completion_details = usage.get('completion_tokens_details', {})
        if completion_details:
            reasoning_tokens = completion_details.get('reasoning_tokens', 0)
            if reasoning_tokens > 0:
                self.logger.debug(f"推理token使用: {reasoning_tokens}")
                reasoning_ratio = (reasoning_tokens / completion_tokens) * 100 if completion_tokens > 0 else 0
                self.logger.debug(f"推理token占比: {reasoning_ratio:.1f}%")
    
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
            "top_k": self.top_k,
            "stop": self.stop,
            "seed": self.seed,
            "response_format": self.response_format,
            "stream": self.stream,
            "n": self.n
        }
        
        # 添加 response_format 的详细信息
        if self.response_format:
            info["response_format_info"] = {
                "type": self.response_format.get("type"),
                "description": "JSON对象格式" if self.response_format.get("type") == "json_object" else "文本格式"
            }
        
        return info
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.aclose()