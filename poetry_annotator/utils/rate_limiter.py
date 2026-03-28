"""
异步令牌桶速率限制器
"""

import asyncio
import time
from typing import Optional


class AsyncTokenBucket:
    """一个简单的异步令牌桶速率限制器"""

    def __init__(self, rate: float, capacity: int, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        初始化令牌桶.

        Args:
            rate: 每秒生成的令牌数 (例如，QPS).
            capacity: 令牌桶的容量 (突发能力).
            loop: 事件循环 (可选).
        """
        if rate <= 0:
            raise ValueError("Rate must be positive.")
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")

        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self._lock = asyncio.Lock()
        self.loop = loop or asyncio.get_running_loop()

    async def _refill(self):
        """根据流逝的时间补充令牌"""
        now = time.monotonic()
        time_passed = now - self.last_refill_time
        new_tokens = time_passed * self.rate

        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill_time = now

    async def acquire(self, tokens_to_consume: int = 1) -> None:
        """获取一个或多个令牌，如果令牌不足则异步等待"""
        if tokens_to_consume > self.capacity:
            raise ValueError(f"Cannot acquire {tokens_to_consume} tokens, exceeds capacity {self.capacity}.")

        async with self._lock:
            await self._refill()
            while self.tokens < tokens_to_consume:
                required_tokens = tokens_to_consume - self.tokens
                wait_time = required_tokens / self.rate
                await asyncio.sleep(wait_time)
                await self._refill()

            self.tokens -= tokens_to_consume

    def __repr__(self):
        return (f"<AsyncTokenBucket rate={self.rate}, capacity={self.capacity}, "
                f"tokens~={self.tokens:.2f}>")
