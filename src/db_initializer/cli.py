"""
数据库初始化模块命令行接口
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db_initializer import get_db_initializer


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument(
        "--init-all",
        action="store_true",
        help="初始化所有数据库"
    )
    parser.add_argument(
        "--init-separate",
        action="store_true",
        help="初始化分离数据库"
    )
    parser.add_argument(
        "--migrate-data",
        action="store_true",
        help="迁移数据到分离数据库（已废弃，因为我们已经完全使用分离数据库）"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示数据库统计信息"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="清空现有数据后重新初始化"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    # 获取数据库初始化器实例
    db_initializer = get_db_initializer()
    
    if args.init_all:
        # 初始化所有数据库
        print("开始初始化所有数据库...")
        results = db_initializer.initialize_all_databases(args.clear_existing)
        
        print("\n数据库初始化结果:")
        for db_name, result in results.items():
            print(f"  {db_name}: {result.get('status', 'unknown')} - {result.get('message', '')}")
            
    if args.init_separate:
        # 初始化分离数据库
        print("\n开始初始化分离数据库...")
        # 忽略 migrate_data 参数，因为我们已经完全使用分离数据库
        separate_results = db_initializer.initialize_separate_databases(args.clear_existing, False)
        
        print("\n分离数据库初始化结果:")
        for db_name, db_results in separate_results.items():
            print(f"  {db_name}:")
            for sub_db_name, result in db_results.items():
                status = result.get('status', 'unknown') if isinstance(result, dict) else 'unknown'
                message = result.get('message', '') if isinstance(result, dict) else str(result)
                print(f"    {sub_db_name}: {status} - {message}")
                
    if args.stats:
        # 显示数据库统计信息
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


if __name__ == "__main__":
    main()