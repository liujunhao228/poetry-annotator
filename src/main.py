import click
import asyncio
import sys
import configparser
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
from src.project import Project
from src.config_manager import ConfigManager
from src.logging_config import setup_default_logging, get_logger

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
@click.option('--project', type=str, help='项目名称 (可选, 默认使用全局配置中的激活项目)')
@click.option('--db-name', type=str, default="default", help='数据库名称（从项目配置文件中获取路径，默认为 "default"）')
@click.pass_context
def cli(ctx, log_level, log_file, enable_file_log, project, db_name):
    """LLM诗词情感标注工具"""
    # Pass the absolute path to the global config.ini
    global_config_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')))
    
    # 如果未指定项目，则从全局配置中获取激活项目
    if not project:
        try:
            global_config = ConfigManager([str(global_config_path)])
            active_project_config_path = global_config.config.get('Project', 'active_project_config')
            # 从路径 'projects/your_project_name/project_config.ini' 中提取 'your_project_name'
            project = Path(active_project_config_path).parent.name
            print(f"未指定项目，将使用激活项目: {project}")
        except (configparser.NoSectionError, configparser.NoOptionError, IndexError) as e:
            print(f"错误: 无法从全局配置中确定激活项目: {e}")
            print("请使用 --project <项目名称> 参数指定一个项目，或在 config/config.ini 中设置 active_project_config。")
            sys.exit(1)

    # 1. 创建项目实例
    project_instance = Project(project_name=project, project_root_dir=Path("projects"), global_config_path=global_config_path)
    
    # 2. 将项目实例和db_name存储在上下文中，供子命令使用
    ctx.obj = {'project_instance': project_instance, 'db_name': db_name}
    
    # 3. 根据项目配置设置日志
    try:
        project_instance.setup_project_logging()
        globals()['logger'] = get_logger(__name__)
    except Exception as e:
        setup_default_logging(
            console_level=log_level, 
            enable_file_log=enable_file_log, 
            log_file=log_file,
            global_config_path=global_config_path
        )
        globals()['logger'] = get_logger(__name__)
        logger.warning(f"使用默认日志配置，因为项目日志配置失败: {e}")
    
    # 记录启动信息
    logger.info("=" * 60)
    logger.info(f"LLM诗词情感标注工具启动 (项目: {project})")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")
    logger.info(f"项目根目录: {project_instance.root_path}")
    logger.info(f"日志级别: {logging.getLevelName(get_logger(__name__).level)}")
    logger.info("=" * 60)


@cli.command()
@click.option('--init-db', is_flag=True, help='初始化数据库（从JSON文件加载数据）')
@click.option('--clear-existing', is_flag=True, help='清空现有数据后重新初始化')
@click.pass_context
def setup(ctx, init_db, clear_existing):
    """初始化或检查当前激活项目的环境"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']
        
        logger.info(f"开始检查和设置项目 '{project_instance.name}' 的环境...")

        # 1. 检查配置文件是否存在
        if not project_instance.project_config_file_path.exists():
            logger.error(f"项目配置文件不存在: {project_instance.project_config_file_path}")
            template_path = project_instance.project_config_file_path.with_suffix(project_instance.project_config_file_path.suffix + '.template')
            if template_path.exists():
                logger.info(f"请参考模板文件 {template_path} 创建您的配置文件。")
            return
        logger.info("项目配置文件加载成功。")

        # 2. 验证配置内容
        if not project_instance.config_manager.validate_config():
            logger.error("项目配置验证失败。请检查配置文件中的错误。")
            return
        logger.info("项目配置验证通过。")

        # 3. 检查数据和日志目录
        project_instance.ensure_project_dirs()
        logger.info("项目所需的数据和日志目录已确认存在。")

        # 4. （可选）初始化数据库
        if init_db:
            logger.info("开始从JSON文件初始化数据库...")
            try:
                data_manager = project_instance.get_data_manager(db_name=db_name)
                result = data_manager.initialize_database_from_json(clear_existing=clear_existing)
                logger.info(f"数据库初始化完成! 作者: {result['authors']}, 诗词: {result['poems']}")
            except Exception as e:
                logger.error(f"数据库初始化失败: {e}", exc_info=True)
                return
        
        logger.info(f"项目 '{project_instance.name}' 环境设置完成！")
        
    except Exception as e:
        logger.error(f"项目设置失败: {e}", exc_info=True)


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
@click.pass_context
def annotate(ctx, models, limit, id_range, force_rerun):
    """启动一个或多个模型的并发标注任务"""
    try:
        project_instance = ctx.obj['project_instance']
        
        logger.info("启动多模型并发标注任务...")
        logger.info(f"任务参数 - 模型: {models or '未指定'}, 限制: {limit or '无'}, 范围: {id_range or '全部'}, 强制重跑: {force_rerun}")
        
        asyncio.run(run_multi_model_annotation(models, limit, id_range, force_rerun, project_instance))
        
        logger.info("标注任务执行完成")
    except Exception as e:
        logger.error(f"标注任务执行失败: {e}", exc_info=True)

@cli.command()
@click.pass_context
def status(ctx):
    """显示标注进度统计 (按模型配置)"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']
        
        logger.info("获取标注进度统计...")
        data_manager_instance = project_instance.get_data_manager(db_name=db_name)
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
@click.pass_context
def export(ctx, output_format, output, model_filter):
    """导出标注结果"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']
        
        if model_filter:
            logger.info(f"导出模型配置 [{model_filter}] 的标注结果，格式: {output_format}")
        else:
            logger.info(f"导出所有已完成的标注结果，格式: {output_format}")
        
        data_manager_instance = project_instance.get_data_manager(db_name=db_name)
        output_file = data_manager_instance.export_results(
            output_format=output_format,
            output_file=output,
            model_filter=model_filter
        )
        
        logger.info(f"结果已导出到: {output_file}")
        
    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)


@cli.command(name="list-models")
@click.pass_context
def list_models(ctx):
    """列出在config.ini中已配置的模型"""
    try:
        project_instance = ctx.obj['project_instance']
        
        logger.info("获取已配置的模型列表...")
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
