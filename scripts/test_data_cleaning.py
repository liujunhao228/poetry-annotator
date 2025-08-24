#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据清洗模块测试脚本
用于测试新实现的数据清洗模块功能
"""

import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_cleaning import DataCleaningManager


def test_data_cleaning_module():
    """测试数据清洗模块"""
    print("开始测试数据清洗模块...")
    
    # 初始化清洗管理器
    global_config_path = os.path.join(project_root, "config", "global", "global_cleaning_rules.yaml")
    
    try:
        cleaning_manager = DataCleaningManager(global_config_path)
        print("✓ 成功初始化清洗管理器")
        
        # 测试获取规则
        rules = cleaning_manager.rule_manager.get_rules()
        print(f"✓ 成功加载 {len(rules)} 条规则")
        
        # 测试获取全局设置
        global_settings = cleaning_manager.rule_manager.get_global_settings()
        print(f"✓ 成功加载全局设置: {global_settings}")
        
        print("数据清洗模块测试完成!")
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False


if __name__ == "__main__":
    success = test_data_cleaning_module()
    sys.exit(0 if success else 1)