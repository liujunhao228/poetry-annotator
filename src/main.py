import click
import asyncio
import sys
from pathlib import Path
from typing import Optional, Tuple
import logging
from .config_manager import config_manager
from .data_manager import data_manager
from .label_parser import label_parser
from .llm_factory import llm_factory
from .annotator import Annotator
from .logging_config import setup_default_logging, get_logger


# 获取主日志记录器
logger = get_logger(__name__)


@click.group()
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default=None,  # 改为None，优先使用配置文件
              help='设置日志级别（可选，将覆盖配置文件设置）')
@click.option('--log-file', help='指定日志文件路径（可选，将覆盖配置文件设置）')
@click.option('--enable-file-log', is_flag=True, default=None, 
              help='启用文件日志输出（可选，将覆盖配置文件设置）')
def cli(log_level, log_file, enable_file_log):
    """LLM诗词情感标注工具"""
    # 设置日志配置 - 优先使用配置文件，CLI参数可覆盖
    try:
        config = config_manager.get_logging_config()
        setup_default_logging(
            log_level=log_level or config['log_level'],
            enable_file_log=enable_file_log if enable_file_log is not None else config['enable_file_log'],
            log_file=log_file or config['log_file']
        )
    except Exception as e:
        # 如果配置文件有问题，使用CLI参数或默认值
        setup_default_logging(log_level, enable_file_log, log_file)
    
    # 记录启动信息
    logger.info("=" * 60)
    logger.info("LLM诗词情感标注工具启动")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")
    logger.info(f"日志级别: {logging.getLevelName(logger.level)}")
    logger.info("=" * 60)


@cli.command()
@click.option('--config', default='config/config.ini', help='配置文件路径')
@click.option('--init-db', is_flag=True, help='初始化数据库（从JSON文件加载数据）')
@click.option('--clear-existing', is_flag=True, help='清空现有数据后重新初始化')
def setup(config, init_db, clear_existing):
    """初始化项目环境"""
    try:
        logger.info("开始初始化项目环境...")
        
        # 检查配置文件
        config_path = Path(config)
        if not config_path.exists():
            template_path = config_path.with_suffix('.ini.template')
            logger.info(f"配置文件 {config} 不存在，自行从模板创建...")
            logger.info(f"请复制 {template_path} 为 {config} 并配置您的API密钥。")
            return

        config_manager.config_path = config
        config_manager._load_config()
        logger.info("配置文件加载成功")
        
        # 记录配置信息
        try:
            llm_config = config_manager.get_llm_config()
            logger.info(f"LLM配置 - 并发数: {llm_config.get('max_workers')}")
            
            db_config = config_manager.get_database_config()
            logger.info(f"数据库配置 - 路径: {db_config.get('db_path')}")
            
            data_config = config_manager.get_data_config()
            logger.info(f"数据配置 - 源目录: {data_config.get('source_dir')}, 输出目录: {data_config.get('output_dir')}")
            
        except Exception as e:
            logger.warning(f"配置信息记录失败: {e}")
        
        if init_db:
            logger.info("开始从JSON文件初始化数据库...")
            try:
                result = data_manager.initialize_database_from_json(clear_existing=clear_existing)
                logger.info(f"数据库初始化完成! 作者: {result['authors']}, 诗词: {result['poems']}")
            except Exception as e:
                logger.error(f"数据库初始化失败: {e}")
                return
        
        logger.info("项目环境初始化完成！")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)


async def run_multi_model_annotation(models: Tuple[str], limit: Optional[int], id_range: Optional[str], force_rerun: bool):
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

    # 为每个模型创建并运行一个标注任务
    tasks = []
    for model_alias in target_models:
        try:
            logger.info(f"创建模型配置 '{model_alias}' 的标注器...")
            annotator = Annotator(config_name=model_alias)
            task = annotator.run(
                limit=limit,
                start_id=start_id,
                end_id=end_id,
                force_rerun=force_rerun
            )
            tasks.append(task)
            logger.info(f"模型配置 '{model_alias}' 的标注任务已创建")
        except Exception as e:
            logger.error(f"创建模型配置 '{model_alias}' 的标注器失败: {e}")
    
    if not tasks:
        logger.warning("没有可执行的标注任务。")
        return

    # 并发执行所有模型任务
    logger.info(f"开始并发执行 {len(tasks)} 个标注任务...")
    results = await asyncio.gather(*tasks)

    # 汇总并打印最终报告
    total_completed, total_failed = 0, 0
    logger.info("\n=== 多模型标注任务最终报告 ===")
    for res in results:
        logger.info(
            f"模型配置 [{res['model']}]: "
            f"总计={res['total']}, 成功={res['completed']}, 失败={res['failed']}"
        )
        total_completed += res.get('completed', 0)
        total_failed += res.get('failed', 0)
    logger.info("---------------------------------")
    logger.info(f"所有模型总计: 成功={total_completed}, 失败={total_failed}")
    logger.info("=================================")


@cli.command()
@click.option('--model', 'models', multiple=True, help="指定一个或多个模型配置别名 (例如 'gpt-4o'), 可多次使用此选项。")
@click.option('--limit', type=int, help='限制每个模型本次标注的数量')
@click.option('--range', 'id_range', help='按ID范围进行标注 (例如: 1:100)')
@click.option('--force-rerun', is_flag=True, help='强制重新标注已完成的条目')
def annotate(models, limit, id_range, force_rerun):
    """启动一个或多个模型的并发标注任务"""
    try:
        logger.info("启动多模型并发标注任务...")
        
        # 记录任务参数
        logger.info(f"任务参数 - 模型: {models or '未指定'}, 限制: {limit or '无'}, 范围: {id_range or '全部'}, 强制重跑: {force_rerun}")
        
        asyncio.run(run_multi_model_annotation(models, limit, id_range, force_rerun))
        
        logger.info("标注任务执行完成")
    except Exception as e:
        logger.error(f"标注任务执行失败: {e}", exc_info=True)

@cli.command()
def status():
    """显示标注进度统计 (按模型配置)"""
    try:
        logger.info("获取标注进度统计...")
        stats = data_manager.get_statistics()
        
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
        if model_filter:
            logger.info(f"导出模型配置 [{model_filter}] 的标注结果，格式: {output_format}")
        else:
            logger.info(f"导出所有已完成的标注结果，格式: {output_format}")
        
        output_file = data_manager.export_results(
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
        logger.info("获取已配置的模型列表...")
        configured_models = llm_factory.list_configured_models()
        
        print("\n=== 已配置的模型 ===")
        if not configured_models:
            print("⚠️  没有在 config.ini 中找到任何 [Model.*] 配置。")
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


if __name__ == '__main__':
    cli() 