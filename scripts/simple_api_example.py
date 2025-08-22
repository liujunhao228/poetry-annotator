"""
为scripts/目录下的脚本提供简单、统一的配置与数据封装API使用示例
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入简单的配置和数据API
from scripts.simple_config_api import simple_config_api
from scripts.simple_data_api import simple_data_api


def main():
    """主函数，演示API的使用方法"""
    print("=== 简单配置与数据API使用示例 ===")
    
    # 1. 配置获取示例
    print("\n1. 配置获取示例:")
    
    # 获取数据库配置
    db_config = simple_config_api.get_database_config()
    print(f"数据库配置: {db_config}")
    
    # 获取数据路径配置
    data_config = simple_config_api.get_data_config()
    print(f"数据路径配置: {data_config}")
    
    # 获取日志配置
    logging_config = simple_config_api.get_logging_config()
    print(f"日志配置: {logging_config}")
    
    # 获取模型配置
    model_configs = simple_config_api.get_model_configs()
    print(f"模型配置数量: {len(model_configs)}")
    if model_configs:
        print(f"第一个模型配置: {model_configs[0]}")
    
    # 获取当前激活的项目配置
    active_project = simple_config_api.get_active_project_config()
    print(f"当前激活的项目配置: {active_project}")
    
    # 2. 数据访问示例
    print("\n2. 数据访问示例:")
    
    # 获取数据管理器
    data_manager = simple_data_api.get_data_manager()
    print(f"数据管理器数据库名称: {data_manager.db_name}")
    
    # 获取数据库统计信息
    try:
        stats = simple_data_api.get_statistics()
        print(f"数据库统计信息: {stats}")
    except Exception as e:
        print(f"获取数据库统计信息时出错: {e}")
    
    # 获取标注统计信息
    try:
        annotation_stats = simple_data_api.get_annotation_statistics()
        print(f"标注统计信息: {annotation_stats}")
    except Exception as e:
        print(f"获取标注统计信息时出错: {e}")
    
    print("\n=== 示例结束 ===")


if __name__ == "__main__":
    main()