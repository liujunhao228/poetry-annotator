"""全局日志服务 - 集中管理应用日志"""

import threading
import queue
from typing import Callable, List, Optional
from collections import deque


class LogService:
    """
    全局日志服务
    
    职责:
    1. 集中管理所有日志输出
    2. 支持多个订阅者（如全局日志面板 + Tab 日志面板）
    3. 线程安全的日志写入
    4. 可配置的日志缓冲
    
    使用示例:
        log_service = LogService()
        
        # 订阅日志
        log_service.subscribe(lambda msg: print(msg))
        
        # 写入日志
        log_service.info("任务开始")
        log_service.error("发生错误")
    """
    
    def __init__(self, max_buffer_size: int = 1000):
        """
        初始化日志服务
        
        Args:
            max_buffer_size: 最大缓冲日志条数
        """
        self._buffer: deque[str] = deque(maxlen=max_buffer_size)
        self._subscribers: List[Callable[[str], None]] = []
        self._lock = threading.Lock()
        self._queue: queue.Queue[str] = queue.Queue()
    
    def subscribe(self, callback: Callable[[str], None]) -> None:
        """
        订阅日志输出
        
        Args:
            callback: 接收日志消息的回调函数
        """
        with self._lock:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[str], None]) -> None:
        """
        取消订阅
        
        Args:
            callback: 要移除的回调函数
        """
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def log(self, message: str) -> None:
        """
        写入日志
        
        Args:
            message: 日志消息
        """
        # 添加到缓冲
        self._buffer.append(message)
        
        # 通知所有订阅者
        with self._lock:
            for callback in self._subscribers:
                try:
                    callback(message)
                except Exception as e:
                    print(f"日志回调失败：{e}")
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self.log(f"[INFO] {message}\n")
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.log(f"[DEBUG] {message}\n")
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.log(f"[WARNING] {message}\n")
    
    def error(self, message: str) -> None:
        """记录错误日志"""
        self.log(f"[ERROR] {message}\n")
    
    def success(self, message: str) -> None:
        """记录成功日志"""
        self.log(f"[SUCCESS] {message}\n")
    
    def get_history(self, lines: Optional[int] = None) -> List[str]:
        """
        获取历史日志
        
        Args:
            lines: 获取的行数，None 表示全部
        
        Returns:
            历史日志列表
        """
        if lines is None:
            return list(self._buffer)
        return list(self._buffer)[-lines:]
    
    def clear(self) -> None:
        """清空日志缓冲"""
        self._buffer.clear()
    
    def get_buffer_size(self) -> int:
        """获取当前缓冲的日志条数"""
        return len(self._buffer)


# 全局日志服务单例
_global_log_service: Optional[LogService] = None


def get_global_log_service() -> LogService:
    """获取全局日志服务单例"""
    global _global_log_service
    if _global_log_service is None:
        _global_log_service = LogService()
    return _global_log_service


def set_global_log_service(service: LogService) -> None:
    """设置全局日志服务"""
    global _global_log_service
    _global_log_service = service
