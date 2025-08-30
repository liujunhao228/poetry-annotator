#!/usr/bin/env python3
"""
数据库初始化脚本
提供更清晰的数据库初始化流程
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db_initializer import get_db_initializer
from src.db_initializer.functions import initialize_all_databases_from_source_folders


def init_database(clear_existing: bool = False):
    \"\"\"初始化数据库\"\"\"
    print("开始初始化数据库...")
    
    # 获取数据库初始化器
    db_initializer = get_db_initializer()
    
    # 1. 初始化分离的数据库结构
    print("\n1. 初始化分离的数据库结构...")
    separate_results = db_initializer.initialize_separate_databases(clear_existing)
    
    print("\n分离数据库初始化结果:")
    for db_name, db_results in separate_results.items():
        print(f"  {db_name}:")
        for sub_db_name, result in db_results.items():
            status = result.get('status', 'unknown') if isinstance(result, dict) else 'unknown'
            message = result.get('message', '') if isinstance(result, dict) else str(result)
            print(f"    {sub_db_name}: {status} - {message}")
    
    # 2. 导入数据
    print("\n2. 开始导入数据...")
    import_results = initialize_all_databases_from_source_folders(clear_existing)
    
    print("\n数据导入结果:")
    for db_name, result in import_results.items():
        if 'error' in result:
            print(f"  {db_name}: 错误 - {result['error']}")
        else:
            print(f"  {db_name}: authors={result.get('authors', 0)}, poems={result.get('poems', 0)}")
    
    # 3. 显示数据库统计信息
    print("\n3. 数据库统计信息:")
    stats = db_initializer.get_database_stats()
    for db_name, stat in stats.items():
        print(f"  {db_name} 对应的分离数据库:")
        if isinstance(stat, dict):
            for sub_db_name, sub_stat in stat.items():
                print(f"    {sub_db_name}:")
                status = sub_stat.get('status', 'unknown') if isinstance(sub_stat, dict) else 'unknown'
                print(f"      状态: {status}")
                if status == 'ok' and isinstance(sub_stat, dict):
                    print(f"      路径: {sub_stat.get('path', 'N/A')}")
                    tables = sub_stat.get('tables', {})
                    for table, count in tables.items():
                        print(f"      {table}: {count} 条记录")
                elif isinstance(sub_stat, dict):
                    print(f"      信息: {sub_stat.get('message', 'N/A')}")
        else:
            print(f"    信息: {str(stat)}")
    
    print("\n数据库初始化完成!")


if __name__ == "__main__":
    # 解析命令行参数
    clear_existing = False
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_existing = True
        print("注意: 将清空现有数据!")
    
    init_database(clear_existing)