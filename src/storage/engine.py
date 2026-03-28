"""
存储引擎抽象基类 - 定义统一的存储接口

Storage engine abstract base class - defines unified storage interface
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from contextlib import contextmanager


class StorageEngine(ABC):
    """
    存储引擎抽象基类
    
    提供统一的数据库操作接口，支持多种存储后端
    """

    @abstractmethod
    def connect(self) -> Any:
        """
        建立数据库连接
        
        Returns:
            数据库连接对象
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    def execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            query: SQL 查询语句
            params: 参数元组
            
        Returns:
            查询结果列表
        """
        pass

    @abstractmethod
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL 更新语句
            params: 参数元组
            
        Returns:
            受影响的行数
        """
        pass

    @abstractmethod
    def executemany(self, query: str, seq_of_parameters: List[tuple]) -> int:
        """
        批量执行语句
        
        Args:
            query: SQL 语句
            seq_of_parameters: 参数列表
            
        Returns:
            受影响的行数
        """
        pass

    @abstractmethod
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        Usage:
            with engine.transaction():
                engine.execute(...)
                engine.execute_update(...)
        """
        pass

    @abstractmethod
    def init_schema(self) -> None:
        """初始化数据库表结构"""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接"""
        pass

    @property
    @abstractmethod
    def engine_type(self) -> str:
        """返回引擎类型名称"""
        pass
