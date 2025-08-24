"""
数据库初始化脚本

注意：这是一个独立的数据库初始化脚本，不使用项目的配置系统。
它直接通过SQL文件初始化数据库，主要用于手动初始化或备份用途。
与src/db_initializer模块不同，不应在正常项目运行中使用。
"""
import sqlite3
import os

def initialize_database(db_path: str, schema_file: str, init_files: list):
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        schema_file: 表结构定义SQL文件路径
        init_files: 初始化数据SQL文件路径列表
    """
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 执行表结构定义脚本
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    # 执行初始化数据脚本
    for init_file in init_files:
        with open(init_file, 'r', encoding='utf-8') as f:
            init_sql = f.read()
            cursor.executescript(init_sql)
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    print(f"数据库 {db_path} 初始化完成")


if __name__ == "__main__":
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 定义数据库路径
    db_path = os.path.join(project_root, "data", "poetry.db")
    
    # 定义SQL文件路径
    schema_file = os.path.join(project_root, "src", "data", "sql", "schema.sql")
    emotion_init_file = os.path.join(project_root, "src", "data", "sql", "init_emotion_categories.sql")
    strategy_init_file = os.path.join(project_root, "src", "data", "sql", "init_strategy_categories.sql")
    
    # 初始化数据库
    initialize_database(db_path, schema_file, [emotion_init_file, strategy_init_file])