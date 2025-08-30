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
    from src.config import get_config_manager
    config_manager = get_config_manager()
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from config import get_config_manager
    config_manager = get_config_manager()

# 移除了对数据库适配器的导入

try:
    from src.plugin_label_parser import get_plugin_label_parser
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from plugin_label_parser import get_plugin_label_parser

try:
    from src.db_initializer.plugin_interface import DatabaseInitPluginManager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent))
    from plugin_interface import DatabaseInitPluginManager

from src.data.exceptions import DatabaseError


class DatabaseInitializer:
    """数据库初始化器，负责初始化和管理分离数据库"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 初始化插件管理器
        self.plugin_manager = DatabaseInitPluginManager(config_manager)
        # 分离数据库管理器将在初始化时设置
        self.separate_db_manager = None
        
    def initialize_separate_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化分离的数据库结构"""
        results = {}
        
        # 获取数据配置
        data_config = config_manager.get_effective_data_config()
        source_dir = data_config.get('source_dir')
        output_dir = data_config.get('output_dir')
        
        # 获取数据库配置
        db_config = config_manager.get_effective_database_config()
        separate_db_paths = db_config.get('separate_db_paths', {})
        
        # 从output_dir路径中提取数据库名称
        import os
        db_name = os.path.basename(output_dir) if output_dir else "default"
        
        from ..data.separate_databases import get_separate_db_manager
        
        # 获取分离数据库管理器
        separate_db_manager = get_separate_db_manager()
        
        # 设置分离数据库管理器到插件管理器
        self.separate_db_manager = separate_db_manager
        self.plugin_manager.set_separate_db_manager(separate_db_manager)
        # 加载插件
        self.plugin_manager.load_plugins_from_config()
        
        # 初始化分离数据库
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
            # 在调用插件之前，更新插件配置以包含源数据路径和数据库路径
            for plugin_name, plugin in self.plugin_manager.plugins.items():
                # 更新插件配置中的源数据路径和数据库路径
                if hasattr(plugin, 'source_dir') and not plugin.source_dir:
                    plugin.source_dir = source_dir
                if hasattr(plugin, 'db_paths') and not plugin.db_paths:
                    plugin.db_paths = separate_db_paths
            
            plugin_results = self.plugin_manager.initialize_plugins(db_name, clear_existing)
            # 将插件初始化结果添加到结果中
            if 'plugins' not in db_results:
                db_results['plugins'] = {}
            db_results['plugins'].update(plugin_results)
        except Exception as e:
            self.logger.error(f"为数据库 {db_name} 初始化插件时出错: {e}")
            if 'plugins' not in db_results:
                db_results['plugins'] = {"status": "error", "message": str(e)}
        
        return results
    
    def _ensure_emotion_categories_imported(self, separate_db_manager) -> Dict[str, Any]:
        """确保情感分类数据已正确导入到分离的情感数据库中"""
        # 情感分类数据导入现在由插件处理，这里直接返回成功状态
        return {
            "status": "success",
            "message": "情感分类数据库初始化完成（数据导入由插件处理）"
        }
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取分离数据库的统计信息"""
        stats = {}
        
        try:
            # 获取数据配置以确定数据库名称
            data_config = config_manager.get_effective_data_config()
            output_dir = data_config.get('output_dir', '')
            
            # 从output_dir路径中提取数据库名称
            import os
            db_name = os.path.basename(output_dir) if output_dir else "default"
            
            from ..data.separate_databases import get_separate_db_manager
            # 获取分离数据库管理器
            separate_db_manager = get_separate_db_manager()
            
            # 获取分离数据库统计信息
            separate_stats = separate_db_manager.get_database_stats()
            stats[db_name] = separate_stats
        except Exception as e:
            # 获取数据配置以确定数据库名称
            data_config = config_manager.get_effective_data_config()
            output_dir = data_config.get('output_dir', '')
            
            # 从output_dir路径中提取数据库名称
            import os
            db_name = os.path.basename(output_dir) if output_dir else "default"
            
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