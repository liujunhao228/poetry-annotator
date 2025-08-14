import click
import asyncio
import sys
from pathlib import Path
from typing import Optional, Tuple
import logging
import os

# 处理相对导入问题
# 优先尝试相对导入（当作为包的一部分被导入时）
relative_import_failed = False
try:
    # 当作为包运行时（推荐方式）
    from .config_manager import config_manager
    from .data_manager import get_data_manager
    from .label_parser import label_parser
    from .llm_factory import llm_factory
    from .annotator import Annotator
    from .logging_config import setup_default_logging, get_logger
except ImportError as e:
    relative_import_failed = True
    print(f"相对导入失败: {e}")

# 如果相对导入失败，则尝试绝对导入
if relative_import_failed:
    # 当直接运行时（兼容开发环境）
    # 确保 src 目录在 sys.path 中，以便绝对导入可以找到 src 下的模块
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"已将 {src_dir} 添加到 sys.path")
        
    try:
        from config_manager import config_manager
        from data_manager import get_data_manager
        from label_parser import label_parser
        from llm_factory import llm_factory
        from annotator import Annotator
        from logging_config import setup_default_logging, get_logger
    except ImportError as e:
        print(f"绝对导入也失败了: {e}")
        raise # Re-raise the exception to stop execution


# 获取主日志记录器
logger = get_logger(__name__)


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
@click.option('--db-name', type=str, help='数据库名称（从配置文件中获取路径）')
def cli(log_level, log_file, enable_file_log, db_name):
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
    
    # 设置数据库
    if db_name:
        try:
            get_data_manager(db_name=db_name)
        except ValueError as e:
            logger.error(f"数据库设置错误: {e}")
            return
    
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
        
        # 确保情感分类体系是最新的（从Markdown文件生成XML文件）
        try:
            logger.info("检查情感分类体系文件...")
            categories_config = config_manager.get_categories_config()
            xml_path = categories_config.get('xml_path')
            md_path = categories_config.get('md_path')
            
            if xml_path and md_path:
                xml_file = Path(xml_path)
                md_file = Path(md_path)
                
                # 如果Markdown文件存在且比XML文件新，或者XML文件不存在，则重新生成XML
                if md_file.exists() and (not xml_file.exists() or md_file.stat().st_mtime > xml_file.stat().st_mtime):
                    logger.info(f"检测到Markdown文件更新，正在重新生成XML文件...")
                    # 重新创建label_parser实例以触发解析和生成
                    from .label_parser import LabelParser
                    LabelParser()  # 初始化时会自动处理Markdown到XML的转换
                    logger.info("情感分类体系XML文件已更新")
                elif xml_file.exists():
                    logger.info("情感分类体系XML文件已是最新")
                else:
                    logger.warning("未找到情感分类体系文件（Markdown或XML）")
            else:
                logger.warning("未配置情感分类体系文件路径")
        except Exception as e:
            logger.warning(f"情感分类体系文件检查失败: {e}")
        
        if init_db:
            logger.info("开始从JSON文件初始化数据库...")
            try:
                # 使用新的多数据库初始化方法
                results = data_manager.initialize_all_databases_from_source_folders(clear_existing=clear_existing)
                logger.info("所有数据库初始化完成!")
                for folder_name, result in results.items():
                    logger.info(f"数据库 [{folder_name}]: 作者: {result['authors']}, 诗词: {result['poems']}")
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

    # 不再创建批次日志记录器，直接使用全局日志记录器
    batch_logger = logger
    batch_logger.info(f"开始新的标注批次任务 - 模型: {target_models}, 范围: {id_range or '全部'}")

    # 为每个模型创建并运行一个标注任务
    tasks = []
    for model_alias in target_models:
        try:
            logger.info(f"创建模型配置 '{model_alias}' 的标注器...")
            # 不再设置环境变量用于批次日志
            annotator = Annotator(config_name=model_alias)
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
