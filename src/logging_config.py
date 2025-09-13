"""
日志配置模块
提供灵活的日志配置选项，支持不同级别的日志输出
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from src.config import config_manager


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
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5,
                     quiet_third_party: bool = True) -> None:
        """
        [重构] 设置日志配置，支持为控制台和文件设置不同级别
        """
        # [修改] 根日志记录器的级别设为最低级别(DEBUG)，以捕获所有消息并交由handlers过滤
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 清除现有处理器，防止重复记录
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 默认日志格式
        if not log_format:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # [修改] 配置控制台处理器，并设置其独立的级别
        if enable_console_log:
            console_handler = logging.StreamHandler(sys.stdout)
            console_level_obj = getattr(logging, console_level.upper(), logging.INFO)
            console_handler.setLevel(console_level_obj)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # [修改] 配置日志文件处理器，并设置其独立的级别
        if enable_file_log:
            if not log_file:
                # 使用项目根目录下的logs目录
                # 获取项目根目录
                project_root = Path(__file__).parent.parent
                logs_dir = project_root / "logs"
                logs_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = str(logs_dir / f"poetry_annotator_{timestamp}.log")
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_level_obj = getattr(logging, file_level.upper(), logging.DEBUG)
            file_handler.setLevel(file_level_obj)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            if enable_console_log:
                print(f"日志文件: {os.path.abspath(log_file)}")
        
        # 静音第三方库的日志
        if quiet_third_party:
            self._quiet_third_party_loggers()
        
        # 记录配置信息
        self.logger.info("日志系统初始化完成。")
        self.logger.info(f"控制台日志级别: {console_level.upper()}, 文件日志级别: {file_level.upper()}")
    
    def _quiet_third_party_loggers(self):
        """静音第三方库的日志"""
        # 减少HTTP库的日志噪音
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        
        # 减少异步库的日志噪音
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        # 减少其他可能产生噪音的库
        logging.getLogger('tqdm').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)
    
    def set_log_level(self, logger_name: str, level: str):
        """设置指定日志记录器的级别"""
        level_obj = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger(logger_name).setLevel(level_obj)
        self.logger.info(f"设置日志记录器 '{logger_name}' 级别为: {level}")
    
    def create_structured_logger(self, name: str, 
                               include_timestamp: bool = True,
                               include_level: bool = True,
                               include_module: bool = True) -> logging.Logger:
        """
        创建结构化日志记录器
        
        Args:
            name: 日志记录器名称
            include_timestamp: 是否包含时间戳
            include_level: 是否包含日志级别
            include_module: 是否包含模块名
        """
        logger = logging.getLogger(name)
        
        # 创建自定义格式化器
        format_parts = []
        if include_timestamp:
            format_parts.append('%(asctime)s')
        if include_level:
            format_parts.append('%(levelname)s')
        if include_module:
            format_parts.append('%(name)s')
        format_parts.append('%(message)s')
        
        formatter = logging.Formatter(' - '.join(format_parts), datefmt='%Y-%m-%d %H:%M:%S')
        
        # 为这个记录器创建专用处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger


# 全局日志配置实例
logging_config = LoggingConfig()


def setup_default_logging(console_level: Optional[str] = None,
                          file_level: Optional[str] = None,
                          enable_file_log: Optional[bool] = None,
                          log_file: Optional[str] = None) -> None:
    """
    [重构] 设置默认日志配置，从配置文件读取并支持命令行覆盖。
    Args:
        console_level: 控制台日志级别（可选，用于覆盖配置文件）
        file_level: 文件日志级别（可选，用于覆盖配置文件）
        enable_file_log: 是否启用文件日志（可选，用于覆盖配置文件）
        log_file: 日志文件路径（可选，用于覆盖配置文件）
    """
    log_config = {}
    try:
        # [修改] 修正方法名称
        log_config = config_manager.get_effective_logging_config()
    except Exception as e:
        import traceback
        print(f"警告: 读取日志配置失败，使用默认值: {e}")
        print(f"类型 of config_manager: {type(config_manager)}")
        traceback.print_exc()
    # 决定最终的配置值，命令行参数 > 配置文件 > 默认值
    final_console_level = console_level if console_level is not None else log_config.get('console_level', 'INFO')
    final_file_level = file_level if file_level is not None else log_config.get('file_level', 'DEBUG')
    final_enable_file_log = enable_file_log if enable_file_log is not None else log_config.get('enable_file_log', False)
    final_log_file = log_file if log_file is not None else log_config.get('log_file')

    # 其他配置从 log_config 或默认值获取
    final_enable_console_log = log_config.get('enable_console_log', True)
    # 将从配置文件读取的max_file_size（MB）转换为字节
    final_max_file_size = log_config.get('max_file_size', 10) * 1024 * 1024
    final_backup_count = log_config.get('backup_count', 5)
    final_quiet_third_party = log_config.get('quiet_third_party', True)

    logging_config.setup_logging(
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
    return logging_config.get_logger(name)

def get_log_directory() -> Path:
    """
    获取当前配置的日志文件目录。
    如果未配置日志文件，则返回默认的 logs/ 目录。
    """
    log_config = {}
    try:
        log_config = config_manager.get_effective_logging_config()
    except Exception as e:
        logging.getLogger(__name__).warning(f"获取日志配置失败，使用默认日志目录: {e}")

    configured_log_file = log_config.get('log_file')

    if configured_log_file:
        # 如果配置了具体的日志文件，返回其父目录
        return Path(configured_log_file).parent
    else:
        # 如果没有配置日志文件，返回默认的 logs/ 目录
        project_root = Path(__file__).parent.parent.parent # src/logging_config.py -> src -> project_root
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True) # 确保目录存在
        return logs_dir


def log_performance_metrics(operation: str, 
                          start_time: float, 
                          end_time: float,
                          additional_info: Optional[Dict[str, Any]] = None):
    """
    记录性能指标
    
    Args:
        operation: 操作名称
        start_time: 开始时间
        end_time: 结束时间
        additional_info: 额外信息
    """
    duration = end_time - start_time
    logger = get_logger('performance')
    
    message = f"性能指标 - {operation}: {duration:.3f}秒"
    if additional_info:
        info_str = ', '.join([f"{k}: {v}" for k, v in additional_info.items()])
        message += f" ({info_str})"
    
    logger.info(message)


def log_error_with_context(error: Exception, 
                         context: Optional[Dict[str, Any]] = None,
                         logger_name: str = 'error'):
    """
    记录带上下文的错误
    
    Args:
        error: 异常对象
        context: 上下文信息
        logger_name: 日志记录器名称
    """
    logger = get_logger(logger_name)
    
    error_msg = f"错误: {type(error).__name__}: {str(error)}"
    if context:
        context_str = ', '.join([f"{k}: {v}" for k, v in context.items()])
        error_msg += f" | 上下文: {context_str}"
    
    logger.error(error_msg, exc_info=True)
