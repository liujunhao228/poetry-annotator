"""
数据库初始化器模块
"""
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    from ..config import config_manager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from src.config import config_manager

try:
    from .adapter import get_database_adapter
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent))
    from adapter import get_database_adapter

try:
    from ..label_parser import get_label_parser
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from label_parser import get_label_parser

from .exceptions import DatabaseError


class DatabaseInitializer:
    """数据库初始化器，负责初始化和管理多数据库"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_configs = self._get_database_configs()
        
    def _get_database_configs(self) -> Dict[str, str]:
        """获取所有主数据库配置名称"""
        db_config = config_manager.get_database_config()
        
        # 获取所有配置的主数据库名称
        if 'db_paths' in db_config:
            return {name: "" for name in db_config['db_paths'].keys()}
        # 回退到旧的单数据库配置
        elif 'db_path' in db_config:
            return {"default": ""}
        else:
            # 如果没有主数据库配置，使用全局配置中的separate_db_paths来获取主数据库名称
            separate_db_config = db_config.get('separate_db_paths', {})
            if separate_db_config:
                # 从分离数据库路径中提取主数据库名称
                main_db_names = set()
                for path in separate_db_config.values():
                    # 查找 {main_db_name} 占位符中的名称
                    if '{main_db_name}' in path:
                        # 如果使用占位符，我们需要从配置中获取所有可能的主数据库名称
                        # 这里我们简单地返回一个默认名称
                        main_db_names.add("default")
                    else:
                        # 从路径中提取主数据库名称
                        parts = path.split('/')
                        if len(parts) > 2:
                            main_db_names.add(parts[1])
                return {name: "" for name in main_db_names}
            else:
                return {"default": ""}
    
    def initialize_all_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化所有配置的分离数据库"""
        results = {}
        
        # 为每个主数据库初始化分离数据库
        for db_name in self.db_configs.keys():
            try:
                self.logger.info(f"开始初始化分离数据库结构 for {db_name}")
                # 使用初始化分离数据库的方法
                result = self.initialize_separate_databases(clear_existing)
                results[db_name] = result
                self.logger.info(f"分离数据库 {db_name} 初始化完成")
            except Exception as e:
                self.logger.error(f"初始化分离数据库 {db_name} 失败: {e}")
                results[db_name] = {"error": str(e)}
                
        return results
    
    def initialize_database(self, db_name: str, db_path: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化单个数据库（已废弃，仅保留用于兼容性）"""
        self.logger.warning("initialize_database 方法已废弃，使用 initialize_separate_databases 代替")
        
        # 调用初始化分离数据库的方法
        try:
            from .separate_databases import get_separate_db_manager
            # 获取针对特定主数据库的分离数据库管理器
            separate_db_manager = get_separate_db_manager(main_db_name=db_name)
            
            # 初始化该主数据库对应的分离数据库
            result = separate_db_manager.initialize_all_databases(clear_existing)
            
            # 返回兼容格式的结果
            return {
                "db_name": db_name,
                "status": "success",
                "message": f"分离数据库 {db_name} 初始化完成"
            }
        except Exception as e:
            self.logger.error(f"初始化分离数据库 {db_name} 失败: {e}")
            return {
                "db_name": db_name,
                "status": "error",
                "message": str(e)
            }
        
    def initialize_separate_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化分离的数据库结构，为每个主数据库创建独立的分离数据库"""
        results = {}
        
        # 为每个主数据库创建独立的分离数据库
        for db_name in self.db_configs.keys():
            from .separate_databases import get_separate_db_manager
            
            # 获取针对特定主数据库的分离数据库管理器
            separate_db_manager = get_separate_db_manager(main_db_name=db_name)
            
            # 初始化该主数据库对应的分离数据库
            db_results = separate_db_manager.initialize_all_databases(clear_existing)
            results[db_name] = db_results
        
        return results
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有分离数据库的统计信息"""
        stats = {}
        
        # 为每个主数据库获取分离数据库统计信息
        for db_name in self.db_configs.keys():
            try:
                from .separate_databases import get_separate_db_manager
                # 获取针对特定主数据库的分离数据库管理器
                separate_db_manager = get_separate_db_manager(main_db_name=db_name)
                
                # 获取分离数据库统计信息
                separate_stats = separate_db_manager.get_database_stats()
                stats[db_name] = separate_stats
            except Exception as e:
                stats[db_name] = {
                    "status": "error",
                    "message": str(e)
                }
                
        return stats


def initialize_all_databases_from_source_folders(clear_existing: bool = False) -> Dict[str, Dict[str, int]]:
    """根据source_json下的子文件夹初始化所有数据库"""
    # 延迟导入以避免循环依赖
    from .manager import DataManager
    
    data_config = config_manager.get_data_config()
    source_json_dir = Path(data_config['source_dir'])
    
    # 获取数据库配置
    db_config = config_manager.get_database_config()
    db_paths = db_config.get('db_paths', {})
    
    # 获取所有子文件夹
    subfolders = [f for f in source_json_dir.iterdir() if f.is_dir()]
    
    results = {}
    
    for folder in subfolders:
        folder_name = folder.name
        
        # 如果该文件夹在数据库配置中，则使用配置的数据库路径
        if folder_name in db_paths:
            db_path = db_paths[folder_name]
        else:
            # 否则使用默认路径格式 data/{folder_name}.db
            db_path = f"data/{folder_name}.db"
        
        # 临时保存原始source_dir配置
        original_source_dir = config_manager.get_data_config()['source_dir']
        
        # 临时修改配置管理器中的source_dir为当前子文件夹
        config_manager.config.set('Data', 'source_dir', str(folder))
        
        try:
            # 创建DataManager实例，使用folder_name作为数据库名称
            # DataManager构造函数会自动使用更新后的source_dir配置
            manager = DataManager(db_name=folder_name)
            
            # 初始化数据（DataManager构造函数已经调用了_init_database）
            result = manager.initialize_database_from_json(clear_existing=clear_existing)
            results[folder_name] = result
        finally:
            # 恢复原始source_dir配置
            config_manager.config.set('Data', 'source_dir', original_source_dir)
        
    return results


# 全局数据库初始化器实例
db_initializer = None


def get_db_initializer() -> DatabaseInitializer:
    """获取数据库初始化器实例"""
    global db_initializer
    if db_initializer is None:
        db_initializer = DatabaseInitializer()
    return db_initializer