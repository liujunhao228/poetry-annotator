"""
分离数据库管理模块
负责管理原始数据、标注数据和情感分类数据的分离存储
支持为每个主数据库创建独立的分离数据库
"""

import sqlite3
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone, timedelta
from .db_config_manager import get_separate_database_paths, ensure_database_directory_exists
from .adapter import get_database_adapter
from .exceptions import DatabaseError


class SeparateDatabaseManager:
    """分离数据库管理器，负责管理原始数据、标注数据和情感分类数据的分离存储"""

    def __init__(self, main_db_name: str = "default"):
        self.logger = logging.getLogger(__name__)
        self.main_db_name = main_db_name
        self.db_configs = self._get_database_configs()
        
        # 初始化各个数据库适配器
        self.raw_data_db = get_database_adapter('sqlite', self.db_configs['raw_data'])
        self.annotation_db = get_database_adapter('sqlite', self.db_configs['annotation'])
        self.emotion_db = get_database_adapter('sqlite', self.db_configs['emotion'])
        
    def _get_database_configs(self) -> Dict[str, str]:
        """获取分离数据库配置，支持为每个主数据库创建独立的分离数据库"""
        # 使用统一的配置管理获取分离数据库路径
        separate_paths = get_separate_database_paths(self.main_db_name)
        
        # 确保数据库目录存在
        for path in separate_paths.values():
            ensure_database_directory_exists(path)
            
        return separate_paths
    
    def initialize_all_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化所有分离的数据库"""
        results = {}
        
        # 初始化原始数据数据库
        try:
            self.logger.info(f"开始初始化原始数据数据库 ({self.db_configs['raw_data']})")
            result = self._initialize_raw_data_database(clear_existing)
            results['raw_data'] = result
            self.logger.info("原始数据数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化原始数据数据库失败: {e}")
            results['raw_data'] = {"error": str(e)}
            
        # 初始化标注数据数据库
        try:
            self.logger.info(f"开始初始化标注数据数据库 ({self.db_configs['annotation']})")
            result = self._initialize_annotation_database(clear_existing)
            results['annotation'] = result
            self.logger.info("标注数据数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化标注数据数据库失败: {e}")
            results['annotation'] = {"error": str(e)}
            
        # 初始化情感分类数据库
        try:
            self.logger.info(f"开始初始化情感分类数据库 ({self.db_configs['emotion']})")
            result = self._initialize_emotion_database(clear_existing)
            results['emotion'] = result
            self.logger.info("情感分类数据库初始化完成")
        except Exception as e:
            self.logger.error(f"初始化情感分类数据库失败: {e}")
            results['emotion'] = {"error": str(e)}
            
        return results
    
    def _initialize_raw_data_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化原始数据数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['raw_data'])
        
        # 初始化数据库表结构（仅初始化原始数据相关表）
        self.raw_data_db.init_raw_data_database()
        
        # 如果需要清空现有数据
        if clear_existing:
            self.raw_data_db.execute_update("DELETE FROM poems")
            self.raw_data_db.execute_update("DELETE FROM authors")
        
        return {
            "status": "success",
            "message": f"原始数据数据库初始化完成"
        }
    
    def _initialize_annotation_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化标注数据数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['annotation'])
        
        # 初始化数据库表结构（仅初始化标注数据相关表）
        self.annotation_db.init_annotation_database()
        
        # 如果需要清空现有数据
        if clear_existing:
            self.annotation_db.execute_update("DELETE FROM annotations")
            self.annotation_db.execute_update("DELETE FROM sentence_annotations")
            self.annotation_db.execute_update("DELETE FROM sentence_emotion_links")
        
        return {
            "status": "success",
            "message": f"标注数据数据库初始化完成"
        }
    
    def _initialize_emotion_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化情感分类数据库"""
        # 确保数据库目录存在
        ensure_database_directory_exists(self.db_configs['emotion'])
        
        # 初始化数据库表结构（仅初始化情感分类相关表）
        self.emotion_db.init_emotion_database()
        
        # 如果需要清空现有数据
        if clear_existing:
            self.emotion_db.execute_update("DELETE FROM emotion_categories")
        
        # 情感分类体系导入现在由插件处理，这里不再直接导入
        
        return {
            "status": "success",
            "message": f"情感分类数据库初始化完成"
        }
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据库的统计信息"""
        stats = {}
        
        # 统计原始数据数据库
        try:
            if not Path(self.db_configs['raw_data']).exists():
                stats['raw_data'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['poems', 'authors']
                
                for table in tables:
                    try:
                        rows = self.raw_data_db.execute_query(f"SELECT COUNT(*) FROM {table}")
                        tables_stats[table] = rows[0][0] if rows else 0
                    except Exception:
                        tables_stats[table] = "N/A"
                
                stats['raw_data'] = {
                    "status": "ok",
                    "path": self.db_configs['raw_data'],
                    "tables": tables_stats
                }
        except Exception as e:
            stats['raw_data'] = {
                "status": "error",
                "message": str(e)
            }
            
        # 统计标注数据数据库
        try:
            if not Path(self.db_configs['annotation']).exists():
                stats['annotation'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['annotations', 'sentence_annotations', 'sentence_emotion_links']
                
                for table in tables:
                    try:
                        rows = self.annotation_db.execute_query(f"SELECT COUNT(*) FROM {table}")
                        tables_stats[table] = rows[0][0] if rows else 0
                    except Exception:
                        tables_stats[table] = "N/A"
                
                stats['annotation'] = {
                    "status": "ok",
                    "path": self.db_configs['annotation'],
                    "tables": tables_stats
                }
        except Exception as e:
            stats['annotation'] = {
                "status": "error",
                "message": str(e)
            }
            
        # 统计情感分类数据库
        try:
            if not Path(self.db_configs['emotion']).exists():
                stats['emotion'] = {
                    "status": "missing",
                    "message": "数据库文件不存在"
                }
            else:
                # 获取表统计信息
                tables_stats = {}
                tables = ['emotion_categories']
                
                for table in tables:
                    try:
                        rows = self.emotion_db.execute_query(f"SELECT COUNT(*) FROM {table}")
                        tables_stats[table] = rows[0][0] if rows else 0
                    except Exception:
                        tables_stats[table] = "N/A"
                
                stats['emotion'] = {
                    "status": "ok",
                    "path": self.db_configs['emotion'],
                    "tables": tables_stats
                }
        except Exception as e:
            stats['emotion'] = {
                "status": "error",
                "message": str(e)
            }
            
        return stats

# 全局分离数据库管理器实例，按主数据库名称存储
separate_db_managers = {}
# 锁对象，确保线程安全
import threading
_separate_db_managers_lock = threading.Lock()


def get_separate_db_manager(main_db_name: str = "default") -> SeparateDatabaseManager:
    """获取分离数据库管理器实例，支持为不同主数据库创建独立实例"""
    global separate_db_managers, _separate_db_managers_lock
    
    # 使用双重检查锁定确保线程安全
    if main_db_name not in separate_db_managers:
        with _separate_db_managers_lock:
            # 再次检查，防止重复创建
            if main_db_name not in separate_db_managers:
                separate_db_managers[main_db_name] = SeparateDatabaseManager(main_db_name=main_db_name)
    
    return separate_db_managers[main_db_name]