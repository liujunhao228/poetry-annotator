# src/llm_services/siliconflow_service.py

import os
import asyncio
import json
import logging
import re  # 导入正则表达式模块
from typing import Dict, Any, Optional, List, Union, Tuple, AsyncGenerator
import httpx
from .base_service import BaseLLMService
from .schemas import PoemData, EmotionSchema
from ..llm_response_parser import ILLMResponseParser


class SiliconFlowService(BaseLLMService):
    """
    SiliconFlow API服务实现 (已重构，并增加响应适配器)
    
    此类现在负责解析和验证其自身的配置，并能通过适配器模式
    兼容不同源（如Ollama）的响应格式。
    """
    
    def __init__(self, config: Dict[str, Any], model_config_name: str, response_parser: Optional[ILLMResponseParser] = None):
        """
        初始化并解析配置字典
        """
        # 调用基类构造函数，传递完整的config字典、模型配置名称和可选的response_parser实例
        super().__init__(config, model_config_name, response_parser)
        
        # 配置解析和验证逻辑，从 LLMFactory 和旧的 __init__ 移入此类
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
        self.top_k = int(self.config['top_k']) if self.config.get('top_k') else None
        self.seed = int(self.config['seed']) if self.config.get('seed') else None
        
        if self.top_k is not None and self.top_k <= 0: raise ValueError("top_k必须大于0")
        if self.seed is not None and self.seed < 0: raise ValueError("seed必须大于等于0")

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
            except Exception as e:
                self.logger.warning(f"解析response_format配置时发生未知错误: '{response_format_raw}', 错误: {e}。将忽略此配置。")
                self.response_format = None
        else:
            self.response_format = None
            
        if self.response_format:
             if not isinstance(self.response_format, dict) or 'type' not in self.response_format or self.response_format['type'] not in ['json_object', 'text']:
                raise ValueError("response_format 格式不正确，必须是包含'type'键的字典，且'type'为'json_object'或'text'。")

        # 特殊参数
        self.stream = self.config.get('stream', 'false').lower() == 'true'

        # 读取响应适配器配置，如果未配置则为 None
        self.response_adapter = self.config.get('response_adapter')

    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """构建消息列表"""
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
        """构建完整的请求体"""
        request_body = {
            "model": self.model,
            "messages": self._build_messages(system_prompt, user_prompt),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n
        }
        
        if self.top_k is not None: request_body["top_k"] = self.top_k
        if self.stop is not None: request_body["stop"] = self.stop
        if self.seed is not None: request_body["seed"] = self.seed
        if self.response_format is not None: request_body["response_format"] = self.response_format
        if self.stream: request_body["stream"] = self.stream
        
        return request_body
    
    def _log_initialization(self):
        """记录简洁的初始化信息"""
        self.logger.info(f"[{self.provider.capitalize()}] 服务初始化完成 - 模型: {self.model}")
        params_summary = (
            f"温度: {self.temperature}, 最大token: {self.max_tokens}, 超时: {self.timeout}s, "
            f"top_p: {self.top_p}, top_k: {self.top_k}, n: {self.n}, stream: {self.stream}, "
            f"seed: {self.seed}, 停止序列: {self.stop}, 响应格式: {self.response_format}, "
            f"响应适配器: {self.response_adapter or '无'}"
        )
        self.logger.debug(f"[{self.provider.capitalize()}] 详细初始化参数: {params_summary}")

    async def health_check(self) -> Tuple[bool, str]:
        self.logger.info(f"对模型 '{self.model}' 执行健康检查...")
        try:
            # 构建一个非常轻量级的请求
            request_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Health check"}],
                "max_tokens": 1
            }
            
            # 为健康检查使用较短的超时
            timeout = httpx.Timeout(10.0)

            response = await self.client.post(f"{self.base_url}", json=request_data, timeout=timeout)
            response.raise_for_status()

            _ = response.json()
            
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

    # 响应适配器方法
    def _adapt_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """根据配置，对不同来源的响应进行格式转换，使其统一。"""
        if self.response_adapter == 'ollama':
            self.logger.debug("检测到Ollama响应适配器，开始转换格式...")
            try:
                # 安全地导航到message对象
                message = response_data.get('choices', [{}])[0].get('message')
                if not message or not isinstance(message, dict):
                    self.logger.warning("Ollama响应适配器：在响应中未找到有效的 'message' 对象。")
                    return response_data
                
                content = message.get('content', '')

                # 使用正则表达式从 content 中提取 <think> 标签包裹的内容
                # re.DOTALL 使得 . 可以匹配包括换行符在内的任意字符
                match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                
                if match:
                    # 提取思考过程
                    reasoning_text = match.group(1).strip()
                    # 将提取的内容填充到 reasoning_content 字段
                    message['reasoning_content'] = reasoning_text
                    self.logger.debug("成功从<think>标签提取并填充了reasoning_content。")
                else:
                    self.logger.debug("未在响应中找到<think>标签，不进行转换。")

            except (KeyError, IndexError, AttributeError) as e:
                # 捕获可能的结构错误
                self.logger.warning(f"Ollama响应格式转换失败，响应结构不符合预期: {e}", exc_info=True)
                # 转换失败则返回原始数据，让后续步骤处理
                return response_data
        
        # 如果没有适配器或者适配器名称不匹配，直接返回原始数据
        return response_data

    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        """
        实现基类的抽象方法，并集成响应适配器和速率限制。
        此方法是唯一的API调用入口，负责完整的处理流程。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成"
        try:
            # 步骤 1: 使用基类方法准备提示词
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt
            
            # 步骤 2: 构建请求体
            request_data = self.build_request_body(system_prompt, user_prompt)
            # 确保流式响应为 False
            request_data["stream"] = False
            
            # 步骤 3: 记录和发送请求
            self.log_request_details(
                request_body=request_data,
                headers=dict(self.client.headers.items()),
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
            
            response = await self.client.post(f"{self.base_url}", json=request_data)
            response.raise_for_status()
            
            # 步骤 4: 解析和适配响应
            response_data = response.json()
            
            adapted_response_data = self._adapt_response(response_data)
            
            self._validate_siliconflow_response(adapted_response_data)
            
            response_text = self._extract_response_content(adapted_response_data)
            usage = adapted_response_data.get('usage', {})
            
            result = self.validate_response(response_text)
            
            # [修改] 传递 poem_id 和完整响应内容用于日志记录
            # 确保 poem 是 PoemData 实例，使用 .id 访问属性而不是 .get()
            self.log_response_details(
                poem_id=poem.id,
                parsed_data=result, # 解析后的数据
                response_data=adapted_response_data, # 完整的响应数据字典
                response_text=response_text, # 纯文本内容
                usage=usage # Token使用情况
            )
            
            return result


        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in [429, 500, 502, 503, 504]:
                self.logger.warning(f"[{self.provider.capitalize()}] API可重试HTTP错误 (status: {status_code}): {e}")
                # 确保 poem 是 PoemData 实例，使用 .id 访问属性而不是 .get()
                self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
                raise
            else:
                self.logger.error(f"[{self.provider.capitalize()}] API不可重试HTTP错误 (status: {status_code}): {e}", exc_info=True)
                # 确保 poem 是 PoemData 实例，使用 .id 访问属性而不是 .get()
                self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
                raise LLMServiceAPIError(f"API HTTP错误 (status: {status_code}): {e.response.text}")
                
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            self.logger.warning(f"[{self.provider.capitalize()}] API连接/超时错误: {e}")
            # 确保 poem 是 PoemData 实例，使用 .id 访问属性而不是 .get()
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            raise LLMServiceTimeoutError(f"API连接/超时错误: {e}")
            
        except Exception as e:
            self.logger.error(f"[{self.provider.capitalize()}] API调用时发生未知错误: {e}", exc_info=True)
            # 确保 poem 是 PoemData 实例，使用 .id 访问属性而不是 .get()
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            raise LLMServiceAPIError(f"API调用失败: {e}")

    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> AsyncGenerator[str, None]:
        """
        [新增] 实现流式响应方法。
        """
        request_data = None
        user_prompt_for_logging: str = "Prompt未生成"
        try:
            system_prompt, user_prompt = self.prepare_prompts(poem, emotion_schema)
            user_prompt_for_logging = user_prompt

            messages = self._build_messages(system_prompt, user_prompt)
            
            request_data = self.build_request_body(system_prompt, user_prompt)
            # 关键: 确保启用流式响应
            request_data["stream"] = True

            self.log_request_details(
                request_body=request_data,
                headers=dict(self.client.headers.items()),
                prompt=system_prompt
            )

            await self._ensure_rate_controller()
            if self.rate_controller:
                await self.rate_controller.acquire()
            
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            # 使用 httpx 的 stream 方法发送流式请求
            async with self.client.stream("POST", f"{self.base_url}", json=request_data) as response:
                response.raise_for_status()
                # 逐行读取响应流
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:] # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            # [修改] 直接从流式响应块中提取 delta.content
                            # 流式响应的结构与完整响应不同，增量内容在 delta.content 中
                            choices = chunk_data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            self.logger.warning(f"[{self.provider.capitalize()}] 无法解析流式响应块为JSON: {data_str}")
                        except Exception as e:
                            self.logger.warning(f"[{self.provider.capitalize()}] 处理流式响应块时出错: {e}")
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            self.logger.error(f"[{self.provider.capitalize()}] 流式API HTTP错误 (status: {status_code}): {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            if status_code in [429, 500, 502, 503, 504]:
                raise # 可重试的错误向上抛出
            else:
                raise LLMServiceAPIError(f"流式API HTTP错误 (status: {status_code}): {e.response.text}")
                
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            self.logger.warning(f"[{self.provider.capitalize()}] 流式API连接/超时错误: {e}")
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            raise LLMServiceTimeoutError(f"流式API连接/超时错误: {e}")
            
        except Exception as e:
            self.logger.error(f"[{self.provider.capitalize()}] 流式API调用时发生未知错误: {e}", exc_info=True)
            self.log_error_details(poem.id, e, request_data, user_prompt_for_logging)
            raise LLMServiceAPIError(f"流式API调用失败: {e}")

    def _validate_siliconflow_response(self, response_data: Dict[str, Any]):
        """验证 SiliconFlow/OpenAI 兼容的API响应结构"""
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
    
    def _extract_reasoning_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从响应数据中提取推理内容。
        [说明] 此方法无需修改，因为响应适配器已经将Ollama的<think>内容
        填充到了标准的`reasoning_content`字段。
        """
        choices = response_data.get('choices', [])
        if not choices:
            return None
        
        choice = choices[0]
        message = choice.get('message', {})
        reasoning_content = message.get('reasoning_content')
        
        return reasoning_content
    
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
        
        if self.response_format:
            info["response_format_info"] = {
                "type": self.response_format.get("type"),
                "description": "JSON对象格式" if self.response_format.get("type") == "json_object" else "文本格式"
            }
        
        return info
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
        # 调用父类的__aexit__
        await super().__aexit__(exc_type, exc_val, exc_tb)
