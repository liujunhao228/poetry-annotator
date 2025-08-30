"""
数据库初始化功能函数
使用新的统一插件系统
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
    from src.component_system import get_component_system, ComponentType
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from src.config import config_manager
    from src.component_system import get_component_system, ComponentType


def initialize_all_databases_from_source_folders(clear_existing: bool = False) -> Dict[str, Dict[str, int]]:
    """根据项目配置初始化数据库"""
    # 获取数据配置
    data_config = config_manager.get_effective_data_config()
    source_dir = data_config['source_dir']
    source_json_dir = Path(source_dir)
    
    # 获取数据库配置
    db_config = config_manager.get_effective_database_config()
    separate_db_paths = db_config.get('separate_db_paths', {})
    
    # 确定源数据名称（用于显示导入结果）
    # 从source_dir路径中提取源数据名称（例如：data/source_json/TangShi -> TangShi）
    source_name = source_json_dir.name if source_json_dir.exists() else "default"
    
    results = {}
    
    try:
        # 获取组件系统并创建统一插件实例
        component_system = get_component_system(project_root)
        social_poem_plugin = component_system.get_component(
            ComponentType.DATA_STORAGE, db_name=source_name
        )
        
        # 使用插件加载数据
        authors = social_poem_plugin.load_author_data(source_dir)
        poems = social_poem_plugin.load_all_json_files(source_dir)
        
        # 使用插件保存数据
        author_count = social_poem_plugin.batch_insert_authors(authors) if authors else 0
        poem_count = social_poem_plugin.batch_insert_poems(poems, start_id=1) if poems else 0
        
        results[source_name] = {
            'authors': author_count,
            'poems': poem_count
        }
    except Exception as e:
        source_name = source_name if 'source_name' in locals() else "default"
        print(f"处理源数据 {source_name} 时出错: {e}")
        results[source_name] = {"error": str(e)}
        
    return results