#!/usr/bin/env python3
"""
详细测试重构后的配置管理体系
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.config.manager import config_manager
    from src.config.project_manager import project_config_manager
    
    def test_config_metadata():
        """测试配置元数据"""
        print("=== 测试配置元数据 ===")
        print(f"  - 配置元数据路径: {config_manager.config_metadata_path}")
        print(f"  - 全局配置文件路径: {config_manager.config_metadata.get('global_config_file')}")
        print(f"  - 激活项目配置文件路径: {config_manager.config_metadata.get('active_project_config_file')}")
        
        validation_rules = config_manager.config_metadata.get('validation_rules', {})
        print(f"  - 校验规则全局文件: {validation_rules.get('global_file')}")
        print(f"  - 校验规则项目文件模板: {validation_rules.get('project_files')}")
        
        preprocessing_rules = config_manager.config_metadata.get('preprocessing_rules', {})
        print(f"  - 预处理规则全局文件: {preprocessing_rules.get('global_file')}")
        print(f"  - 预处理规则项目文件模板: {preprocessing_rules.get('project_files')}")
        
        cleaning_rules = config_manager.config_metadata.get('cleaning_rules', {})
        print(f"  - 清洗规则全局文件: {cleaning_rules.get('global_file')}")
        print(f"  - 清洗规则项目文件模板: {cleaning_rules.get('project_files')}")

    def test_global_config():
        """测试全局配置"""
        print("\n=== 测试全局配置 ===")
        print(f"  - 全局配置文件路径: {config_manager.global_config_path}")
        print(f"  - 全局配置文件是否存在: {os.path.exists(config_manager.global_config_path)}")
        
        # 测试一些全局配置项
        llm_config = config_manager.get_llm_config()
        print(f"  - LLM最大工作线程数: {llm_config.get('max_workers')}")
        
        db_config = config_manager.global_loader._get_global_database_config()
        print(f"  - 全局数据库配置: {list(db_config.keys()) if db_config else 'None'}")

    def test_project_config():
        """测试项目配置"""
        print("\n=== 测试项目配置 ===")
        
        # 测试项目配置管理器
        print("  1. 项目配置管理器:")
        active_project = project_config_manager.get_active_project()
        print(f"    - 当前激活的项目: {active_project}")
        available_projects = project_config_manager.get_available_projects()
        print(f"    - 可用项目列表: {available_projects}")
        print(f"    - 配置文件路径: {project_config_manager.config_file}")
        print(f"    - 配置文件是否存在: {os.path.exists(project_config_manager.config_file)}")
        
        # 测试当前项目配置
        print("  2. 当前项目配置:")
        print(f"    - 项目配置文件路径: {config_manager.project_config_path}")
        print(f"    - 项目配置文件是否存在: {os.path.exists(config_manager.project_config_path)}")
        
        if config_manager.project_config:
            # 显示项目配置的一些关键信息
            db_config = config_manager.get_effective_database_config()
            print(f"    - 数据库配置: {db_config}")
            
            models = config_manager.get_effective_model_configs()
            print(f"    - 使用的模型数量: {len(models)}")
            for model in models:
                print(f"      - {model.get('model_name', 'Unknown')}")
            
            print(f"    - 校验规则集名称: {config_manager.get_effective_validation_ruleset_name()}")
            print(f"    - 预处理规则集名称: {config_manager.get_effective_preprocessing_ruleset_name()}")
            print(f"    - 清洗规则集名称: {config_manager.get_effective_cleaning_ruleset_name()}")

    def test_project_switching():
        """测试项目切换"""
        print("\n=== 测试项目切换 ===")
        
        original_project = project_config_manager.get_active_project()
        print(f"  - 初始激活项目: {original_project}")
        
        # 获取所有可用项目
        available_projects = project_config_manager.get_available_projects()
        print(f"  - 可用项目: {available_projects}")
        
        # 尝试切换到每个项目
        for project in available_projects:
            if project != original_project:
                print(f"  - 切换到项目: {project}")
                success = config_manager.switch_project_config(project)
                if success:
                    new_active = project_config_manager.get_active_project()
                    print(f"    ✓ 切换成功，当前激活项目: {new_active}")
                    # 显示项目配置信息
                    db_config = config_manager.get_effective_database_config()
                    models = config_manager.get_effective_model_configs()
                    print(f"    - 数据库配置: {list(db_config.keys()) if db_config else 'None'}")
                    print(f"    - 使用模型数量: {len(models)}")
                else:
                    print(f"    ✗ 切换失败")
                    
                # 切换回原项目
                print(f"  - 切换回原项目: {original_project}")
                config_manager.switch_project_config(original_project)
                break  # 只测试一个项目切换

    def test_rules_loading():
        """测试规则加载"""
        print("\n=== 测试规则加载 ===")
        
        # 测试校验规则
        validation_ruleset = config_manager.get_effective_validation_ruleset_name()
        print(f"  - 当前校验规则集: {validation_ruleset}")
        
        # 测试预处理规则
        preprocessing_ruleset = config_manager.get_effective_preprocessing_ruleset_name()
        print(f"  - 当前预处理规则集: {preprocessing_ruleset}")
        
        # 测试清洗规则
        cleaning_ruleset = config_manager.get_effective_cleaning_ruleset_name()
        print(f"  - 当前清洗规则集: {cleaning_ruleset}")

    def main():
        """主测试函数"""
        print("重构后的配置管理体系详细测试")
        print("=" * 50)
        
        test_config_metadata()
        test_global_config()
        test_project_config()
        test_project_switching()
        test_rules_loading()
        
        print("\n" + "=" * 50)
        print("测试完成")

    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"测试过程中出错: {e}")
    import traceback
    traceback.print_exc()