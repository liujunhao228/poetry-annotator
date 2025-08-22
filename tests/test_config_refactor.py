#!/usr/bin/env python3
"""
测试重构后的配置管理体系
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
    
    def test_config_structure():
        """测试配置结构"""
        print("=== 测试配置管理体系 ===")
        
        # 测试全局配置
        print("\n1. 测试全局配置:")
        print(f"  - 全局配置文件路径: {config_manager.global_config_path}")
        
        # 测试项目配置
        print("\n2. 测试项目配置:")
        active_project = project_config_manager.get_active_project()
        print(f"  - 当前激活的项目: {active_project}")
        available_projects = project_config_manager.get_available_projects()
        print(f"  - 可用项目列表: {available_projects}")
        print(f"  - 当前项目配置文件路径: {config_manager.project_config_path}")
        
        # 显示所有项目配置文件路径
        print("  - 所有项目配置文件路径:")
        for project in available_projects:
            project_path = f"config/projects/{project}"
            exists = "✓" if os.path.exists(project_path) else "✗"
            print(f"    {exists} {project_path}")
        
        # 测试规则配置
        print("\n3. 测试规则配置:")
        print(f"  - 校验规则集名称: {config_manager.get_effective_validation_ruleset_name()}")
        print(f"  - 预处理规则集名称: {config_manager.get_effective_preprocessing_ruleset_name()}")
        print(f"  - 清洗规则集名称: {config_manager.get_effective_cleaning_ruleset_name()}")
        
        # 测试模型配置
        print("\n4. 测试模型配置:")
        models = config_manager.get_effective_model_configs()
        print(f"  - 项目使用的模型数量: {len(models)}")
        for model in models:
            print(f"    - {model.get('model_name', 'Unknown')}")
        
        # 测试数据库配置
        print("\n5. 测试数据库配置:")
        db_config = config_manager.get_effective_database_config()
        print(f"  - 数据库配置: {db_config}")
        
        # 测试切换项目
        print("\n6. 测试切换项目:")
        # 切换到宋词项目
        print("  - 切换到宋词项目...")
        success = config_manager.switch_project_config("songci/project.ini")
        if success:
            print(f"  - 成功切换到宋词项目")
            new_active = project_config_manager.get_active_project()
            print(f"  - 当前激活的项目: {new_active}")
            print(f"  - 当前项目配置文件路径: {config_manager.project_config_path}")
        else:
            print("  - 切换项目失败")
        
        # 切换回唐诗项目
        print("  - 切换回唐诗项目...")
        success = config_manager.switch_project_config("tangshi/project.ini")
        if success:
            print(f"  - 成功切换回唐诗项目")
            new_active = project_config_manager.get_active_project()
            print(f"  - 当前激活的项目: {new_active}")
            print(f"  - 当前项目配置文件路径: {config_manager.project_config_path}")
        else:
            print("  - 切换项目失败")

    if __name__ == "__main__":
        test_config_structure()
        
except Exception as e:
    print(f"导入模块时出错: {e}")
    import traceback
    traceback.print_exc()