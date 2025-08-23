#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 ProjectSystem 的基本功能
"""

import sys
import os

# 将项目根目录添加到 sys.path，以便能够导入 src 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from src.project_system import ProjectSystem

# 配置根日志记录器
logging.basicConfig(
    level=logging.DEBUG,  # 设置为 DEBUG 以查看详细日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 为项目系统模块设置日志级别
logging.getLogger('src.project_system').setLevel(logging.DEBUG)

async def main():
    print("--- 测试 ProjectSystem 初始化和插件加载 ---")
    try:
        # 创建 ProjectSystem 实例，这会触发插件配置的加载
        ps = ProjectSystem()
        print("ProjectSystem 实例创建成功。")
        
        # 尝试获取一个默认的 Annotator 组件（因为没有启用相关插件）
        print("\n--- 测试获取默认 Annotator 组件 ---")
        # 注意：这会因为缺少 model_config_name 而失败，这是预期的
        try:
            annotator = ps.get_component("annotator")
        except ValueError as e:
            print(f"按预期捕获到 ValueError (缺少 model_config_name): {e}")
        
        # 尝试获取一个默认的 DataManager 组件
        print("\n--- 测试获取默认 DataManager 组件 ---")
        try:
            data_manager = ps.get_component("data_manager")
            print(f"成功获取默认 DataManager 实例: {type(data_manager)}")
        except Exception as e:
            print(f"获取默认 DataManager 失败: {e}")

        # 尝试获取一个不存在的组件类型
        print("\n--- 测试获取不存在的组件类型 ---")
        try:
            unknown_component = ps.get_component("unknown_component")
        except ValueError as e:
            print(f"按预期捕获到 ValueError (未知组件类型): {e}")
            
    except Exception as e:
        print(f"测试过程中发生未预期的错误: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())