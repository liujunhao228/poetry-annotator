"""
统一 ID 生成器 - 确保全局唯一性

ID Generator - ensures globally unique IDs across different databases
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class IDPrefixConfig:
    """
    ID 前缀配置数据类
    
    定义不同数据库类型的 ID 前缀映射
    """
    # 预定义的 ID 前缀映射
    PREFIX_MAP: Dict[str, int] = field(default_factory=lambda: {
        "TangShi": 1000000,    # 唐诗 ID 前缀：1xxxxxx
        "SongCi": 2000000,     # 宋词 ID 前缀：2xxxxxx
        "YuanQu": 3000000,     # 元曲 ID 前缀：3xxxxxx
        "default": 0,          # 默认前缀：无
    })

    def get_prefix(self, db_name: str) -> int:
        """根据数据库名称获取 ID 前缀"""
        return self.PREFIX_MAP.get(db_name, 0)

    def get_db_name(self, prefix: int) -> str:
        """根据 ID 前缀反推数据库名称"""
        for name, p in self.PREFIX_MAP.items():
            if p == prefix:
                return name
        return "unknown"

    def extract_original_id(self, global_id: int) -> int:
        """从全局 ID 中提取原始 ID"""
        for prefix in sorted(self.PREFIX_MAP.values(), reverse=True):
            if global_id >= prefix and prefix > 0:
                return global_id - prefix
        return global_id


class IDGenerator:
    """
    统一 ID 生成器
    
    为不同数据库的诗词生成全局唯一 ID
    
    Usage:
        generator = IDGenerator("TangShi")
        id1 = generator.generate()      # 1000001
        id2 = generator.generate()      # 1000002
        ids = generator.generate_batch(10)  # [1000003, 1000004, ...]
    """

    def __init__(self, db_name: str = "default"):
        """
        初始化 ID 生成器
        
        Args:
            db_name: 数据库名称/别名（用于确定 ID 前缀）
        """
        self.db_name = db_name
        self._config = IDPrefixConfig()
        self._prefix = self._config.get_prefix(db_name)
        self._counter = 0
        
        logger.info(f"ID 生成器初始化 - 数据库：{db_name}, 前缀：{self._prefix}")

    @property
    def prefix(self) -> int:
        """获取当前 ID 前缀"""
        return self._prefix

    @property
    def counter(self) -> int:
        """获取当前计数器值"""
        return self._counter

    def generate(self) -> int:
        """
        生成全局唯一 ID
        
        Returns:
            全局唯一 ID
        """
        self._counter += 1
        global_id = self._prefix + self._counter
        logger.debug(f"生成 ID: {global_id} (prefix={self._prefix}, counter={self._counter})")
        return global_id

    def generate_batch(self, count: int) -> List[int]:
        """
        批量生成 ID
        
        Args:
            count: 需要生成的 ID 数量
            
        Returns:
            ID 列表
        """
        ids = [self.generate() for _ in range(count)]
        logger.debug(f"批量生成 {count} 个 ID: {ids[0]} - {ids[-1]}")
        return ids

    def reset(self, start_count: int = 0) -> None:
        """
        重置计数器
        
        Args:
            start_count: 新的计数器起始值
        """
        self._counter = start_count
        logger.info(f"ID 生成器计数器已重置：{start_count}")

    def set_prefix(self, prefix: int) -> None:
        """
        手动设置 ID 前缀
        
        Args:
            prefix: 新的 ID 前缀
        """
        old_prefix = self._prefix
        self._prefix = prefix
        logger.info(f"ID 前缀已更新：{old_prefix} -> {prefix}")

    def is_valid_global_id(self, global_id: int) -> bool:
        """
        检查 ID 是否是有效的全局 ID
        
        Args:
            global_id: 要检查的 ID
            
        Returns:
            是否有效
        """
        for prefix in self._config.PREFIX_MAP.values():
            if global_id >= prefix:
                return True
        return False

    def get_db_name_from_id(self, global_id: int) -> str:
        """
        根据全局 ID 获取所属数据库名称
        
        Args:
            global_id: 全局 ID
            
        Returns:
            数据库名称
        """
        for name, prefix in sorted(
            self._config.PREFIX_MAP.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if global_id >= prefix and prefix > 0:
                return name
        return "default"

    def to_global_id(self, original_id: int) -> int:
        """
        将原始 ID 转换为全局 ID
        
        Args:
            original_id: 原始 ID（从 1 开始）
            
        Returns:
            全局 ID
        """
        return self._prefix + original_id

    def to_original_id(self, global_id: int) -> int:
        """
        将全局 ID 转换为原始 ID
        
        Args:
            global_id: 全局 ID
            
        Returns:
            原始 ID
        """
        return self._config.extract_original_id(global_id)
