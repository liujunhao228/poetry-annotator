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
from .adapter import get_database_adapter
from .exceptions import DatabaseError
from ..config import config_manager


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
        db_config = config_manager.get_effective_database_config()
        
        # 默认路径配置，使用主数据库名称作为前缀
        default_paths = {
            'raw_data': f'data/{self.main_db_name}/raw_data.db',
            'annotation': f'data/{self.main_db_name}/annotation.db',
            'emotion': f'data/{self.main_db_name}/emotion.db'
        }
        
        # 处理新的分离数据库配置
        if 'separate_db_paths' in db_config:
            separate_paths = db_config['separate_db_paths']
            # 确保使用绝对路径，并替换主数据库名称占位符
            resolved_paths = {}
            for name, path in separate_paths.items():
                # 支持使用 {main_db_name} 占位符
                path = path.replace('{main_db_name}', self.main_db_name)
                if not Path(path).is_absolute():
                    resolved_paths[name] = str(Path(path).resolve())
                else:
                    resolved_paths[name] = path
            # 合并默认路径和配置路径
            return {**default_paths, **resolved_paths}
        else:
            # 如果没有配置分离数据库，则使用默认路径
            return {
                'raw_data': str(Path(default_paths['raw_data']).resolve()),
                'annotation': str(Path(default_paths['annotation']).resolve()),
                'emotion': str(Path(default_paths['emotion']).resolve())
            }
    
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
        db_path_obj = Path(self.db_configs['raw_data'])
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
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
        db_path_obj = Path(self.db_configs['annotation'])
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
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
        db_path_obj = Path(self.db_configs['emotion'])
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表结构（仅初始化情感分类相关表）
        self.emotion_db.init_emotion_database()
        
        # 如果需要清空现有数据
        if clear_existing:
            self.emotion_db.execute_update("DELETE FROM emotion_categories")
        
        # 导入情感分类体系
        imported_count = 0
        try:
            from ..label_parser import get_label_parser
            label_parser = get_label_parser()
            # 获取所有分类的详细信息，包括英文名称
            categories_data = []
            for primary_id, primary_data in label_parser.categories.items():
                # 添加一级分类
                categories_data.append({
                    'id': primary_data['id'],
                    'name_zh': primary_data['name_zh'],
                    'name_en': primary_data.get('name_en', ''),
                    'parent_id': None,
                    'level': 1
                })
                # 添加二级分类
                for secondary in primary_data.get('secondaries', []):
                    categories_data.append({
                        'id': secondary['id'],
                        'name_zh': secondary['name_zh'],
                        'name_en': secondary.get('name_en', ''),
                        'parent_id': primary_data['id'],
                        'level': 2
                    })
            
            # 使用批量插入和事务优化性能
            if categories_data:
                conn = self.emotion_db.connect()
                try:
                    # 开启事务
                    conn.execute('BEGIN TRANSACTION')
                    
                    # 准备批量插入数据
                    insert_data = [
                        (
                            category['id'],
                            category['name_zh'],
                            category['name_en'],
                            category['parent_id'],
                            category['level']
                        )
                        for category in categories_data
                    ]
                    
                    # 执行批量插入
                    conn.executemany('''
                        INSERT OR REPLACE INTO emotion_categories 
                        (id, name_zh, name_en, parent_id, level)
                        VALUES (?, ?, ?, ?, ?)
                    ''', insert_data)
                    
                    # 提交事务
                    conn.commit()
                    imported_count = len(categories_data)
                    self.logger.info(f"向情感分类数据库批量导入了 {imported_count} 个情感分类")
                    
                except Exception as e:
                    # 回滚事务
                    conn.rollback()
                    self.logger.error(f"批量导入情感分类时出错，已回滚事务: {e}")
                    raise
                finally:
                    conn.close()
                    
        except Exception as e:
            self.logger.error(f"向情感分类数据库导入情感分类时出错: {e}")
        
        return {
            "status": "success",
            "message": f"情感分类数据库初始化完成，导入了 {imported_count} 个情感分类"
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


def get_separate_db_manager(main_db_name: str = "default") -> SeparateDatabaseManager:
    """获取分离数据库管理器实例，支持为不同主数据库创建独立实例"""
    global separate_db_managers
    if main_db_name not in separate_db_managers:
        separate_db_managers[main_db_name] = SeparateDatabaseManager(main_db_name=main_db_name)
    return separate_db_managers[main_db_name]