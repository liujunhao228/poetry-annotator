import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.db_config_manager import get_separate_database_paths

# 检查数据库结构
def check_db_structure():
    # 获取数据库路径（使用默认项目）
    db_paths = get_separate_database_paths("data/SocialPoemAnalysis")
    
    print("数据库路径:")
    for db_type, path in db_paths.items():
        print(f"  {db_type}: {path}")
        if Path(path).exists():
            print(f"    文件存在: 是")
        else:
            print(f"    文件存在: 否")
    
    # 检查annotation数据库中的表结构
    annotation_db_path = db_paths['annotation']
    if Path(annotation_db_path).exists():
        print(f"\n检查标注数据库 ({annotation_db_path}) 表结构:")
        
        conn = sqlite3.connect(annotation_db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f" 表列表: {[table[0] for table in tables]}")
        
        # 检查annotations表的结构
        if ('annotations',) in tables:
            print(f"\n  annotations 表结构:")
            cursor.execute("PRAGMA table_info(annotations);")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
        
        # 检查sentence_annotations表的结构
        if ('sentence_annotations',) in tables:
            print(f"\n  sentence_annotations 表结构:")
            cursor.execute("PRAGMA table_info(sentence_annotations);")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
        
        conn.close()
    else:
        print(f"\n标注数据库文件不存在: {annotation_db_path}")

if __name__ == "__main__":
    check_db_structure()
