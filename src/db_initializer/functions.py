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

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.config import config_manager
    from src.data.manager import get_data_manager
except ImportError:
    # 当作为独立模块运行时
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from src.config import config_manager
    from src.data.manager import get_data_manager


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
        # 获取数据管理器实例
        data_manager = get_data_manager(db_name=source_name)
        
        # 使用数据管理器加载和保存数据
        authors = data_manager.load_author_data(source_dir)
        poems = data_manager.load_all_json_files()
        
        author_count = data_manager.batch_insert_authors(authors) if authors else 0
        logger.info(f"从源 '{source_name}' 成功插入 {author_count} 位作者。")
        poem_count = data_manager.batch_insert_poems(poems, start_id=1) if poems else 0
        logger.info(f"从源 '{source_name}' 成功插入 {poem_count} 首诗词。")
        
        results[source_name] = {
            'authors': author_count,
            'poems': poem_count
        }
    except Exception as e:
        source_name = source_name if 'source_name' in locals() else "default"
        print(f"处理源数据 {source_name} 时出错: {e}")
        results[source_name] = {"error": str(e)}
        
    return results
