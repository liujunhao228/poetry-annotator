"""
Repository 抽象基类 - 定义通用数据访问接口

Base repository patterns for data access abstraction
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from contextlib import contextmanager

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    通用仓库接口
    
    提供基本的 CRUD 操作抽象
    """

    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[T]:
        """根据 ID 获取单个实体"""
        pass

    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """获取所有实体（支持分页）"""
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """添加单个实体"""
        pass

    @abstractmethod
    def add_batch(self, entities: List[T]) -> List[T]:
        """批量添加实体"""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """更新单个实体"""
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """删除单个实体"""
        pass

    @abstractmethod
    def count(self) -> int:
        """获取实体总数"""
        pass


class UnitOfWork(ABC):
    """
    工作单元抽象基类
    
    用于管理事务边界，确保数据一致性
    """

    @abstractmethod
    def __enter__(self) -> 'UnitOfWork':
        """进入事务上下文"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出事务上下文"""
        pass

    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """检查事务是否活跃"""
        pass
