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


from src.task_distribution.manager import run_distribution_task # Import the new function

def run_cli_mode(unknown_args):
    """运行CLI模式"""
    # 解析 unknown_args 为 run_distribution_task 的参数
    # 注意：这里需要将命令行参数转换为函数参数
    # 这是一个简化的示例，实际应用中可能需要更复杂的参数解析逻辑
    
    # 默认参数值
    params = {
        "selected_models": [],
        "id_file": None,
        "id_dir": None,
        "force_rerun": False,
        "chunk_size": 1000,
        "fresh_start": False,
        "db_name": "",
        "console_log_level": None,
        "file_log_level": None,
        "enable_file_log": None,
        "dry_run": False,
        "full_dry_run": False,
    }

    i = 0
    while i < len(unknown_args):
        arg = unknown_args[i]
        if arg == '--selected-models' or arg == '-m':
            i += 1
            while i < len(unknown_args) and not unknown_args[i].startswith('-'):
                params["selected_models"].append(unknown_args[i])
                i += 1
            i -= 1 # Adjust index for next loop iteration
        elif arg == '--id-file' or arg == '-f':
            params["id_file"] = unknown_args[i+1]
            i += 1
        elif arg == '--id-dir' or arg == '-d':
            params["id_dir"] = unknown_args[i+1]
            i += 1
        elif arg == '--force-rerun' or arg == '-r':
            params["force_rerun"] = True
        elif arg == '--chunk-size' or arg == '-c':
            params["chunk_size"] = int(unknown_args[i+1])
            i += 1
        elif arg == '--fresh-start' or arg == '-s':
            params["fresh_start"] = True
        elif arg == '--db':
            params["db_name"] = unknown_args[i+1]
            i += 1
        elif arg == '--console-log-level':
            params["console_log_level"] = unknown_args[i+1]
            i += 1
        elif arg == '--file-log-level':
            params["file_log_level"] = unknown_args[i+1]
            i += 1
        elif arg == '--enable-file-log':
            params["enable_file_log"] = True
        elif arg == '--dry-run':
            params["dry_run"] = True
        elif arg == '--full-dry-run':
            params["full_dry_run"] = True
        i += 1

    print(f"正在以CLI模式执行任务函数: run_distribution_task，参数: {params}")

    try:
        result = run_distribution_task(**params)
        if result.get("status") == "completed_with_errors":
            print(f"CLI任务函数执行失败，错误: {result.get('errors')}")
            sys.exit(1)
        else:
            print("CLI任务函数执行成功。")
    except Exception as e:
        print(f"运行CLI任务函数时发生异常: {e}")
        sys.exit(1)


def run_init_db_mode():
    """运行数据库初始化模式"""
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


def run_gui_mode():
    """运行GUI模式"""
    try:
        # 直接导入并运行GUI应用
        from gui.app import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"错误: 无法导入GUI模块 - {e}")
        print("请确保GUI模块已正确安装。")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 启动GUI模式时出现问题 - {e}")
        sys.exit(1)


def run_gui_review_mode():
    """运行标注校对GUI模式"""
    # 启动标注校对GUI模式
    try:
        # 直接导入并运行标注校对GUI模块
        from src.gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"错误: 无法导入标注校对GUI模块 - {e}")
        print("请确保GUI模块已正确安装。")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 启动标注校对GUI模式时出现问题 - {e}")
        sys.exit(1)


def run_visualizer_mode():
    """运行数据可视化模式"""
    # 检查是否安装了streamlit
    try:
        import streamlit
    except ImportError:
        print("错误: 未安装streamlit。请运行 'pip install streamlit' 后重试。")
        sys.exit(1)
        
    # 运行数据可视化应用
    # 注意: 项目中可能没有专门的可视化模块，这里提供一个占位实现
    print("警告: 数据可视化模块尚未实现或未找到相关脚本。")
    print("如果需要使用数据可视化功能，请确保相关模块已正确安装。")
    sys.exit(1)


def run_test_annotate_mode(unknown_args):
    """运行简化测试标注模式"""
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger("test-annotate-autofill")

    logger.info("Simplified test annotation mode enabled.")
    
    # 默认启用 dry-run 和 full-dry-run
    if '--dry-run' not in unknown_args:
        unknown_args.append('--dry-run')
    if '--full-dry-run' not in unknown_args:
        unknown_args.append('--full-dry-run')

    # 检查是否已提供模型参数，如果没有，则添加默认值
    has_model_arg = any(arg.startswith('--model') or arg == '-m' or arg == '--all-models' or arg == '-a' for arg in unknown_args)
    if not has_model_arg:
        # 优先尝试从 project/project.ini 读取 fake 开头的模型名
        import configparser
        ini_path = project_root / 'project' / 'project.ini'
        fake_model = None
        logger.info("未检测到模型参数，尝试自动补全 dry-run 模型……")
        if ini_path.exists():
            config = configparser.ConfigParser()
            config.read(str(ini_path), encoding='utf-8')
            if 'Model' in config and 'model_names' in config['Model']:
                model_names = [m.strip() for m in config['Model']['model_names'].split(',')]
                logger.info(f"从配置文件读取到模型列表: {model_names}")
                for m in model_names:
                    if m.lower().startswith('fake'):
                        fake_model = m
                        logger.info(f"检测到以 'fake' 开头的模型: {fake_model}")
                        break
        else:
            logger.warning(f"未找到配置文件: {ini_path}")
        if fake_model:
            logger.info(f"为 test-annotate 自动选择模型参数: --model {fake_model}")
            unknown_args.extend(['--model', fake_model])
        else:
            logger.info("未找到以 'fake' 开头的模型，回退为 --all-models")
            unknown_args.append('--all-models')
    else:
        logger.info("已检测到模型参数，跳过自动补全。")

    # 检查是否已提供ID目录参数，如果没有，则添加默认值
    has_id_arg = any(arg.startswith('--id-file') or arg == '-f' or arg.startswith('--id-dir') or arg == '-d' for arg in unknown_args)
    if not has_id_arg:
        logger.info("为 test-annotate 添加默认ID目录参数: --id-dir ids")
        unknown_args.append('--id-dir')
        unknown_args.append('ids')
    else:
        logger.info("已检测到 ID参数，跳过自动补全。")

    logger.info(f"最终 test-annotate 参数列表: {unknown_args}")
    
    # 确保数据库已初始化
    logger.info("在 test-annotate 模式下，自动初始化数据库...")
    from src.db_initializer import get_db_initializer
    from src.db_initializer.functions import initialize_all_databases_from_source_folders # Import the function
    
    db_initializer = get_db_initializer()
    db_initializer.initialize_separate_databases()
    
    # 在 test-annotate 模式下，确保数据也被导入
    logger.info("在 test-annotate 模式下，自动导入数据...")
    import_results = initialize_all_databases_from_source_folders()
    logger.info(f"数据导入结果: {import_results}")
    
    run_cli_mode(unknown_args)


def parse_arguments():
    """解析命令行参数"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="LLM诗词情感标注工具")
    parser.add_argument(
        "--mode",
        choices=["cli", "gui", "gui-review", "visualizer", "init-db", "test-annotate"],
        default="cli",
        help="启动模式: cli(命令行模式)、gui(功能工具集GUI模式)、gui-review(标注校对GUI模式)、visualizer(数据可视化模式)、init-db(初始化数据库) 或 test-annotate(简化测试标注模式) (默认: cli)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="空运行模式，使用假数据测试主流程"
    )
    parser.add_argument(
        "--full-dry-run",
        action="store_true",
        help="在dry-run模式下，执行完整流程测试（包括响应解析、内容验证、数据保存到JSON文件），而非跳过这些流程。"
    )
    
    # 解析参数
    args, unknown = parser.parse_known_args()
    
    # 将所有未知参数收集起来，传递给 run_cli_mode
    # 这比之前的方法更健壮，能处理所有 --key=value 和 --key value 形式的参数
    return args, unknown


def main():
    """主函数"""
    args, unknown_args = parse_arguments()

    if args.dry_run:
        # 日志记录设置
        import logging
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
        logger = logging.getLogger("dryrun-autofill")

        logger.info("Dry-run mode enabled.")
        # 确保 --dry-run 标志在参数列表中
        if '--dry-run' not in unknown_args:
            unknown_args.append('--dry-run')
        
        # 如果指定了 --full-dry-run，也将其添加到 unknown_args
        if args.full_dry_run and '--full-dry-run' not in unknown_args:
            unknown_args.append('--full-dry-run')

        # 检查是否已提供模型或ID文件参数，如果没有，则添加默认值
        has_model_arg = any(arg.startswith('--model') or arg == '-m' or arg == '--all-models' or arg == '-a' for arg in unknown_args)
        has_id_arg = any(arg.startswith('--id-file') or arg == '-f' or arg.startswith('--id-dir') or arg == '-d' for arg in unknown_args)

        if not has_model_arg:
            # 优先尝试从 project/project.ini 读取 fake 开头的模型名
            import configparser
            ini_path = project_root / 'project' / 'project.ini'
            fake_model = None
            logger.info("未检测到 dry-run 模型参数，尝试自动补全……")
            if ini_path.exists():
                config = configparser.ConfigParser()
                config.read(str(ini_path), encoding='utf-8')
                if 'Model' in config and 'model_names' in config['Model']:
                    model_names = [m.strip() for m in config['Model']['model_names'].split(',')]
                    logger.info(f"从配置文件读取到模型列表: {model_names}")
                    for m in model_names:
                        if m.lower().startswith('fake'):
                            fake_model = m
                            logger.info(f"检测到以 'fake' 开头的模型: {fake_model}")
                            break
            else:
                logger.warning(f"未找到配置文件: {ini_path}")
            if fake_model:
                logger.info(f"为 dry-run 自动选择模型参数: --model {fake_model}")
                unknown_args.extend(['--model', fake_model])
            else:
                logger.info("未找到以 'fake' 开头的模型，回退为 --all-models")
                unknown_args.append('--all-models')
        else:
            logger.info("已检测到 dry-run 模型参数，跳过自动补全。")
        if not has_id_arg:
            logger.info("为 dry-run 添加默认ID目录参数: --id-dir ids")
            unknown_args.append('--id-dir')
            unknown_args.append('ids')
        else:
            logger.info("已检测到 dry-run ID参数，跳过自动补全。")

        # 在 dry-run 模式下，我们强制使用 cli 模式
        logger.info(f"最终 dry-run 参数列表: {unknown_args}")
        run_cli_mode(unknown_args)
        return
    
    # 根据模式运行相应功能
    if args.mode == "init-db":
        run_init_db_mode()
    elif args.mode == "gui":
        run_gui_mode()
    elif args.mode == "gui-review":
        run_gui_review_mode()
    elif args.mode == "visualizer":
        run_visualizer_mode()
    elif args.mode == "test-annotate":
        run_test_annotate_mode(unknown_args)
    else:
        # CLI模式
        run_cli_mode(unknown_args)


if __name__ == '__main__':
    main()
