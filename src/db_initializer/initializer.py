"""
数据库初始化器模块
"""
import sys
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.config import config_manager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from config import config_manager

try:
    from src.data.adapter import get_database_adapter
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent))
    from data.adapter import get_database_adapter

try:
    from src.label_parser import get_label_parser
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from label_parser import get_label_parser

try:
    from src.db_initializer.plugin_interface import DatabaseInitPluginManager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent))
    from plugin_interface import DatabaseInitPluginManager

from src.data.exceptions import DatabaseError


class DatabaseInitializer:
    """数据库初始化器，负责初始化和管理多数据库"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_configs = self._get_database_configs()
        # 初始化插件管理器
        self.plugin_manager = DatabaseInitPluginManager(config_manager)
        # 分离数据库管理器将在初始化时设置
        self.separate_db_manager = None
        
    def _get_database_configs(self) -> Dict[str, str]:
        """获取所有主数据库配置名称"""
        db_config = config_manager.get_effective_database_config()
        
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
        """初始化单个数据库"""
        # 确保数据库目录存在
        db_path_obj = Path(db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库适配器
        db_adapter = get_database_adapter('sqlite', db_path)
        
        # 初始化数据库表结构
        db_adapter.init_database()
        
        # 导入情感分类体系
        imported_count = 0
        try:
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
                conn = db_adapter.connect()
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
                    self.logger.info(f"向数据库 {db_name} 批量导入了 {imported_count} 个情感分类")
                    
                except Exception as e:
                    # 回滚事务
                    conn.rollback()
                    self.logger.error(f"批量导入情感分类时出错，已回滚事务: {e}")
                    raise
                finally:
                    conn.close()
                    
        except Exception as e:
            self.logger.error(f"向数据库 {db_name} 导入情感分类时出错: {e}")
        
        result = {
            "db_name": db_name,
            "db_path": db_path,
            "status": "success",
            "message": f"数据库 {db_name} 初始化成功，导入了 {imported_count} 个情感分类"
        }
        
        return result
        
    def initialize_separate_databases(self, clear_existing: bool = False, migrate_data: bool = True) -> Dict[str, Dict[str, Any]]:
        """初始化分离的数据库结构，为每个主数据库创建独立的分离数据库"""
        results = {}
        
        # 为每个主数据库创建独立的分离数据库
        for db_name in self.db_configs.keys():
            from ..data.separate_databases import get_separate_db_manager
            
            # 获取针对特定主数据库的分离数据库管理器
            separate_db_manager = get_separate_db_manager(main_db_name=db_name)
            
            # 设置分离数据库管理器到插件管理器
            self.separate_db_manager = separate_db_manager
            self.plugin_manager.set_separate_db_manager(separate_db_manager)
            # 加载插件
            self.plugin_manager.load_plugins_from_config()
            
            # 初始化该主数据库对应的分离数据库
            db_results = separate_db_manager.initialize_all_databases(clear_existing)
            results[db_name] = db_results
            
            # 确保情感分类数据正确导入到分离的情感数据库中
            try:
                emotion_result = self._ensure_emotion_categories_imported(separate_db_manager)
                if 'emotion' in db_results:
                    db_results['emotion'].update(emotion_result)
                else:
                    db_results['emotion'] = emotion_result
            except Exception as e:
                self.logger.error(f"为数据库 {db_name} 导入情感分类数据时出错: {e}")
                if 'emotion' not in db_results:
                    db_results['emotion'] = {"status": "error", "message": str(e)}
            
            # 执行插件的数据库初始化
            try:
                plugin_results = self.plugin_manager.initialize_plugins(db_name, clear_existing)
                # 将插件初始化结果添加到结果中
                if 'plugins' not in db_results:
                    db_results['plugins'] = {}
                db_results['plugins'].update(plugin_results)
            except Exception as e:
                self.logger.error(f"为数据库 {db_name} 初始化插件时出错: {e}")
                if 'plugins' not in db_results:
                    db_results['plugins'] = {"status": "error", "message": str(e)}
            
            # 如果需要迁移数据，则记录警告信息（因为我们已经完全使用分离数据库）
            if migrate_data:
                self.logger.warning("迁移数据功能已禁用，因为我们已经完全使用分离数据库")
        
        return results
    
    def _ensure_emotion_categories_imported(self, separate_db_manager) -> Dict[str, Any]:
        """确保情感分类数据已正确导入到分离的情感数据库中"""
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
                # 确保数据库连接是打开的
                conn = separate_db_manager.emotion_db.connect()
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
                    # 不要在这里关闭连接，因为其他地方可能还需要使用
                    pass
                    
        except Exception as e:
            self.logger.error(f"向情感分类数据库导入情感分类时出错: {e}")
            raise
            
        return {
            "status": "success",
            "message": f"情感分类数据库初始化完成，导入了 {imported_count} 个情感分类"
        }
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有分离数据库的统计信息"""
        stats = {}
        
        # 为每个主数据库获取分离数据库统计信息
        for db_name in self.db_configs.keys():
            try:
                from ..data.separate_databases import get_separate_db_manager
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


# 全局数据库初始化器实例
db_initializer = None


def get_db_initializer() -> DatabaseInitializer:
    """获取数据库初始化器实例"""
    global db_initializer
    if db_initializer is None:
        db_initializer = DatabaseInitializer()
    return db_initializer