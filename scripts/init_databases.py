#!/usr/bin/env python3
"""
数据库初始化工具
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db_initializer import get_db_initializer

def main():
    print("开始初始化数据库...")
    db_initializer = get_db_initializer()
    results = db_initializer.initialize_all_databases()
    
    print("\n数据库初始化结果:")
    for db_name, result in results.items():
        print(f"  {db_name}: {result.get('status', 'unknown')} - {result.get('message', '')}")
        
    print("\n数据库统计信息:")
    stats = db_initializer.get_database_stats()
    for db_name, stat in stats.items():
        print(f"  {db_name}:")
        print(f"    状态: {stat.get('status', 'unknown')}")
        if stat.get('status') == 'ok':
            print(f"    路径: {stat.get('path', 'N/A')}")
            tables = stat.get('tables', {})
            for table, count in tables.items():
                print(f"    {table}: {count} 条记录")
        else:
            print(f"    信息: {stat.get('message', 'N/A')}")

if __name__ == '__main__':
    main()