# src/utils/rate_controller.py
"""
速率控制模块，提供多种速率控制算法实现
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    qps: Optional[float] = None  # 每秒查询数
    rpm: Optional[float] = None  # 每分钟查询数
    max_concurrent: Optional[int] = None  # 最大并发数
    burst: Optional[int] = None  # 突发请求数
    window_size: Optional[int] = None  # 窗口大小(秒)

    def __post_init__(self):
        if self.qps is None and self.rpm is None:
            raise ValueError("必须指定qps或rpm")
        if self.qps is not None and self.rpm is not None:
            raise ValueError("不能同时指定qps和rpm")
        if self.rpm is not None:
            self.qps = self.rpm / 60.0


class RateController(ABC):
    """速率控制器抽象基类"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._lock = asyncio.Lock()

    @abstractmethod
    async def acquire(self) -> None:
        """获取执行权限"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass

    async def release(self) -> None:
        """释放执行权限（可选实现）"""
        pass


class TokenBucketController(RateController):
    """令牌桶速率控制器"""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        rate = config.qps or (config.rpm / 60.0)
        capacity = config.burst or int(rate * 2)
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        logger.info(f"初始化令牌桶控制器: rate={rate}, capacity={capacity}")

    async def _refill(self):
        """补充令牌"""
        now = time.monotonic()
        time_passed = now - self.last_refill_time
        new_tokens = time_passed * self.rate
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill_time = now

    async def acquire(self) -> None:
        """获取令牌"""
        async with self._lock:
            await self._refill()
            while self.tokens < 1:
                # 计算需要等待多久才能获得足够的令牌
                required_tokens = 1 - self.tokens
                wait_time = required_tokens / self.rate
                await asyncio.sleep(wait_time)
                await self._refill()
            self.tokens -= 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "type": "token_bucket",
            "rate": self.rate,
            "capacity": self.capacity,
            "current_tokens": self.tokens,
            "last_refill_time": self.last_refill_time
        }


class LeakyBucketController(RateController):
    """漏桶速率控制器"""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        rate = config.qps or (config.rpm / 60.0)
        capacity = config.burst or int(rate * 2)
        self.rate = rate
        self.capacity = capacity
        self.queue = deque()
        self.last_leak_time = time.monotonic()
        logger.info(f"初始化漏桶控制器: rate={rate}, capacity={capacity}")

    async def _leak(self):
        """漏水"""
        now = time.monotonic()
        time_passed = now - self.last_leak_time
        leaks = int(time_passed * self.rate)
        if leaks > 0:
            for _ in range(min(leaks, len(self.queue))):
                self.queue.popleft()
            self.last_leak_time = now

    async def acquire(self) -> None:
        """添加请求到队列"""
        async with self._lock:
            await self._leak()
            if len(self.queue) >= self.capacity:
                # 队列已满，需要等待
                wait_time = (len(self.queue) - self.capacity + 1) / self.rate
                await asyncio.sleep(wait_time)
                await self._leak()
            self.queue.append(time.monotonic())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "type": "leaky_bucket",
            "rate": self.rate,
            "capacity": self.capacity,
            "queue_size": len(self.queue),
            "last_leak_time": self.last_leak_time
        }


class FixedWindowController(RateController):
    """固定窗口速率控制器"""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        if config.qps:
            self.window_size = config.window_size or 1  # 默认1秒窗口
            self.max_requests = int(config.qps * self.window_size)
        else:  # rpm
            self.window_size = config.window_size or 60  # 默认60秒窗口
            self.max_requests = int((config.rpm / 60.0) * self.window_size)
        self.requests = deque()
        self.window_start = time.monotonic()
        logger.info(f"初始化固定窗口控制器: window_size={self.window_size}, max_requests={self.max_requests}")

    async def _slide_window(self):
        """滑动窗口"""
        now = time.monotonic()
        window_end = self.window_start + self.window_size
        if now >= window_end:
            # 窗口已过期，重置
            self.requests.clear()
            self.window_start = now
        else:
            # 移除窗口外的请求
            expire_time = now - self.window_size
            while self.requests and self.requests[0] <= expire_time:
                self.requests.popleft()

    async def acquire(self) -> None:
        """获取执行权限"""
        async with self._lock:
            await self._slide_window()
            if len(self.requests) >= self.max_requests:
                # 超过限制，需要等待
                next_window_start = self.window_start + self.window_size
                wait_time = next_window_start - time.monotonic()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                await self._slide_window()
            self.requests.append(time.monotonic())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "type": "fixed_window",
            "window_size": self.window_size,
            "max_requests": self.max_requests,
            "current_requests": len(self.requests),
            "window_start": self.window_start
        }


class ConcurrentLimiter:
    """并发限制器"""

    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.current_concurrent = 0
        self._lock = asyncio.Lock()
        logger.info(f"初始化并发限制器: max_concurrent={max_concurrent}")

    async def acquire(self) -> None:
        """获取执行权限"""
        await self.semaphore.acquire()
        async with self._lock:
            self.current_concurrent += 1

    async def release(self) -> None:
        """释放执行权限"""
        self.semaphore.release()
        async with self._lock:
            self.current_concurrent -= 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "type": "concurrent_limiter",
            "max_concurrent": self.max_concurrent,
            "current_concurrent": self.current_concurrent
        }


class CompositeRateController(RateController):
    """复合速率控制器，组合多种控制策略"""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self.controllers = []
        # 创建速率控制器
        if config.qps is not None or config.rpm is not None:
            # 默认使用令牌桶算法
            self.controllers.append(TokenBucketController(config))
        # 创建并发控制器
        if config.max_concurrent is not None:
            self.concurrent_limiter = ConcurrentLimiter(config.max_concurrent)
        else:
            self.concurrent_limiter = None

    async def acquire(self) -> None:
        """获取执行权限"""
        # 先获取并发权限
        if self.concurrent_limiter:
            await self.concurrent_limiter.acquire()
        # 再获取速率控制权限
        for controller in self.controllers:
            await controller.acquire()

    async def release(self) -> None:
        """释放执行权限"""
        if self.concurrent_limiter:
            await self.concurrent_limiter.release()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "type": "composite",
            "controllers": [c.get_stats() for c in self.controllers]
        }
        if self.concurrent_limiter:
            stats["concurrent_limiter"] = self.concurrent_limiter.get_stats()
        return stats


def create_rate_controller(config: RateLimitConfig) -> CompositeRateController:
    """创建速率控制器工厂方法"""
    return CompositeRateController(config)
