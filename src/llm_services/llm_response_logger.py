# src/llm_services/llm_response_logger.py

import json
import logging
import time
import os
from typing import Dict, Any, Optional
from pathlib import Path


class LLMResponseLogger:
    """LLM完整响应日志器 - 用于记录API调用的完整原始响应"""

    def __init__(self, model_config_name: str):
        """
        初始化LLM响应日志器
        
        Args:
            model_config_name: 模型配置名称，用于日志文件命名
        """
        self.model_config_name = model_config_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        设置专门用于记录LLM完整响应的logger
        
        Returns:
            配置好的logger实例
        """
        # 生成规范的日志文件名
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        log_filename = f"llm_response_{self.model_config_name}_{timestamp}.log"
        
        # 确保日志目录存在
        log_dir = Path("logs") / "llm_responses"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / log_filename
        
        # 创建独立的logger
        logger_name = f"llm_response_{self.model_config_name}_{timestamp}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # 防止日志传播到父logger
        
        # 避免重复添加handler
        if not logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 单行格式化器，不添加换行符
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
        
        return logger

    def log_response(self, poem_id: str, response_data: Dict[str, Any], response_text: str, usage: Optional[Dict[str, Any]] = None):
        """
        记录成功的LLM完整响应（单行格式，便于机器解析）
        
        Args:
            poem_id: 诗词ID
            response_data: 完整的响应数据字典 (可能包含 usage, reasoning_content 等)
            response_text: 响应的纯文本内容
            usage: Token使用情况 (可选)
        """
        try:
            # 获取当前UTC时间戳
            timestamp = time.time()
            # 构建日志消息 - 单行JSON格式，包含关键元数据和完整响应
            log_entry = {
                "event": "llm_response_received",
                "poem_id": poem_id,
                "model_config": self.model_config_name,
                "status": "success",
                "response_full_data": response_data, # 完整的响应数据
                "response_text": response_text,      # 纯文本内容
                "usage": usage,                      # Token使用情况
                "timestamp": timestamp
            }
            
            # 将数据序列化为单行JSON字符串并记录
            log_message = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
            self.logger.info(log_message)
        except Exception as e:
            # 如果记录日志失败，使用主日志记录错误
            logging.getLogger(__name__).error(f"记录LLM完整响应日志失败 - 诗词ID: {poem_id}, 错误: {e}")

    def log_error(self, poem_id: str, error: Exception, request_data: Optional[Dict[str, Any]] = None):
        """
        记录LLM调用的错误信息（单行格式，便于机器解析）
        
        Args:
            poem_id: 诗词ID
            error: 发生的异常对象
            request_data: 请求数据 (可选，用于调试)
        """
        try:
            # 获取当前UTC时间戳
            timestamp = time.time()
            # 构建错误日志消息
            log_entry = {
                "event": "llm_call_error",
                "poem_id": poem_id,
                "model_config": self.model_config_name,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "request_data": request_data, # 请求数据，敏感信息已在BaseService中处理
                "timestamp": timestamp
            }
            
            # 将数据序列化为单行JSON字符串并记录
            log_message = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
            self.logger.info(log_message)
        except Exception as e:
            # 如果记录日志失败，使用主日志记录错误
            logging.getLogger(__name__).error(f"记录LLM错误日志失败 - 诗词ID: {poem_id}, 错误: {e}")