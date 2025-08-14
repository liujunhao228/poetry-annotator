"""模型特定日志配置模块
提供为每个模型创建独立日志文件的功能
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class ModelSpecificLogging:
    """模型特定日志管理器"""

    def __init__(self, model_name: str, base_log_dir: str = "logs"):
        self.model_name = model_name
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(exist_ok=True)
        
        # 创建模型特定的日志目录
        self.model_log_dir = self.base_log_dir / model_name
        self.model_log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(f"model.{model_name}")
        self.handler = None

    def setup_model_logger(self,
                          file_level: str = 'DEBUG',
                          log_format: Optional[str] = None,
                          max_file_size: int = 100 * 1024 * 1024,  # 100MB
                          backup_count: int = 9999) -> logging.Logger:
        """
        为特定模型设置独立的日志文件
        """
        # 清除可能已存在的处理器，防止重复记录
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # 默认日志格式
        if not log_format:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
        formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建带时间戳的日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.model_log_dir / f"{self.model_name}_{timestamp}.log"
        
        # 创建文件处理器
        self.handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        file_level_obj = getattr(logging, file_level.upper(), logging.DEBUG)
        self.handler.setLevel(file_level_obj)
        self.handler.setFormatter(formatter)
        
        # 设置logger
        self.logger.addHandler(self.handler)
        self.logger.setLevel(file_level_obj)
        # 防止日志传播到根logger，避免重复记录
        self.logger.propagate = False
        
        return self.logger

    def get_logger(self) -> logging.Logger:
        """获取模型特定的日志记录器"""
        return self.logger
