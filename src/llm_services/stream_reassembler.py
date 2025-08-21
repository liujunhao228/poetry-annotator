# src/llm_services/stream_reassembler.py

import json
import logging
from typing import AsyncGenerator, List, Dict, Any
from src.llm_response_parser import llm_response_parser
from .exceptions import LLMServiceResponseError

class StreamReassembler:
    """流式响应重组器
    
    负责将不同服务返回的流式响应块重新组装成完整的响应，并进行验证
    """
    
    def __init__(self, provider: str):
        self.provider = provider
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def parse_stream_chunks(self, chunks: AsyncGenerator[str, None]) -> str:
        """将流式响应块重新组装成完整响应
        
        Args:
            chunks: 异步生成器，产生响应块
            
        Returns:
            完整的响应字符串
        """
        complete_response = ""
        async for chunk in chunks:
            if self.provider in ['openai', 'siliconflow']:
                # OpenAI/SiliconFlow格式处理
                complete_response += self._parse_openai_chunk(chunk)
            elif self.provider == 'dashscope':
                # DashScope格式处理
                complete_response += self._parse_dashscope_chunk(chunk)
            elif self.provider == 'gemini':
                # Gemini格式处理
                complete_response += chunk
            else:
                # 默认直接拼接
                complete_response += chunk
                
        self.logger.debug(f"[{self.provider}] 重组完成的响应长度: {len(complete_response)} 字符")
        return complete_response
    
    def _parse_openai_chunk(self, chunk: str) -> str:
        """解析OpenAI格式的流式响应块"""
        try:
            # OpenAI流式响应是纯文本内容块
            return chunk
        except Exception as e:
            self.logger.warning(f"解析OpenAI响应块时出错: {e}")
            return chunk
    
    def _parse_dashscope_chunk(self, chunk: str) -> str:
        """解析DashScope格式的流式响应块"""
        try:
            # DashScope流式响应是JSON格式的块
            chunk_data = json.loads(chunk)
            choices = chunk_data.get('choices', [])
            if choices:
                delta = choices[0].get('delta', {})
                return delta.get('content', '')
            return ""
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析DashScope响应块为JSON: {chunk}")
            return ""
        except Exception as e:
            self.logger.warning(f"解析DashScope响应块时出错: {e}")
            return ""
    
    def validate_complete_response(self, response_text: str) -> List[Dict[str, Any]]:
        """验证完整响应
        
        Args:
            response_text: 完整的响应文本
            
        Returns:
            验证后的标注结果列表
            
        Raises:
            LLMServiceResponseError: 当响应无法验证时
        """
        try:
            return llm_response_parser.parse(response_text)
        except Exception as e:
            self.logger.error(f"验证重组后的完整响应失败: {e}", exc_info=True)
            raise LLMServiceResponseError(f"验证重组后的完整响应失败: {e}") from e