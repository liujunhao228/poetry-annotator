import sqlite3
import pandas as pd
from datetime import datetime
import pytz
from pathlib import Path

# 测试 Path 是否可用
test_path = Path('.')

# 从主项目导入日志配置系统
try:
    from src.logging_config import get_logger, setup_default_logging
    # 初始化日志系统，使用主项目的配置
    setup_default_logging()
    logger = get_logger(__name__)
except ImportError:
    # 如果无法导入主项目的日志配置，则使用默认配置
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

def db_connect(db_path):
    """建立数据库连接，并进行性能优化设置."""
    conn = sqlite3.connect(db_path)
    # 启用 WAL 模式，提高并发读取性能，减少写锁定
    conn.execute("PRAGMA journal_mode = WAL;")
    # 降低同步级别，在数据安全性要求不太高时提升写入速度
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def get_current_time_iso_utc():
    """获取当前UTC时间的ISO格式字符串."""
    return datetime.now(pytz.utc).isoformat()
