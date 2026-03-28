"""
CLI 命令定义 - 使用 Click 框架
"""

import click
import asyncio
import sys
import configparser
from pathlib import Path
from typing import Optional, Tuple
import logging

from .project import Project
from .config import ConfigManager
from .logging_config import setup_default_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default=None,
              help='设置日志级别（可选，将覆盖配置文件设置）')
@click.option('--log-file', help='指定日志文件路径（可选，将覆盖配置文件设置）')
@click.option('--enable-file-log', is_flag=True, default=None,
              help='启用文件日志输出（可选，将覆盖配置文件设置）')
@click.option('--project', type=str, help='项目名称 (可选，默认使用全局配置中的激活项目)')
@click.option('--db-name', type=str, default="default", help='数据库名称（从项目配置文件中获取路径，默认为 "default"）')
@click.pass_context
def cli(ctx, log_level, log_file, enable_file_log, project, db_name):
    """LLM 诗词情感标注工具"""
    global_config_path = Path(__file__).parent.parent / "config" / "config.ini"

    if not project:
        try:
            global_config = ConfigManager([str(global_config_path)])
            active_project_config_path = global_config.config.get('Project', 'active_project_config')
            project = Path(active_project_config_path).parent.name
            print(f"未指定项目，将使用激活项目：{project}")
        except (configparser.NoSectionError, configparser.NoOptionError, IndexError) as e:
            print(f"错误：无法从全局配置中确定激活项目：{e}")
            print("请使用 --project <项目名称> 参数指定一个项目。")
            sys.exit(1)

    project_instance = Project(project_name=project, project_root_dir=Path("projects"), global_config_path=global_config_path)
    ctx.obj = {'project_instance': project_instance, 'db_name': db_name}

    try:
        project_instance.setup_project_logging()
    except Exception as e:
        setup_default_logging(
            console_level=log_level,
            enable_file_log=enable_file_log,
            log_file=log_file,
            global_config_path=global_config_path
        )
        logger.warning(f"使用默认日志配置，因为项目日志配置失败：{e}")

    logger.info("=" * 60)
    logger.info(f"LLM 诗词情感标注工具启动 (项目：{project})")
    logger.info(f"项目根目录：{project_instance.root_path}")
    logger.info("=" * 60)


@cli.command()
@click.option('--init-db', is_flag=True, help='初始化数据库（从 JSON 文件加载数据）')
@click.option('--clear-existing', is_flag=True, help='清空现有数据后重新初始化')
@click.pass_context
def setup(ctx, init_db, clear_existing):
    """初始化或检查当前激活项目的环境"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']

        logger.info(f"开始检查和设置项目 '{project_instance.name}' 的环境...")

        if not project_instance.project_config_file_path.exists():
            logger.error(f"项目配置文件不存在：{project_instance.project_config_file_path}")
            return
        logger.info("项目配置文件加载成功。")

        if not project_instance.config_manager.validate_config():
            logger.error("项目配置验证失败。")
            return
        logger.info("项目配置验证通过。")

        project_instance.ensure_project_dirs()
        logger.info("项目所需的数据和日志目录已确认存在。")

        if init_db:
            logger.info("开始从 JSON 文件初始化数据库...")
            try:
                data_manager = project_instance.get_data_manager(db_name=db_name)
                result = data_manager.initialize_database_from_json(clear_existing=clear_existing)
                logger.info(f"数据库初始化完成！作者：{result['authors']}, 诗词：{result['poems']}")
            except Exception as e:
                logger.error(f"数据库初始化失败：{e}", exc_info=True)
                return

        logger.info(f"项目 '{project_instance.name}' 环境设置完成！")

    except Exception as e:
        logger.error(f"项目设置失败：{e}", exc_info=True)


async def run_multi_model_annotation(models: Tuple[str], limit: Optional[int], id_range: Optional[str],
                                     force_rerun: bool, project_instance: Project):
    """异步调度器，用于运行多模型标注任务"""
    start_id, end_id = None, None
    if id_range:
        try:
            start_id, end_id = map(int, id_range.split(':'))
            logger.info(f"标注范围：{start_id} - {end_id}")
        except ValueError:
            logger.error("范围格式错误，请使用 'start:end' 格式")
            return

    if not models:
        logger.error("必须指定至少一个模型配置。请使用 --model 选项指定模型配置别名。")
        return

    target_models = list(models)
    logger.info(f"将要执行标注任务的模型配置：{target_models}")

    batch_logger = logger
    batch_logger.info(f"开始新的标注批次任务 - 模型：{target_models}")

    tasks = []
    for model_alias in target_models:
        try:
            logger.info(f"创建模型配置 '{model_alias}' 的标注器...")
            annotator = project_instance.get_annotator(config_name=model_alias)
            task = annotator.run(
                limit=limit,
                start_id=start_id,
                end_id=end_id,
                force_rerun=force_rerun
            )
            tasks.append(task)
            logger.info(f"模型配置 '{model_alias}' 的标注任务已创建")
        except Exception as e:
            logger.error(f"创建模型配置 '{model_alias}' 的标注器失败：{e}")

    if not tasks:
        logger.warning("没有可执行的标注任务。")
        return

    logger.info(f"开始并发执行 {len(tasks)} 个标注任务...")
    results = await asyncio.gather(*tasks)

    total_completed, total_failed = 0, 0
    logger.info("\n=== 多模型标注任务最终报告 ===")
    for res in results:
        logger.info(f"模型配置 [{res['model']}]: 总计={res['total']}, 成功={res['completed']}, 失败={res['failed']}")
        total_completed += res.get('completed', 0)
        total_failed += res.get('failed', 0)
    logger.info("---------------------------------")
    logger.info(f"所有模型总计：成功={total_completed}, 失败={total_failed}")
    logger.info("=================================")


@cli.command()
@click.option('--model', 'models', multiple=True, help="指定一个或多个模型配置别名")
@click.option('--limit', type=int, help='限制每个模型本次标注的数量')
@click.option('--range', 'id_range', help='按 ID 范围进行标注 (例如：1:100)')
@click.option('--force-rerun', is_flag=True, help='强制重新标注已完成的条目')
@click.pass_context
def annotate(ctx, models, limit, id_range, force_rerun):
    """启动一个或多个模型的并发标注任务"""
    try:
        project_instance = ctx.obj['project_instance']
        logger.info("启动多模型并发标注任务...")
        asyncio.run(run_multi_model_annotation(models, limit, id_range, force_rerun, project_instance))
        logger.info("标注任务执行完成")
    except Exception as e:
        logger.error(f"标注任务执行失败：{e}", exc_info=True)


@cli.command()
@click.pass_context
def status(ctx):
    """显示标注进度统计"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']

        logger.info("获取标注进度统计...")
        data_manager_instance = project_instance.get_data_manager(db_name=db_name)
        stats = data_manager_instance.get_statistics()

        print("\n=== 标注进度统计 ===")
        print(f"总诗词数量：{stats.get('total_poems', 0)}")
        print(f"总作者数量：{stats.get('total_authors', 0)}")

        if not stats.get('stats_by_model'):
            print("\n尚未有任何模型的标注记录。")
            return

        print("\n--- 按模型配置统计 ---")
        for model, model_stats in stats['stats_by_model'].items():
            completed = model_stats.get('completed', 0)
            failed = model_stats.get('failed', 0)
            total = completed + failed
            completion_rate = (completed / stats['total_poems'] * 100) if stats['total_poems'] > 0 else 0

            print(f"\n模型配置：{model}")
            print(f"  - 已标注：{total} / {stats['total_poems']} ({completion_rate:.2f}%)")
            print(f"  - 成功：{completed}")
            print(f"  - 失败：{failed}")

    except Exception as e:
        logger.error(f"获取统计信息失败：{e}", exc_info=True)


@cli.command()
@click.option('--format', 'output_format', default='jsonl', type=click.Choice(['jsonl', 'json']), help='输出格式')
@click.option('--output', help='输出文件路径')
@click.option('--model', 'model_filter', help='只导出指定模型配置的标注结果')
@click.pass_context
def export(ctx, output_format, output, model_filter):
    """导出标注结果"""
    try:
        project_instance = ctx.obj['project_instance']
        db_name = ctx.obj['db_name']

        data_manager_instance = project_instance.get_data_manager(db_name=db_name)
        output_file = data_manager_instance.export_results(
            output_format=output_format,
            output_file=output,
            model_filter=model_filter
        )

        logger.info(f"结果已导出到：{output_file}")

    except Exception as e:
        logger.error(f"导出失败：{e}", exc_info=True)


@cli.command(name="list-models")
@click.pass_context
def list_models(ctx):
    """列出在 config.ini 中已配置的模型"""
    try:
        project_instance = ctx.obj['project_instance']
        llm_factory_instance = project_instance.llm_factory
        configured_models = llm_factory_instance.list_configured_models()

        print("\n=== 已配置的模型 ===")
        if not configured_models:
            print("⚠️ 没有在 config.ini 中找到任何 [Model.*] 配置。")
        else:
            for name, details in configured_models.items():
                print(f"  - {name}")
                print(f"    - provider: {details.get('provider')}")
                print(f"    - model_name: {details.get('model_name')}")

    except Exception as e:
        logger.error(f"获取已配置模型列表失败：{e}", exc_info=True)
