# src/utils/async_task_manager.py
"""
异步任务管理器
提供统一的异步任务管理机制
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from contextlib import asynccontextmanager
from .async_error_handler import async_error_handler

logger = logging.getLogger(__name__)


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tasks: List[asyncio.Task] = []
        self.results: List[Any] = []
        self.errors: List[Exception] = []

    async def __aenter__(self):
        """异步上下文管理器入口"""
        logger.debug(f"进入异步任务管理器，最大并发数: {self.max_concurrent}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        logger.debug("退出异步任务管理器")
        # 等待所有任务完成
        if self.tasks:
            results = await asyncio.gather(*self.tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self.errors.append(result)
                else:
                    self.results.append(result)
        
        # 清理任务列表
        self.tasks.clear()

    async def submit_task(self, coro: Awaitable[Any]) -> asyncio.Task:
        """
        提交任务到任务管理器

        Args:
            coro: 要执行的异步协程

        Returns:
            创建的异步任务
        """
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.tasks.append(task)
            logger.debug(f"提交任务，当前任务数: {len(self.tasks)}")
            return task

    async def run_task_with_limit(self, coro: Awaitable[Any]) -> Any:
        """
        在并发限制下运行任务

        Args:
            coro: 要执行的异步协程

        Returns:
            协程的返回值
        """
        async with self.semaphore:
            return await coro

    def get_results(self) -> List[Any]:
        """获取所有任务的结果"""
        return self.results.copy()

    def get_errors(self) -> List[Exception]:
        """获取所有任务的错误"""
        return self.errors.copy()

    def get_task_count(self) -> int:
        """获取任务总数"""
        return len(self.tasks)


@asynccontextmanager
async def async_task_group_context(max_concurrent: int = 10, group_name: str = "任务组"):
    """
    异步任务组上下文管理器

    Args:
        max_concurrent: 最大并发数
        group_name: 任务组名称，用于日志记录
    """
    logger.debug(f"初始化{group_name}，最大并发数: {max_concurrent}")
    task_manager = AsyncTaskManager(max_concurrent)
    try:
        yield task_manager
    finally:
        logger.debug(f"{group_name}执行完成")