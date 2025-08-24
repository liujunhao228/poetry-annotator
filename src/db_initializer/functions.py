"""
数据库初始化功能函数
从src/data/initializer.py迁移过来的函数
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
    from src.config import config_manager


def initialize_all_databases_from_source_folders(clear_existing: bool = False) -> Dict[str, Dict[str, int]]:
    """根据项目配置初始化数据库"""
    # 延期导入以避免循环依赖
    from src.data.manager import DataManager
    
    # 获取数据配置
    data_config = config_manager.get_effective_data_config()
    source_dir = data_config['source_dir']
    source_json_dir = Path(source_dir)
    
    # 获取数据库配置
    db_config = config_manager.get_effective_database_config()
    separate_db_paths = db_config.get('separate_db_paths', {})
    
    # 确定数据库名称
    # 从source_dir路径中提取数据库名称（例如：data/source_json/TangShi -> TangShi）
    db_name = source_json_dir.name if source_json_dir.exists() else "default"
    
    results = {}
    
    try:
        # 创建DataManager实例，使用从路径中提取的数据库名称
        manager = DataManager(db_name=db_name)
        
        # 确保manager的source_dir属性指向正确的源数据目录
        manager.source_dir = str(source_json_dir)
        
        # 初始化数据
        result = manager.initialize_database_from_json(clear_existing=clear_existing)
        results[db_name] = result
    except Exception as e:
        db_name = db_name if 'db_name' in locals() else "default"
        print(f"处理数据库 {db_name} 时出错: {e}")
        results[db_name] = {"error": str(e)}
        
    return results