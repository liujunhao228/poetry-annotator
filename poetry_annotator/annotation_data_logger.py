"""
标注数据集合日志器 - 用于记录即将保存的标注数据
"""

import json
import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional


class AnnotationDataLogger:
    """标注数据集合日志器"""

    def __init__(self, model_identifier: str, log_dir: Optional[str] = None):
        """
        初始化集合日志器

        Args:
            model_identifier: 模型标识符，用于日志文件命名
            log_dir: 日志目录路径（可选）
        """
        self.model_identifier = model_identifier
        self.log_dir = log_dir or os.path.join("logs", "annotation_data")
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置专门用于记录标注数据的 logger"""
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        log_filename = f"annotation_data_{self.model_identifier}_{timestamp}.log"

        os.makedirs(self.log_dir, exist_ok=True)
        log_file_path = os.path.join(self.log_dir, log_filename)

        logger_name = f"annotation_data_{self.model_identifier}_{timestamp}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not logger.handlers:
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def log_annotation_data(self, poem_id: str, annotation_result: Dict[str, Any], 
                           status: str = "completed", event_type: str = "annotation_saved"):
        """
        记录即将保存的标注数据（单行 JSON 格式）

        Args:
            poem_id: 诗词 ID
            annotation_result: 标注结果数据
            status: 标注状态
            event_type: 事件类型
        """
        try:
            timestamp = time.time()
            log_entry = {
                "event": event_type,
                "poem_id": poem_id,
                "model": self.model_identifier,
                "status": status,
                "annotation_data": annotation_result,
                "timestamp": timestamp
            }
            log_message = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
            self.logger.info(log_message)
        except Exception as e:
            logging.getLogger(__name__).error(f"记录标注数据到集合日志失败 - 诗词 ID: {poem_id}, 错误：{e}")
