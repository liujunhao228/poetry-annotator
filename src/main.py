import click
import asyncio
import sys
from pathlib import Path
from typing import Optional, Tuple
import logging
import os

# 处理导入问题
# 确保 src 目录在 sys.path 中，以便绝对导入可以找到 src 下的模块
import sys
import os
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    print(f"已将 {src_dir} 添加到 sys.path")

# 使用绝对导入
from project import Project
from config_manager import ConfigManager
from logging_config import setup_default_logging, get_logger

# 获取主日志记录器
logger = get_logger(__name__)



@click.group()
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default=None, # 改为None，优先使用配置文件
              help='设置日志级别（可选，将覆盖配置文件设置）')
@click.option('--log-file', help='指定日志文件路径（可选，将覆盖配置文件设置）')
@click.option('--enable-file-log', is_flag=True, default=None, 
              help='启用文件日志输出（可选，将覆盖配置文件设置）')
@click.option('--project', type=str, required=True, help='项目名称')
@click.option('--db-name', type=str, default="default", help='数据库名称（从项目配置文件中获取路径，默认为 "default"）')
def cli(log_level, log_file, enable_file_log, project, db_name):
    """LLM诗词情感标注工具"""
    # 1. 创建项目实例
    project_instance = Project(project_name=project, project_root_dir=Path("projects"))
    
    # 2. 根据项目配置设置日志
    try:
        project_instance.setup_project_logging()
        # 重新获取 logger 实例，因为日志配置已更改
        # Note: 在函数中重新赋值模块级别的logger变量，不需要global声明，
        # 因为logger已经在模块级别定义了
        globals()['logger'] = get_logger(__name__)
        logger = globals()['logger']
    except Exception as e:
        # 如果项目日志配置有问题，使用CLI参数或默认值
        # setup_default_logging 期望 console_level, file_level, enable_file_log, log_file
        setup_default_logging(console_level=log_level, enable_file_log=enable_file_log, log_file=log_file)
        # 重新获取 logger 实例，因为日志配置已更改
        # Note: 在函数中重新赋值模块级别的logger变量，不需要global声明，
        # 因为logger已经在模块级别定义了
        globals()['logger'] = get_logger(__name__)
        logger = globals()['logger']
        logger.warning(f"使用默认日志配置，因为项目日志配置失败: {e}")
    
    # 记录启动信息
    logger.info("=" * 60)
    logger.info(f"LLM诗词情感标注工具启动 (项目: {project})")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")
    logger.info(f"项目根目录: {project_instance.root_path}")
    logger.info(f"日志级别: {logging.getLevelName(logger.level)}")
    logger.info("=" * 60)


@cli.command()
@click.option('--config', default='config.ini', help='项目配置文件路径 (相对于项目目录)')
@click.option('--init-db', is_flag=True, help='初始化数据库（从JSON文件加载数据）')
@click.option('--clear-existing', is_flag=True, help='清空现有数据后重新初始化')
def setup(config, init_db, clear_existing):
    """初始化项目环境"""
    try:
        # 从全局CLI上下文中获取项目实例
        # 由于 `cli` 函数已经创建了 `Project` 实例并存储在局部变量 `project_instance` 中，
        # 我们需要一种方式让子命令能够访问它。Click 提供了 `click.pass_context` 来传递上下文。
        # 但更简单的方式是在 `cli` 中将 project_instance 存储到一个模块级变量或使用其他上下文管理方式。
        # 为了保持简单和解耦，我们在这里重新创建 Project 实例，
        # 这在实际应用中可能不是最优的，但对于此重构是可行的，因为 Project 使用了懒加载。
        # 从命令行参数获取项目名称
        ctx = click.get_current_context()
        project_name = ctx.parent.params['project']
        project_instance = Project(project_name=project_name, project_root_dir=Path("projects"))
        
        logger.info("开始初始化项目环境...")
        
        # 检查配置文件
        config_path = project_instance.root_path / config
        if not config_path.exists():
            template_path = config_path.with_suffix(config_path.suffix + '.template')
            logger.info(f"配置文件 {config_path} 不存在。")
            if template_path.exists():
                logger.info(f"请复制模板文件 {template_path} 为 {config_path} 并配置您的API密钥。")
            else:
                logger.warning(f"模板文件 {template_path} 也不存在。您需要手动创建配置文件 {config_path}。")
            return

        # 项目实例的 config_manager 已经在 __init__ 中加载了配置
        logger.info("配置文件加载成功")
        
        # 记录配置信息
        try:
            llm_config = project_instance.config_manager.get_llm_config()
            logger.info(f"LLM配置 - 并发数: {llm_config.get('max_workers')}")
            
            db_config = project_instance.config_manager.get_database_config()
            logger.info(f"数据库配置 - 路径: {db_config.get('db_path', 'N/A')}")
            
            data_config = project_instance.config_manager.get_data_config()
            logger.info(f"数据配置 - 源目录: {data_config.get('source_dir')}, 输出目录: {data_config.get('output_dir')}")
            
        except Exception as e:
            logger.warning(f"配置信息记录失败: {e}")
        
        # 确保情感分类体系是最新的（从Markdown文件生成XML文件）
        try:
            logger.info("检查情感分类体系文件...")
            categories_config = project_instance.config_manager.get_categories_config()
            xml_path = project_instance.root_path / categories_config.get('xml_path', 'categories.xml')
            md_path = project_instance.root_path / categories_config.get('md_path', 'classification_schema.md')
            
            if xml_path.exists() and md_path.exists():
                # 如果Markdown文件存在且比XML文件新，或者XML文件不存在，则重新生成XML
                if md_path.stat().st_mtime > xml_path.stat().st_mtime:
                    logger.info(f"检测到Markdown文件更新，正在重新生成XML文件...")
                    # 重新创建label_parser实例以触发解析和生成
                    # 从项目上下文获取标签解析器
                    label_parser_instance = project_instance.label_parser
                    # 重新解析和生成，如果需要的话
                    # Note: LabelParser 的 _load_categories 方法会检查文件修改时间并决定是否重新生成
                    logger.info("情感分类体系XML文件已更新或已是最新")
                else:
                    logger.info("情感分类体系XML文件已是最新")
            elif md_path.exists():
                logger.info("仅发现Markdown文件，正在生成XML文件...")
                label_parser_instance = project_instance.label_parser
                logger.info("情感分类体系XML文件已生成")
            else:
                logger.warning(f"未找到情感分类体系文件（{md_path} 或 {xml_path}）")
        except Exception as e:
            logger.warning(f"情感分类体系文件检查失败: {e}")
        
        if init_db:
            logger.info("开始从JSON文件初始化数据库...")
            try:
                # 使用项目实例的 DataManager 来初始化数据库
                # 这里我们直接调用 DataManager 的方法，而不是旧的全局方法
                data_manager_instance = project_instance.get_data_manager(db_name=ctx.parent.params['db_name'])
                # 从项目配置中获取数据源目录
                source_dir = project_instance.root_path / data_config.get('source_dir', 'data')
                # 加载数据并初始化
                result = data_manager_instance.initialize_database_from_json(clear_existing=clear_existing)
                logger.info(f"数据库初始化完成! 作者: {result['authors']}, 诗词: {result['poems']}")
            except Exception as e:
                logger.error(f"数据库初始化失败: {e}")
                return
        
        logger.info("项目环境初始化完成！")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)


async def run_multi_model_annotation(models: Tuple[str], limit: Optional[int], id_range: Optional[str], force_rerun: bool, project_instance: Project):
    """异步调度器，用于运行多模型标注任务"""
    start_id, end_id = None, None
    if id_range:
        try:
            start_id, end_id = map(int, id_range.split(':'))
            logger.info(f"标注范围: {start_id} - {end_id}")
        except ValueError:
            logger.error("范围格式错误，请使用 'start:end' 格式")
            return
            
    # 如果未指定模型，要求用户必须指定
    if not models:
        logger.error("必须指定至少一个模型配置。请使用 --model 选项指定模型配置别名。")
        return
    target_models = list(models)
    logger.info(f"将要执行标注任务的模型配置: {target_models}")

    # 不再创建批次日志记录器，直接使用全局日志记录器
    batch_logger = logger
    batch_logger.info(f"开始新的标注批次任务 - 模型: {target_models}, 范围: {id_range or '全部'}")

    # 为每个模型创建并运行一个标注任务
    tasks = []
    for model_alias in target_models:
        try:
            logger.info(f"创建模型配置 '{model_alias}' 的标注器...")
            # 不再设置环境变量用于批次日志
            # 使用项目实例来获取 Annotator
            annotator = project_instance.get_annotator(config_name=model_alias)
            task = annotator.run(
                limit=limit,
                start_id=start_id,
                end_id=end_id,
                force_rerun=force_rerun
            )
            tasks.append(task)
            logger.info(f"模型配置 '{model_alias}' 的标注任务已创建")
            batch_logger.info(f"模型配置 '{model_alias}' 的标注任务已创建")
        except Exception as e:
            logger.error(f"创建模型配置 '{model_alias}' 的标注器失败: {e}")
            batch_logger.error(f"创建模型配置 '{model_alias}' 的标注器失败: {e}")
    
    if not tasks:
        logger.warning("没有可执行的标注任务。")
        batch_logger.warning("没有可执行的标注任务。")
        return

    # 并发执行所有模型任务
    logger.info(f"开始并发执行 {len(tasks)} 个标注任务...")
    batch_logger.info(f"开始并发执行 {len(tasks)} 个标注任务...")
    results = await asyncio.gather(*tasks)

    # 汇总并打印最终报告
    total_completed, total_failed = 0, 0
    logger.info("\n=== 多模型标注任务最终报告 ===")
    batch_logger.info("\n=== 多模型标注任务最终报告 ===")
    for res in results:
        logger.info(
            f"模型配置 [{res['model']}]: "
            f"总计={res['total']}, 成功={res['completed']}, 失败={res['failed']}"
        )
        batch_logger.info(
            f"模型配置 [{res['model']}]: "
            f"总计={res['total']}, 成功={res['completed']}, 失败={res['failed']}"
        )
        total_completed += res.get('completed', 0)
        total_failed += res.get('failed', 0)
    logger.info("---------------------------------")
    batch_logger.info("---------------------------------")
    logger.info(f"所有模型总计: 成功={total_completed}, 失败={total_failed}")
    batch_logger.info(f"所有模型总计: 成功={total_completed}, 失败={total_failed}")
    logger.info("=================================")
    batch_logger.info("=================================")


@cli.command()
@click.option('--model', 'models', multiple=True, help="指定一个或多个模型配置别名 (例如 'gpt-4o'), 可多次使用此选项。")
@click.option('--limit', type=int, help='限制每个模型本次标注的数量')
@click.option('--range', 'id_range', help='按ID范围进行标注 (例如: 1:100)')
@click.option('--force-rerun', is_flag=True, help='强制重新标注已完成的条目')
def annotate(models, limit, id_range, force_rerun):
    """启动一个或多个模型的并发标注任务"""
    try:
        # 从全局CLI上下文中获取项目实例
        ctx = click.get_current_context()
        project_name = ctx.parent.params['project']
        project_instance = Project(project_name=project_name, project_root_dir=Path("projects"))
        
        logger.info("启动多模型并发标注任务...")
        
        # 记录任务参数
        logger.info(f"任务参数 - 模型: {models or '未指定'}, 限制: {limit or '无'}, 范围: {id_range or '全部'}, 强制重跑: {force_rerun}")
        
        asyncio.run(run_multi_model_annotation(models, limit, id_range, force_rerun, project_instance))
        
        logger.info("标注任务执行完成")
    except Exception as e:
        logger.error(f"标注任务执行失败: {e}", exc_info=True)

@cli.command()
def status():
    """显示标注进度统计 (按模型配置)"""
    try:
        # 从全局CLI上下文中获取项目实例
        ctx = click.get_current_context()
        project_name = ctx.parent.params['project']
        project_instance = Project(project_name=project_name, project_root_dir=Path("projects"))
        
        logger.info("获取标注进度统计...")
        # 使用项目实例的 DataManager 来获取统计信息
        data_manager_instance = project_instance.get_data_manager(db_name=ctx.parent.params['db_name'])
        stats = data_manager_instance.get_statistics()
        
        print("\n=== 标注进度统计 ===")
        print(f"总诗词数量: {stats.get('total_poems', 0)}")
        print(f"总作者数量: {stats.get('total_authors', 0)}")
        
        if not stats.get('stats_by_model'):
            print("\n尚未有任何模型的标注记录。")
            logger.info("当前没有标注记录")
            return
            
        print("\n--- 按模型配置统计 ---")
        for model, model_stats in stats['stats_by_model'].items():
            completed = model_stats.get('completed', 0)
            failed = model_stats.get('failed', 0)
            total = completed + failed
            completion_rate = (completed / stats['total_poems'] * 100) if stats['total_poems'] > 0 else 0
            
            print(f"\n模型配置: {model}")
            print(f"  - 已标注: {total} / {stats['total_poems']} ({completion_rate:.2f}%)")
            print(f"  - 成功: {completed}")
            print(f"  - 失败: {failed}")
            
            logger.info(f"模型 {model}: 完成率 {completion_rate:.2f}% ({completed}/{stats['total_poems']})")
        
        print()
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)


@cli.command()
@click.option('--format', 'output_format', default='jsonl', 
              type=click.Choice(['jsonl', 'json']), help='输出格式')
@click.option('--output', help='输出文件路径 (可选)')
@click.option('--model', 'model_filter', help='只导出指定模型配置的标注结果 (可选)')
def export(output_format, output, model_filter):
    """导出标注结果"""
    try:
        # 从全局CLI上下文中获取项目实例
        ctx = click.get_current_context()
        project_name = ctx.parent.params['project']
        project_instance = Project(project_name=project_name, project_root_dir=Path("projects"))
        
        if model_filter:
            logger.info(f"导出模型配置 [{model_filter}] 的标注结果，格式: {output_format}")
        else:
            logger.info(f"导出所有已完成的标注结果，格式: {output_format}")
        
        # 使用项目实例的 DataManager 来导出结果
        data_manager_instance = project_instance.get_data_manager(db_name=ctx.parent.params['db_name'])
        output_file = data_manager_instance.export_results(
            output_format=output_format,
            output_file=output,
            model_filter=model_filter
        )
        
        logger.info(f"结果已导出到: {output_file}")
        
    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)


@cli.command(name="list-models")
def list_models():
    """列出在config.ini中已配置的模型"""
    try:
        # 从全局CLI上下文中获取项目实例
        ctx = click.get_current_context()
        project_name = ctx.parent.params['project']
        project_instance = Project(project_name=project_name, project_root_dir=Path("projects"))
        
        logger.info("获取已配置的模型列表...")
        # 使用项目实例的 LLMFactory 来获取配置的模型列表
        llm_factory_instance = project_instance.llm_factory
        configured_models = llm_factory_instance.list_configured_models()
        
        print("\n=== 已配置的模型 ===")
        if not configured_models:
            print("⚠️ 没有在 config.ini 中找到任何 [Model.*] 配置。")
            print("请参考 config.ini.template 添加您的模型配置。")
            logger.warning("未找到任何模型配置")
        else:
            for name, details in configured_models.items():
                print(f"  - {name}")
                print(f"    - provider: {details.get('provider')}")
                print(f"    - model_name: {details.get('model_name')}")
                
                logger.info(f"模型配置: {name} (provider: {details.get('provider')}, model: {details.get('model_name')})")
        
        print()
        
    except Exception as e:
        logger.error(f"获取已配置模型列表失败: {e}", exc_info=True)


@cli.command(name="recover-from-logs")
@click.option('--log-path', required=True, help='日志文件或目录路径')
@click.option('--model', 'model_identifier', required=True, help='保存标注到数据库时使用的模型标识符, 例如 "gemini-2.5-flash"。')
@click.option('--dry-run', is_flag=True, default=False, help='试运行模式，仅分析日志，不写入数据库')
def recover_from_logs(log_path, model_identifier, dry_run):
    """从日志文件中恢复因意外中断而未保存的标注数据"""
    try:
        logger.info("开始执行日志恢复任务...")
        
        # 导入恢复功能模块
        from scripts.recover_from_log_v6 import cli as recover_cli
        
        # 构造参数
        import sys
        original_argv = sys.argv[:]
        
        # 构造新的命令行参数
        sys.argv = ['recover_from_log_v6.py']
        
        # 判断是文件还是目录
        path_obj = Path(log_path)
        if path_obj.is_file():
            sys.argv.extend(['--file', str(path_obj)])
        elif path_obj.is_dir():
            sys.argv.extend(['--dir', str(path_obj)])
        else:
            logger.error(f"指定的路径既不是文件也不是目录: {log_path}")
            return
            
        sys.argv.extend(['--model', model_identifier])
        
        # 如果不是dry-run，则添加--write标志
        if not dry_run:
            sys.argv.append('--write')
            
        # 调用恢复功能
        recover_cli()
        
        # 恢复原始参数
        sys.argv = original_argv
        
        logger.info("日志恢复任务执行完成")
        
    except Exception as e:
        logger.error(f"日志恢复任务执行失败: {e}", exc_info=True)


if __name__ == '__main__':
    cli()
