# src/annotation_data_logger.py

import json
import logging
import time
import os
from typing import Dict, Any, Optional


class AnnotationDataLogger:
    """标注数据集合日志器 - 用于记录即将保存的标注数据"""

    def __init__(self, model_identifier: str):
        """
        初始化集合日志器
        
        Args:
            model_identifier: 模型标识符，用于日志文件命名
        """
        self.model_identifier = model_identifier
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        设置专门用于记录标注数据的logger
        
        Returns:
            配置好的logger实例
        """
        # 生成规范的日志文件名
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        log_filename = f"annotation_data_{self.model_identifier}_{timestamp}.log"
        
        # 确保日志目录存在
        log_dir = os.path.join("logs", "annotation_data")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, log_filename)
        
        # 创建独立的logger
        logger_name = f"annotation_data_{self.model_identifier}_{timestamp}"
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

    def log_annotation_data(self, poem_id: str, annotation_result: Dict[str, Any], status: str = "completed", event_type: str = "annotation_saved"):
        """
        记录即将保存的标注数据（单行格式，便于机器解析）
        
        Args:
            poem_id: 诗词ID
            annotation_result: 标注结果数据
            status: 标注状态 (e.g., "completed", "failed")
            event_type: 事件类型 (e.g., "annotation_saved", "annotation_failed")
        """
        try:
            # 获取当前UTC时间戳
            timestamp = time.time()
            # 构建日志消息 - 单行JSON格式，包含更完善的元数据
            log_entry = {
                "event": event_type,
                "poem_id": poem_id,
                "model": self.model_identifier,
                "status": status,
                "annotation_data": annotation_result,
                "timestamp": timestamp
            }
            
            # 将数据序列化为单行JSON字符串并记录
            log_message = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
            self.logger.info(log_message)
        except Exception as e:
            # 如果记录日志失败，使用主日志记录错误
            logging.getLogger(__name__).error(f"记录标注数据到集合日志失败 - 诗词ID: {poem_id}, 错误: {e}")