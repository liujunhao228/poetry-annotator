"""
数据库初始化器模块
"""
import sys
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
    from src.emotion_classification.manager import get_emotion_classification_manager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from emotion_classification.manager import get_emotion_classification_manager

try:
    from src.db_initializer.plugin_interface import DatabaseInitPluginManager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent))
    from plugin_interface import DatabaseInitPluginManager

from src.data.exceptions import DatabaseError
from src.data.db_config_manager import get_separate_database_paths, extract_project_name_from_output_dir
from src.data.separate_databases import SeparateDatabaseManager
from src.config.project_config_loader import ProjectConfigLoader # Import ProjectConfigLoader
from src.config.schema import ProjectConfig # Import ProjectConfig


class DatabaseInitializer:
    """数据库初始化器，负责初始化和管理分离数据库"""
    
    def __init__(self, output_dir: str, source_dir: str):
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.source_dir = source_dir
        self.project_name = extract_project_name_from_output_dir(output_dir) if output_dir else "default"
        
        # 初始化插件管理器
        self.plugin_manager = DatabaseInitPluginManager(config_manager)
        # 分离数据库管理器将在初始化时设置
        self.separate_db_manager = None
        
    def initialize_separate_databases(self, clear_existing: bool = False) -> Dict[str, Dict[str, Any]]:
        """初始化分离的数据库结构"""
        results = {}
        
        # 获取分离数据库管理器
        separate_db_manager = SeparateDatabaseManager(self.output_dir)
        
        # 设置分离数据库管理器到插件管理器
        self.separate_db_manager = separate_db_manager
        self.plugin_manager.set_separate_db_manager(separate_db_manager)
        # 加载插件
        self.plugin_manager.load_plugins_from_config()
        
        # 初始化分离数据库
        db_results = separate_db_manager.initialize_all_databases(clear_existing)
        results[self.project_name] = db_results
        
        # 执行插件的数据库初始化
        try:
            # 在调用插件之前，更新插件配置以包含源数据路径和数据库路径
            # 先获取数据库路径
            separate_db_paths = get_separate_database_paths(self.output_dir)
            for plugin_name, plugin in self.plugin_manager.plugins.items():
                # 更新插件配置中的源数据路径和数据库路径
                if hasattr(plugin, 'source_dir') and not plugin.source_dir:
                    plugin.source_dir = self.source_dir
                if hasattr(plugin, 'db_paths') and not plugin.db_paths:
                    plugin.db_paths = separate_db_paths
            
            plugin_results = self.plugin_manager.initialize_plugins(self.project_name, clear_existing)
            # 将插件初始化结果添加到结果中
            if 'plugins' not in db_results:
                db_results['plugins'] = {}
            db_results['plugins'].update(plugin_results)
        except Exception as e:
            self.logger.error(f"为项目 {self.project_name} 初始化插件时出错: {e}")
            if 'plugins' not in db_results:
                db_results['plugins'] = {"status": "error", "message": str(e)}
        
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取分离数据库的统计信息"""
        stats = {}
        
        try:
            # 获取分离数据库管理器
            separate_db_manager = SeparateDatabaseManager(self.output_dir)
            
            # 获取分离数据库统计信息
            separate_stats = separate_db_manager.get_database_stats()
            stats[self.project_name] = separate_stats
        except Exception as e:
            stats[self.project_name] = {
                "status": "error",
                "message": str(e)
            }
            
        return stats


# 全局数据库初始化器实例
db_initializer: Optional[DatabaseInitializer] = None


def get_db_initializer(output_dir: str = None, source_dir: str = None) -> DatabaseInitializer:
    """获取数据库初始化器实例"""
    global db_initializer
    
    # 如果没有提供参数，从配置中获取默认值
    if output_dir is None or source_dir is None:
        # 获取项目配置
        project_config = config_manager.project_config
        if output_dir is None:
            output_dir = project_config.data_path.output_dir or "data/default"
        if source_dir is None:
            source_dir = project_config.data_path.source_dir or "data/source_json"
    
    if db_initializer is None or db_initializer.output_dir != output_dir or db_initializer.source_dir != source_dir:
        db_initializer = DatabaseInitializer(output_dir=output_dir, source_dir=source_dir)
    return db_initializer
