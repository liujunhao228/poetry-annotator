#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# 设置环境变量以避免相对导入问题
os.environ['PYTHONPATH'] = str(Path(__file__).parent / 'src')

from src.data_manager import DataManager

def main():
    """初始化数据库"""
    print("=== 诗词情感标注工具 - 数据库初始化 ===")
    
    # 创建数据管理器实例
    dm = DataManager()
    
    try:
        # 初始化数据库（清空现有数据）
        print("\n开始从JSON文件初始化数据库...")
        result = dm.initialize_database_from_json(clear_existing=True)
        
        print(f"\n初始化完成!")
        print(f"- 作者数量: {result['authors']}")
        print(f"- 诗词数量: {result['poems']}")
        
        # 显示统计信息
        print("\n数据库统计信息:")
        stats = dm.get_statistics()
        print(f"- 总诗词数: {stats['total']}")
        print(f"- 状态分布: {stats['status_counts']}")
        print(f"- 前10位作者: {stats['top_authors']}")
        
        print("\n数据库初始化成功! 现在可以开始标注任务了。")
        
    except Exception as e:
        print(f"\n错误: {e}")
        print("请检查:")
        print("1. 配置文件 config/config.ini 是否正确")
        print("2. JSON文件是否在 data/source_json/ 目录中")
        print("3. 数据源目录是否存在")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 