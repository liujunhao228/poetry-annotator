#!/usr/bin/env python3
"""
诗词标注任务分发工具
用于从文件读取诗词ID并分发标注任务，支持多模型、高并发。
支持传入单个列表文件或包含多个列表文件的目录，并可将目录内文件与模型顺序匹配。

【新日志系统适配说明】
此版本已适配新的分层日志系统 (控制台INFO, 文件DEBUG)。
- 增加了 `--console-log-level`, `--file-log-level`, `--enable-file-log` 命令行参数。
- 这些参数可以覆盖 config.ini 中的设置，方便从命令行或GUI进行精细化控制。
- 脚本内的日志记录遵循新规范：
  - `logger.info()` 用于用户可见的关键进度更新。
  - `logger.debug()` 用于详细的内部状态和调试信息，仅记录于文件。
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

# 获取当前脚本的绝对路径
script_dir = Path(__file__).resolve().parent
# 获取项目根目录
project_root = script_dir.parent
# 将项目根目录添加到 sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import click
import asyncio
import time
import json
import hashlib
from typing import List, Tuple, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# [修改] 导入新的日志配置模块
from src.config import config_manager
from src.data import get_data_manager
from src.annotator import Annotator
from src.logging_config import setup_default_logging, get_logger
from src.utils.health_checker import health_checker
from src.llm_factory import llm_factory
from src.plugin_system.manager import get_plugin_manager
from src.plugin_system.project_config_manager import ProjectPluginConfigManager
from src.plugin_system.loader import PluginLoader

logger = get_logger(__name__)


class ProgressManager:
    """管理任务进度的类"""
    def __init__(self, model_name: str, id_file_path: str):
        self.state_dir = Path(".progress_cache")
        self.state_dir.mkdir(exist_ok=True)
      
        resolved_id_file_path = str(Path(id_file_path).resolve())
        id_file_hash = hashlib.md5(resolved_id_file_path.encode('utf-8')).hexdigest()
        
        self.state_file = self.state_dir / f"state_{model_name}_{id_file_hash}.json"
        self.backup_file = self.state_dir / f"state_{model_name}_{id_file_hash}.backup.json"
      
        # 使用 DEBUG 级别记录详细路径，不会在控制台刷屏
        logger.debug(f"使用进度文件: {self.state_file} (基于ID文件: {id_file_path})")

    def load_state(self) -> dict:
        """加载进度。如果文件不存在或无效，返回默认值。"""
        # 首先尝试加载主进度文件
        if self.state_file.exists():
            state = self._load_state_file(self.state_file)
            if state:
                return state
        
        # 如果主进度文件不存在或无效，尝试加载备份文件
        if self.backup_file.exists():
            logger.warning(f"主进度文件无效或不存在，尝试加载备份文件: {self.backup_file}")
            state = self._load_state_file(self.backup_file)
            if state:
                # 将备份文件恢复为主文件
                try:
                    self.backup_file.rename(self.state_file)
                    logger.info(f"已从备份文件恢复进度: {self.state_file}")
                    return state
                except OSError as e:
                    logger.error(f"无法从备份文件恢复进度: {e}")
        
        # 如果都没有有效的进度文件
        logger.info(f"为任务 [{Path(self.state_file).stem}] 未发现有效的进度文件，将从头开始。")
        return self._default_state()

    def _load_state_file(self, file_path: Path) -> Optional[dict]:
        """从指定文件加载进度状态"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # 验证状态文件的基本结构
                required_keys = ['last_completed_chunk_index', 'total_processed_count', 
                               'total_success_count', 'total_failed_count']
                if all(key in state for key in required_keys):
                    logger.info(f"进度加载成功: {state}")
                    return state
                else:
                    raise KeyError(f"进度文件缺少必要字段: {required_keys}")
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"无法解析进度文件或格式错误: {e}。文件: {file_path}")
            return None

    def save_state(self, state: dict):
        """保存进度状态，包含备份机制"""
        try:
            # 先创建备份（如果主文件存在）
            if self.state_file.exists():
                self.state_file.replace(self.backup_file)
            
            # 写入新的状态文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            
            # 频繁的保存操作使用 DEBUG 级别
            logger.debug(f"进度已保存: {state}")
        except OSError as e:
            logger.error(f"保存进度文件失败: {e}")

    def clear_state(self):
        """清除进度文件和备份文件"""
        cleared_files = []
        for file_path in [self.state_file, self.backup_file]:
            if file_path.exists():
                try:
                    os.remove(file_path)
                    cleared_files.append(str(file_path))
                except OSError as e:
                    logger.error(f"清除进度文件失败: {e}")
        
        if cleared_files:
            logger.info(f"已清除旧的进度文件: {', '.join(cleared_files)}")

    def mark_task_completed(self):
        """标记任务完成，清理进度文件"""
        self.clear_state()
        logger.info("任务已完成，进度文件已清理。")

    def _default_state(self) -> dict:
        return {
            "last_completed_chunk_index": -1,
            "total_processed_count": 0,
            "total_success_count": 0,
            "total_failed_count": 0,
            "total_duration_so_far": 0.0
        }


def read_poem_ids_in_chunks(file_path: str, chunk_size: int):
    """从文件中分块读取诗词ID，作为生成器"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ID文件不存在: {file_path}")
  
    with open(path, 'r', encoding='utf-8') as f:
        chunk = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                chunk.append(int(line))
                if len(chunk) == chunk_size:
                    yield chunk
                    chunk = []
            except ValueError:
                logger.warning(f"忽略文件 '{file_path}' 中非整数的行: '{line}'")
        if chunk:
            yield chunk


def process_chunk(args: Tuple[str, List[int], bool, bool, bool, str, str]) -> Dict[str, Any]:
    """
    【内层并发单元】工作线程执行的函数，处理一个批次的ID。
    """
    model_name, poem_ids_chunk, force_rerun, dry_run, full_dry_run, output_dir, source_dir = args
    thread_ident = threading.get_ident()
    logger.debug(f"线程 {thread_ident} 开始为模型 '{model_name}' 处理 {len(poem_ids_chunk)} 个ID的批次。")

    # 如果是 dry_run 模式但不是 full_dry_run，则执行模拟处理并返回
    if dry_run and not full_dry_run:
        logger.info(f"[Dry Run - Simulated] 模拟处理模型 '{model_name}' 的 {len(poem_ids_chunk)} 个ID。")
        time.sleep(0.1)  # 模拟少量I/O延迟
        # 模拟成功和失败的情况
        num_failed = len(poem_ids_chunk) // 10  # 模拟10%的失败率
        num_completed = len(poem_ids_chunk) - num_failed
        return {
            'total': len(poem_ids_chunk),
            'completed': num_completed,
            'failed': num_failed,
            'skipped': 0,
            'dry_run': True
        }

    # 否则（非 dry_run 或 full_dry_run 模式），实例化 Annotator 并运行
    try:
        annotator = Annotator(model_name, output_dir=output_dir, source_dir=source_dir, dry_run=dry_run, full_dry_run=full_dry_run)
        results = asyncio.run(annotator.run(poem_ids=poem_ids_chunk, force_rerun=force_rerun))
        # logger.debug(f"线程 {thread_ident} 完成为模型 '{model_name}' 处理批次。")
        return results
    except Exception as e:
        logger.error(f"线程池任务在处理模型 '{model_name}' 的批次时失败: {e}", exc_info=True)
        return {
            'total': len(poem_ids_chunk),
            'completed': 0,
            'failed': len(poem_ids_chunk),
            'error': str(e)
        }


def run_annotation_for_model(model: str, id_file: str, force_rerun: bool, chunk_size: int, fresh_start: bool, max_workers: int, output_dir: str, source_dir: str, dry_run: bool = False, full_dry_run: bool = False):
    """
    【外层并发单元】为单个指定模型和单个ID文件运行完整的并行标注流程。
    """
    # 设置环境变量，供日志系统使用
    import os
    os.environ['ANNOTATION_MODEL_NAME'] = model
    os.environ['ANNOTATION_ID_FILE'] = Path(id_file).stem  # 使用文件名而不是完整路径
    
    # 初始化批次日志记录器（已移除对不存在模块的依赖）
    # 直接使用全局日志记录器记录批次任务信息
    logger.info(f"开始新的批次任务 - 模型: {model}, ID文件: {Path(id_file).name}")
    
    if dry_run:
        logger.info("********** DRY RUN 模式已激活 **********")
        logger.info("将跳过实际的LLM标注调用，仅测试流程。")

    logger.info("=" * 60)
    logger.info(f"启动任务流水线 -> 模型: [{model}], ID文件: [{Path(id_file).name}]")
    logger.info(f"任务将使用 {max_workers} 个内部工作线程处理数据块。")
    logger.debug(f"完整ID文件路径: [{id_file}]") # 详细路径用 DEBUG
    logger.info("=" * 60)

    progress_manager = ProgressManager(model, id_file)
    if fresh_start:
        progress_manager.clear_state()
  
    state = progress_manager.load_state()
    last_completed_chunk_index = state['last_completed_chunk_index']
    total_processed_count = state['total_processed_count']
    total_success_count = state['total_success_count']
    total_failed_count = state['total_failed_count']
    total_duration_so_far = state.get('total_duration_so_far', 0.0)
  
    start_time_current_run = time.time()
    task_completed_successfully = False
  
    try:
        id_chunks = list(read_poem_ids_in_chunks(id_file, chunk_size))
        if not id_chunks:
            logger.warning(f"ID文件 '{id_file}' 为空或不包含有效ID。跳过此任务。")
            return

        chunks_to_process = id_chunks[last_completed_chunk_index + 1:]
      
        if not chunks_to_process:
            logger.info(f"对于模型 [{model}] 和文件 [{Path(id_file).name}]，所有批次都已处理完毕，任务结束。")
            task_completed_successfully = True
            return
          
        logger.info(f"总共有 {len(id_chunks)} 个批次，将从批次 {last_completed_chunk_index + 2} 开始处理 {len(chunks_to_process)} 个批次。")
      
        task_args = [(model, chunk, force_rerun, dry_run, full_dry_run, output_dir, source_dir) for chunk in chunks_to_process]
      
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"{model[:10]}_worker") as executor:
            results_iterator = executor.map(process_chunk, task_args)
          
            for i, results in enumerate(results_iterator):
                current_chunk_index = last_completed_chunk_index + 1 + i
              
                if not results or 'error' in results:
                    chunk_len = len(chunks_to_process[i])
                    processed = results.get('total', chunk_len)
                    completed = results.get('completed', 0)
                    failed = results.get('failed', chunk_len)
                    error_msg = results.get('error', '未知线程错误')
                    logger.error(f"模型 [{model}] 处理批次 {current_chunk_index + 1} 时发生错误: {error_msg}")
                else:
                    processed = results.get('total', 0)
                    completed = results.get('completed', 0)
                    failed = results.get('failed', 0)
                    # 这是用户最关心的进度信息，使用 INFO
                    logger.info(f"模型 [{model}] 的批次 {current_chunk_index + 1}/{len(id_chunks)} 处理完成。成功: {completed}, 失败: {failed}")
              
                total_processed_count += processed
                total_success_count += completed
                total_failed_count += failed
              
                current_run_duration = time.time() - start_time_current_run
                state = {
                    "last_completed_chunk_index": current_chunk_index,
                    "total_processed_count": total_processed_count,
                    "total_success_count": total_success_count,
                    "total_failed_count": total_failed_count,
                    "total_duration_so_far": total_duration_so_far + current_run_duration
                }
                progress_manager.save_state(state)
                logger.debug(f"模型 [{model}] 的进度已更新至批次 {current_chunk_index + 1}。")

                # 检查是否所有批次都已完成
                if current_chunk_index + 1 == len(id_chunks):
                    task_completed_successfully = True

    except FileNotFoundError as e:
        logger.error(f"任务 [{model}]-[{Path(id_file).name}] 失败: 读取ID文件时出错: {e}")
        return
    except Exception as e:
        logger.error(f"任务 [{model}]-[{Path(id_file).name}] 失败: 发生未知错误: {e}", exc_info=True)
        return
    finally:
        # 如果任务成功完成，清理进度文件
        if task_completed_successfully:
            progress_manager.mark_task_completed()

    end_time = time.time()
    total_duration_this_run = end_time - start_time_current_run
    final_total_duration = total_duration_so_far + total_duration_this_run

    logger.info("-" * 60)
    logger.info(f"任务流水线完成 -> 模型: [{model}], ID文件: [{Path(id_file).name}]")
    logger.info(f"本次运行耗时: {total_duration_this_run:.2f} 秒")
    logger.info(f"累计总耗时: {final_total_duration:.2f} 秒")
    logger.info(f"总处理ID数: {total_processed_count}")
    logger.info(f"总成功: {total_success_count}")
    logger.info(f"总失败: {total_failed_count}")
    logger.info("-" * 60)


def run_distribution_task(
    model: Optional[str] = None,
    all_models: bool = False,
    id_file: Optional[str] = None,
    id_dir: Optional[str] = None,
    force_rerun: bool = False,
    chunk_size: int = 1000,
    fresh_start: bool = False,
    output_dir: str = "",
    source_dir: str = "",
    console_log_level: Optional[str] = None,
    file_log_level: Optional[str] = None,
    enable_file_log: Optional[bool] = None,
    dry_run: bool = False,
    full_dry_run: bool = False # 新增参数
) -> Dict[str, Any]:
    """
    【模块化入口函数】执行诗词标注任务分发。
    此函数不依赖Click，可被其他Python模块（如GUI）直接导入和调用。

    :param model: 指定模型别名。
    :param all_models: 是否对所有模型执行。
    :param id_file: 单个ID文件路径。
    :param id_dir: 包含ID文件的目录路径。
    :param force_rerun: 强制重新标注。
    :param chunk_size: 批次大小。
    :param fresh_start: 清除进度从头开始。
    :param output_dir: 项目输出目录，用于派生项目名称和数据库路径。
    :param source_dir: 数据源目录。
    :param console_log_level: 控制台日志级别。
    :param file_log_level: 文件日志级别。
    :param enable_file_log: 是否启用文件日志。
    :param dry_run: 空运行模式，测试流程而不调用LLM。
    :return: 一个包含执行结果摘要的字典。
    :raises ValueError: 如果参数组合无效。
    """
    # 1. 日志和数据库设置
    setup_default_logging(
        console_level=console_log_level,
        file_level=file_log_level,
        enable_file_log=enable_file_log
    )
    
    # 移除对 db 参数的直接处理，因为现在通过 output_dir 和 source_dir 间接管理
    # if db:
    #     try:
    #         get_data_manager(db_name=db)
    #     except ValueError as e:
    #         logger.error(f"数据库设置错误: {e}")
    #         raise  # 向上抛出异常

    # 2. 初始化插件系统
    logger.info("初始化插件系统...")
    global_plugin_manager = get_plugin_manager()
    project_plugin_config_manager = ProjectPluginConfigManager(project_root)
    PluginLoader.load_plugins_from_config(project_plugin_config_manager, global_plugin_manager, str(project_root))
    global_plugin_manager.initialize_all_plugins()
    logger.info("插件系统初始化完成。")

    script_start_time = time.time()

    # 3. 参数校验
    if not model and not all_models:
        raise ValueError("错误: 必须提供 'model' 或 'all_models' 参数之一。")
    if model and all_models:
        raise ValueError("错误: 'model' 和 'all_models' 参数是互斥的。")
    if not id_file and not id_dir:
        raise ValueError("错误: 必须提供 'id_file' 或 'id_dir' 参数之一。")
    if id_file and id_dir:
        raise ValueError("错误: 'id_file' 和 'id_dir' 参数是互斥的。")

    available_models = llm_factory.list_configured_models().keys()
    if not available_models:
        raise ValueError("错误: 配置文件中没有找到任何 [Model.*] 配置。")

    models_to_run = list(available_models) if all_models else [model]
    if not all(m in available_models for m in models_to_run):
        raise ValueError(f"错误: 指定模型不在配置中。请求: {models_to_run}, 可用: {list(available_models)}")

    # 3. 健康检查
    if not asyncio.run(health_checker.run_all_checks(models_to_run)):
        msg = "任务因健康检查失败而中止。"
        logger.critical(msg)
        raise RuntimeError(msg)

    # 4. 确定任务列表
    tasks_to_distribute: List[Tuple[str, str]] = []
    if id_file:
        tasks_to_distribute = [(model_name, id_file) for model_name in models_to_run]
    elif id_dir:
        id_files_in_dir = sorted([str(p.resolve()) for p in Path(id_dir).glob('*.txt') if p.is_file()])
        if not id_files_in_dir:
            raise FileNotFoundError(f"错误: 目录 '{id_dir}' 中没有找到任何 .txt 文件。")
        if len(models_to_run) > 1 and len(models_to_run) != len(id_files_in_dir):
            raise ValueError(f"错误: 当指定多个模型时，模型数量 ({len(models_to_run)}) 与 .txt 文件数量 ({len(id_files_in_dir)}) 必须匹配。")
        
        if len(models_to_run) == 1 and len(id_files_in_dir) > 1:
             # 一个模型对一个目录，处理目录下所有文件
            tasks_to_distribute = [(models_to_run[0], f) for f in id_files_in_dir]
        else: # 模型和文件一对一匹配
            tasks_to_distribute = list(zip(models_to_run, id_files_in_dir))


    # 5. 获取并发设置
    try:
        llm_config = config_manager.get_llm_config()
        max_workers = llm_config.get('max_workers', 1)
        max_model_pipelines = llm_config.get('max_model_pipelines', 1)
    except Exception as e:
        logger.warning(f"从配置加载并发设置失败: {e}。将使用默认值 1。")
        max_workers = 1
        max_model_pipelines = 1

    # 6. 记录启动信息
    logger.info("=" * 80)
    logger.info("诗词ID分发标注任务启动")
    logger.info(f"目标任务总数: {len(tasks_to_distribute)}")
    logger.info(f"强制重跑: {force_rerun}, 全新开始: {fresh_start}, 批次大小: {chunk_size}")
    if dry_run:
        logger.info("模式: Dry Run (空运行)")
    logger.info(f"模型间最大并发数: {max_model_pipelines}, 模型内最大并发数: {max_workers}")
    logger.info("将要执行的任务对:")
    for model_name, current_id_file in tasks_to_distribute:
        logger.info(f"  - 模型: [{model_name}] <---> 文件: [{Path(current_id_file).name}]")
    logger.info("=" * 80)

    if not tasks_to_distribute:
        logger.warning("没有要执行的任务。程序退出。")
        return {"status": "skipped", "message": "没有要执行的任务。"}

    # 7. 执行任务
    total_success = True
    errors = []
    with ThreadPoolExecutor(max_workers=max_model_pipelines, thread_name_prefix="ModelPipeline") as executor:
        future_to_task = {
            executor.submit(run_annotation_for_model, model=m, id_file=f, force_rerun=force_rerun, chunk_size=chunk_size, fresh_start=fresh_start, max_workers=max_workers, output_dir=output_dir, source_dir=source_dir, dry_run=dry_run, full_dry_run=full_dry_run): (m, Path(f).name)
            for m, f in tasks_to_distribute
        }
        for future in as_completed(future_to_task):
            task_info = future_to_task[future]
            try:
                future.result()
                logger.info(f"主线程监控到任务 [{task_info[0]}]-[{task_info[1]}] 已成功结束。")
            except Exception as e:
                total_success = False
                error_msg = f"任务 [{task_info[0]}]-[{task_info[1]}] 执行期间发生严重错误: {e}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

    # 8. 总结和返回
    total_runtime = time.time() - script_start_time
    logger.info("=" * 80)
    logger.info(f"所有指定的模型任务均已执行完毕。总耗时: {total_runtime:.2f} 秒。")
    logger.info("=" * 80)

    return {
        "status": "completed" if total_success else "completed_with_errors",
        "total_duration": total_runtime,
        "tasks_count": len(tasks_to_distribute),
        "errors": errors
    }


@click.command()
@click.option('--model', '-m', help="指定要使用的模型配置别名 (与 --all-models 互斥)")
@click.option('--all-models', '-a', is_flag=True, default=False, help="对所有已配置的模型执行标注任务 (与 --model 互斥)")
@click.option('--id-file', '-f', type=click.Path(exists=True, dir_okay=False, resolve_path=True), 
              help="包含诗词ID的文本文件路径 (与 --id-dir 互斥)。如果指定，该文件将被所有选定模型使用。")
@click.option('--id-dir', '-d', type=click.Path(exists=True, file_okay=False, resolve_path=True), 
              help="包含多个诗词ID文件的目录路径 (与 --id-file 互斥)。")
@click.option('--force-rerun', '-r', is_flag=True, default=False, help="强制重新标注已完成的条目")
@click.option('--chunk-size', '-c', type=int, default=1000, show_default=True, help="每个批次处理的诗词数量")
@click.option('--fresh-start', '-s', is_flag=True, default=False, help="忽略并清除旧的进度，从头开始运行")
@click.option('--output-dir', type=click.Path(file_okay=False, resolve_path=True), required=True, help="项目输出目录，用于派生项目名称和数据库路径")
@click.option('--source-dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), required=True, help="数据源目录")
# [新增] 专门用于控制日志的命令行选项
@click.option('--console-log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default=None, help='设置控制台的日志级别 (覆盖配置文件)')
@click.option('--file-log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default=None, help='设置文件日志的级别 (覆盖配置文件)')
@click.option('--enable-file-log', is_flag=True, default=None, help='强制启用文件日志 (覆盖配置文件)')
@click.option('--dry-run', is_flag=True, default=False, help="空运行模式，测试流程而不实际调用LLM")
@click.option('--full-dry-run', is_flag=True, default=False, help="在dry-run模式下，执行完整流程测试（包括响应解析、内容验证、数据保存到JSON文件），而非跳过这些流程。") # 新增参数
def cli(model, all_models, id_file, id_dir, force_rerun, chunk_size, fresh_start, output_dir, source_dir, console_log_level, file_log_level, enable_file_log, dry_run, full_dry_run):
    """
    【主控制函数】从文件分批读取诗词ID并以多模型并发方式分发标注任务。
    """
    # [修改] 此函数现在作为命令行接口的包装器，调用核心逻辑函数。
    try:
        result = run_distribution_task(
            model=model,
            all_models=all_models,
            id_file=id_file,
            id_dir=id_dir,
            force_rerun=force_rerun,
            chunk_size=chunk_size,
            fresh_start=fresh_start,
            output_dir=output_dir,
            source_dir=source_dir,
            console_log_level=console_log_level,
            file_log_level=file_log_level,
            enable_file_log=enable_file_log,
            dry_run=dry_run,
            full_dry_run=full_dry_run # 传递新增参数
        )
        if result.get("errors"):
            logger.error("一个或多个任务执行失败。详情请查看上面的日志。")
            # 可选：根据需要设置非零退出码
            # sys.exit(1)

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        # 捕获参数校验和健康检查的错误
        logger.error(f"任务启动失败: {e}")
        # 打印帮助信息以指导用户
        click.echo(click.get_current_context().get_help(), err=True)
        # sys.exit(1)
    except Exception as e:
        logger.critical(f"发生未预料的严重错误: {e}", exc_info=True)
        # sys.exit(1)


if __name__ == '__main__':
    # 为了能够从项目根目录直接运行此脚本（python -m src.distribute_tasks），
    # 我们需要在脚本主入口进行一些路径处理，以确保能正确找到 `src` 目录下的其他模块。
    # 如果您总是通过 `python distribute_tasks.py` 在根目录运行，这部分不是必须的，但这是一个好的实践。
    import sys
    from pathlib import Path
    # 将项目根目录添加到Python路径
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 现在可以安全地调用 cli 函数了
    cli()
