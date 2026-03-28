"""
日志配置模块 - 提供灵活的日志配置选项
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .config import ConfigManager


class LoggingConfig:
    """日志配置管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def setup_logging(self,
                     console_level: str = 'INFO',
                     file_level: str = 'DEBUG',
                     log_file: Optional[str] = None,
                     enable_file_log: bool = False,
                     enable_console_log: bool = True,
                     log_format: Optional[str] = None,
                     max_file_size: int = 10 * 1024 * 1024,
                     backup_count: int = 5,
                     quiet_third_party: bool = True) -> None:
        """设置日志配置，支持为控制台和文件设置不同级别"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        if not log_format:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

        if enable_console_log:
            console_handler = logging.StreamHandler(sys.stdout)
            console_level_obj = getattr(logging, console_level.upper(), logging.INFO)
            console_handler.setLevel(console_level_obj)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        if enable_file_log:
            if not log_file:
                project_root = Path(__file__).parent.parent
                logs_dir = project_root / "logs"
                logs_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = str(logs_dir / f"poetry_annotator_{timestamp}.log")

            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_file_size, backupCount=backup_count, encoding='utf-8'
            )
            file_level_obj = getattr(logging, file_level.upper(), logging.DEBUG)
            file_handler.setLevel(file_level_obj)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            if enable_console_log:
                print(f"日志文件：{os.path.abspath(log_file)}")

        if quiet_third_party:
            self._quiet_third_party_loggers()

        self.logger.info("日志系统初始化完成。")
        self.logger.info(f"控制台日志级别：{console_level.upper()}, 文件日志级别：{file_level.upper()}")

    def _quiet_third_party_loggers(self):
        """静音第三方库的日志"""
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('tqdm').setLevel(logging.WARNING)

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)


def setup_default_logging(console_level: Optional[str] = None,
                          file_level: Optional[str] = None,
                          enable_file_log: Optional[bool] = None,
                          log_file: Optional[str] = None,
                          global_config_path: Optional[Path] = None) -> None:
    """
    设置默认日志配置，从配置文件读取并支持命令行覆盖。
    """
    config = {}
    if global_config_path and global_config_path.is_file():
        config_manager_instance = ConfigManager(config_paths=[str(global_config_path)])
        config = config_manager_instance.get_logging_config()
    else:
        print(f"警告：未提供有效的全局配置文件路径，将使用默认日志配置。")

    final_console_level = console_level or config.get('console_log_level', 'INFO')
    final_file_level = file_level or config.get('file_log_level', 'DEBUG')
    final_enable_file_log = enable_file_log if enable_file_log is not None else config.get('enable_file_log', True)
    final_log_file = log_file or config.get('log_file')
    final_enable_console_log = config.get('enable_console_log', True)
    final_max_file_size = config.get('max_file_size', 10) * 1024 * 1024
    final_backup_count = config.get('backup_count', 5)
    final_quiet_third_party = config.get('quiet_third_party', True)

    _logging_config = LoggingConfig()
    _logging_config.setup_logging(
        console_level=final_console_level,
        file_level=final_file_level,
        enable_file_log=final_enable_file_log,
        log_file=final_log_file,
        enable_console_log=final_enable_console_log,
        max_file_size=final_max_file_size,
        backup_count=final_backup_count,
        quiet_third_party=final_quiet_third_party
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)
