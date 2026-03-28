"""
事务管理器 - 管理工作单元和事务边界

Transaction manager - manages unit of work and transaction boundaries
"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from .engine import StorageEngine
from .sqlite_engine import TransactionContext

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    事务管理器
    
    管理工作单元模式，确保数据一致性
    """

    def __init__(self, storage_engine: StorageEngine):
        """
        初始化事务管理器
        
        Args:
            storage_engine: 存储引擎实例
        """
        self._engine = storage_engine
        self._active_transaction: Optional[TransactionContext] = None
        self._in_transaction = False

    @contextmanager
    def begin(self):
        """
        开始一个新事务
        
        Usage:
            with transaction_manager.begin():
                # 执行数据库操作
                repo.add(entity)
        """
        if self._in_transaction:
            logger.warning("嵌套事务检测到，当前事务已活跃")
            yield self._active_transaction
            return

        try:
            logger.debug("开始新事务")
            self._in_transaction = True
            
            with self._engine.transaction() as tx_context:
                self._active_transaction = tx_context
                yield tx_context
                self._active_transaction = None
        except Exception as e:
            logger.error(f"事务执行失败：{e}")
            raise
        finally:
            self._in_transaction = False

    @property
    def is_active(self) -> bool:
        """检查是否有活跃的事务"""
        return self._in_transaction and self._active_transaction is not None

    @property
    def engine(self) -> StorageEngine:
        """获取底层存储引擎"""
        return self._engine


class UnitOfWork:
    """
    工作单元实现
    
    跟踪事务中的变更，支持提交和回滚
    """

    def __init__(self, transaction_manager: TransactionManager):
        """
        初始化工作单元
        
        Args:
            transaction_manager: 事务管理器实例
        """
        self._tm = transaction_manager
        self._new: Dict[str, Any] = {}
        self._dirty: Dict[str, Any] = {}
        self._deleted: Dict[str, Any] = {}

    def register_new(self, key: str, entity: Any) -> None:
        """注册新创建的实体"""
        self._new[key] = entity

    def register_dirty(self, key: str, entity: Any) -> None:
        """注册被修改的实体"""
        self._dirty[key] = entity

    def register_deleted(self, key: str, entity: Any) -> None:
        """注册被删除的实体"""
        self._deleted[key] = entity

    def commit(self) -> None:
        """
        提交工作单元
        
        按顺序处理：新建 -> 更新 -> 删除
        """
        if not self._tm.is_active:
            raise RuntimeError("无法提交：没有活跃的事务")

        logger.debug(f"提交工作单元 - 新建：{len(self._new)}, 更新：{len(self._dirty)}, 删除：{len(self._deleted)}")

        # 清空追踪列表
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    def rollback(self) -> None:
        """回滚工作单元"""
        logger.debug("回滚工作单元")
        
        # 清空追踪列表
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    def clear(self) -> None:
        """清除所有追踪"""
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()
