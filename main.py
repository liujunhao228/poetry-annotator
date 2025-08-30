#!/usr/bin/env python3
"""
LLM诗词情感标注工具
主入口文件
"""

import sys
import os
from pathlib import Path
import argparse

# 添加项目根目录到Python路径，确保能正确导入src下的模块
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 使用绝对导入方式
from src.main import cli
from src.db_initializer import get_db_initializer

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="LLM诗词情感标注工具")
    parser.add_argument(
        "--mode",
        choices=["cli", "gui", "gui-review", "visualizer", "init-db"],
        default="cli",
        help="启动模式: cli(命令行模式)、gui(功能工具集GUI模式)、gui-review(标注校对GUI模式)、visualizer(数据可视化模式) 或 init-db(初始化数据库) (默认: cli)"
    )
    
    # 解析参数
    args, unknown = parser.parse_known_args()
    
    # 检查是否有项目配置参数
    project_arg_idx = -1
    for i, arg in enumerate(sys.argv):
        if arg == '--project':
            project_arg_idx = i
            break
        elif arg.startswith('--project='):
            project_arg_idx = i
            break
    
    if project_arg_idx != -1:
        # 如果有项目配置参数，需要传递给CLI
        if '=' in sys.argv[project_arg_idx]:
            # 格式为 --project=value
            unknown.extend([sys.argv[project_arg_idx]])
        else:
            # 格式为 --project value
            if project_arg_idx + 1 < len(sys.argv):
                unknown.extend([sys.argv[project_arg_idx], sys.argv[project_arg_idx + 1]])
    
    if args.mode == "init-db":
        # 初始化数据库模式
        print("开始初始化数据库...")
        from src.db_initializer import get_db_initializer
        db_initializer = get_db_initializer()
        
        # 初始化分离的数据库结构
        print("\n开始初始化分离的数据库结构...")
        separate_results = db_initializer.initialize_separate_databases()
        
        print("\n分离数据库初始化结果:")
        for db_name, db_results in separate_results.items():
            print(f"  {db_name}:")
            for sub_db_name, result in db_results.items():
                status = result.get('status', 'unknown') if isinstance(result, dict) else 'unknown'
                message = result.get('message', '') if isinstance(result, dict) else str(result)
                print(f"    {sub_db_name}: {status} - {message}")
            
        # 导入数据
        print("\n开始导入数据...")
        from src.db_initializer.functions import initialize_all_databases_from_source_folders
        import_results = initialize_all_databases_from_source_folders()
        
        print("\n数据导入结果:")
        for db_name, result in import_results.items():
            if 'error' in result:
                print(f"  {db_name}: 错误 - {result['error']}")
            else:
                print(f"  {db_name}: authors={result.get('authors', 0)}, poems={result.get('poems', 0)}")
            
        # 显示数据库统计信息
        print("\n数据库统计信息:")
        stats = db_initializer.get_database_stats()
        
        # 遍历所有数据库统计信息
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
                print(f"信息: {str(stat)}")
    elif args.mode == "gui":
        # 启动GUI模式 (使用scripts/gui_launcher.py)
        gui_script_path = Path(__file__).parent / "scripts" / "gui_launcher.py"
        if gui_script_path.exists():
            # 直接运行GUI脚本
            os.system(f"{sys.executable} {gui_script_path}")
        else:
            print("错误: 找不到GUI启动器脚本 (scripts/gui_launcher.py)")
            sys.exit(1)
    elif args.mode == "gui-review":
        # 启动标注校对GUI模式 (使用src/gui.py)
        try:
            # 直接导入并运行标注校对GUI模块
            from src.gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"错误: 无法导入标注校对GUI模块 - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"错误: 启动标注校对GUI模式时出现问题 - {e}")
            sys.exit(1)
    elif args.mode == "visualizer":
        # 启动数据可视化模式
        # 设置数据可视化模块路径
        visualizer_path = project_root / "poetry-annotator-data-visualizer"
        if str(visualizer_path) not in sys.path:
            sys.path.insert(0, str(visualizer_path))
        
        # 检查是否安装了streamlit
        try:
            import streamlit
        except ImportError:
            print("错误: 未安装streamlit。请运行 'pip install streamlit' 后重试。")
            sys.exit(1)
            
        # 在启动可视化之前，先运行数据迁移脚本
        db_setup_script_path = visualizer_path / "data_visualizer" / "db_setup.py"
        if db_setup_script_path.exists():
            print("正在更新标注结果数据库...")
            # 使用subprocess运行数据迁移脚本，确保它在正确的环境中执行
            import subprocess
            # 构造PYTHONPATH环境变量，包含数据可视化模块路径
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{visualizer_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
            result = subprocess.run([sys.executable, str(db_setup_script_path)], cwd=str(visualizer_path), env=env)
            if result.returncode != 0:
                print("警告: 数据库更新脚本执行失败。将继续启动可视化应用。")
            else:
                print("标注结果数据库更新完成。")
        else:
            print("警告: 找不到数据库更新脚本 (poetry-annotator-data-visualizer/data_visualizer/db_setup.py)。将继续启动可视化应用。")
            
        # 运行数据可视化应用
        visualizer_script_path = visualizer_path / "main.py"
        if visualizer_script_path.exists():
            # 使用streamlit运行可视化应用
            os.system(f"{sys.executable} -m streamlit run {visualizer_script_path}")
        else:
            print("错误: 找不到数据可视化启动脚本 (poetry-annotator-data-visualizer/main.py)")
            sys.exit(1)
    else:
        # 启动CLI模式
        # 将未知参数传递给click
        sys.argv[1:] = unknown
        cli()

if __name__ == '__main__':
    main()