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


class LoggingConfig:
    """日志配置管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self, 
                     log_level: str = 'INFO',
                     log_file: Optional[str] = None,
                     enable_file_log: bool = False,
                     enable_console_log: bool = True,
                     log_format: Optional[str] = None,
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5,
                     quiet_third_party: bool = True) -> None:
        """
        设置日志配置
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            log_file: 日志文件路径
            enable_file_log: 是否启用文件日志
            enable_console_log: 是否启用控制台日志
            log_format: 自定义日志格式
            max_file_size: 日志文件最大大小（字节）
            backup_count: 日志文件备份数量
            quiet_third_party: 是否静音第三方库的日志
        """
        # 确定日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 默认日志格式
        if not log_format:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 创建格式化器
        formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        if enable_console_log:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 如果启用文件日志，添加文件处理器
        if enable_file_log:
            if not log_file:
                # 创建logs目录
                logs_dir = Path("logs")
                logs_dir.mkdir(exist_ok=True)
                
                # 生成日志文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = str(logs_dir / f"poetry_annotator_{timestamp}.log")
            
            # 创建文件处理器，支持日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            if enable_console_log:
                print(f"日志文件: {log_file}")
        
        # 静音第三方库的日志
        if quiet_third_party:
            self._quiet_third_party_loggers()
        
        # 记录配置信息
        self.logger.info(f"日志系统初始化完成 - 级别: {logging.getLevelName(level)}")
        if enable_file_log and log_file:
            self.logger.info(f"日志文件: {log_file}")
        if enable_console_log:
            self.logger.info("控制台日志已启用")
    
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


def setup_default_logging(log_level: Optional[str] = None, 
                         enable_file_log: Optional[bool] = None,
                         log_file: Optional[str] = None) -> None:
    """
    设置默认日志配置，支持从配置文件读取
    
    Args:
        log_level: 日志级别（可选，优先使用配置文件）
        enable_file_log: 是否启用文件日志（可选，优先使用配置文件）
        log_file: 日志文件路径（可选，优先使用配置文件）
    """
    try:
        from .config_manager import config_manager
        config = config_manager.get_logging_config()
        
        # 使用配置文件中的值，除非显式指定了参数
        final_log_level = log_level or config['log_level']
        final_enable_file_log = enable_file_log if enable_file_log is not None else config['enable_file_log']
        final_log_file = log_file or config['log_file']
        final_enable_console_log = config['enable_console_log']
        final_max_file_size = config['max_file_size'] * 1024 * 1024  # 转换为字节
        final_backup_count = config['backup_count']
        final_quiet_third_party = config['quiet_third_party']
        
    except Exception as e:
        # 如果配置文件读取失败，使用默认值
        print(f"警告: 读取日志配置失败，使用默认值: {e}")
        final_log_level = log_level or 'INFO'
        final_enable_file_log = enable_file_log or True
        final_log_file = log_file
        final_enable_console_log = True
        final_max_file_size = 10 * 1024 * 1024
        final_backup_count = 5
        final_quiet_third_party = True
    
    logging_config.setup_logging(
        log_level=final_log_level,
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