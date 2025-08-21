# src/utils/async_context_manager.py
"""
异步上下文管理工具
提供统一的异步上下文管理机制
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, AsyncIterator
from contextlib import asynccontextmanager
from .async_error_handler import async_error_handler

logger = logging.getLogger(__name__)


class AsyncContextManager:
    """异步上下文管理器"""

    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._cleanup_callbacks: List[Callable] = []

    async def __aenter__(self):
        """异步上下文管理器入口"""
        logger.debug("进入异步上下文管理器")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        logger.debug("退出异步上下文管理器")
        # 执行清理回调
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.warning(f"执行清理回调时出错: {e}")

        # 清理资源
        self._resources.clear()
        self._cleanup_callbacks.clear()

    def register_resource(self, name: str, resource: Any):
        """注册资源"""
        self._resources[name] = resource
        logger.debug(f"注册资源: {name}")

    def get_resource(self, name: str) -> Any:
        """获取资源"""
        return self._resources.get(name)

    def register_cleanup_callback(self, callback: Callable):
        """注册清理回调"""
        self._cleanup_callbacks.append(callback)
        logger.debug("注册清理回调")


@asynccontextmanager
async def async_timeout_context(timeout: float, operation_name: str = "异步操作"):
    """
    异步超时上下文管理器

    Args:
        timeout: 超时时间（秒）
        operation_name: 操作名称，用于日志记录
    """
    try:
        async with asyncio.timeout(timeout):
            logger.debug(f"开始{operation_name}，超时时间: {timeout}秒")
            yield
    except asyncio.TimeoutError:
        logger.error(f"{operation_name}超时 ({timeout}秒)")
        raise
    except Exception as e:
        logger.error(f"{operation_name}执行出错: {e}")
        raise


@asynccontextmanager
async def async_resource_pool_context(resources: List[Any], pool_name: str = "资源池"):
    """
    异步资源池上下文管理器

    Args:
        resources: 资源列表
        pool_name: 资源池名称，用于日志记录
    """
    logger.debug(f"初始化{pool_name}，资源数量: {len(resources)}")
    try:
        yield resources
    finally:
        # 清理资源
        for resource in resources:
            if hasattr(resource, 'close'):
                try:
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                except Exception as e:
                    logger.warning(f"关闭资源时出错: {e}")
        logger.debug(f"{pool_name}清理完成")