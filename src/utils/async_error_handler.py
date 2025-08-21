# src/utils/async_error_handler.py
"""
异步错误处理工具
提供统一的异步错误处理机制
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Type, Tuple
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncErrorHandler:
    """异步错误处理器"""

    @staticmethod
    async def handle_async_errors(
        coro,
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        执行异步函数并处理错误，支持重试机制

        Args:
            coro: 要执行的异步函数
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            retry_backoff: 重试延迟倍数
            retry_exceptions: 需要重试的异常类型
            *args: 传递给coro的参数
            **kwargs: 传递给coro的关键词参数

        Returns:
            异步函数的返回值

        Raises:
            Exception: 如果超过最大重试次数或遇到不需要重试的异常
        """
        last_exception = None
        delay = retry_delay

        for attempt in range(max_retries + 1):
            try:
                return await coro(*args, **kwargs)
            except asyncio.CancelledError:
                # 不重试被取消的任务
                logger.info("异步任务被取消")
                raise
            except retry_exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        f"异步任务执行失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}. "
                        f"将在 {delay:.2f} 秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    delay *= retry_backoff
                else:
                    logger.error(
                        f"异步任务执行失败，已达到最大重试次数 ({max_retries + 1}): {e}"
                    )
            except Exception as e:
                # 不在重试异常列表中的异常直接抛出
                logger.error(f"异步任务执行遇到未预期异常: {e}")
                raise

        # 如果所有重试都失败了，抛出最后一个异常
        raise last_exception

    @staticmethod
    @asynccontextmanager
    async def async_context_manager_error_handler(context_name: str = "异步上下文"):
        """
        异步上下文管理器的错误处理装饰器

        Args:
            context_name: 上下文名称，用于日志记录
        """
        try:
            yield
        except asyncio.CancelledError:
            logger.info(f"{context_name}被取消")
            raise
        except Exception as e:
            logger.error(f"{context_name}执行出错: {e}")
            raise


# 创建全局实例
async_error_handler = AsyncErrorHandler()