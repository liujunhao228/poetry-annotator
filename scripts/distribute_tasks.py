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


def process_chunk(args: Tuple[str, List[int], bool]) -> Dict[str, Any]:
    """
    【内层并发单元】工作线程执行的函数，处理一个批次的ID。
    """
    model_name, poem_ids_chunk, force_rerun = args
    thread_ident = threading.get_ident()
    logger.debug(f"线程 {thread_ident} 开始为模型 '{model_name}' 处理 {len(poem_ids_chunk)} 个ID的批次。")
    try:
        annotator = Annotator(model_name)
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


def run_annotation_for_model(model: str, id_file: str, force_rerun: bool, chunk_size: int, fresh_start: bool, max_workers: int):
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
      
        task_args = [(model, chunk, force_rerun) for chunk in chunks_to_process]
      
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


# [修改] 为脚本添加入口参数，使其可被GUI调用和控制
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
@click.option('--db', type=str, help="数据库名称（从配置文件中获取路径）")
# [新增] 专门用于控制日志的命令行选项
@click.option('--console-log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default=None, help='设置控制台的日志级别 (覆盖配置文件)')
@click.option('--file-log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default=None, help='设置文件日志的级别 (覆盖配置文件)')
@click.option('--enable-file-log', is_flag=True, default=None, help='强制启用文件日志 (覆盖配置文件)')
def cli(model, all_models, id_file, id_dir, force_rerun, chunk_size, fresh_start, db, console_log_level, file_log_level, enable_file_log):
    """
    【主控制函数】从文件分批读取诗词ID并以多模型并发方式分发标注任务。
    """
    # [修改] 使用新的日志设置函数，并传入命令行参数
    # 这允许GUI或命令行用户动态调整日志级别
    setup_default_logging(
        console_level=console_log_level,
        file_level=file_log_level,
        enable_file_log=enable_file_log
    )
    
    # 设置数据库
    if db:
        try:
            # 更新全局数据管理器实例以使用指定的数据库
            get_data_manager(db_name=db)
        except ValueError as e:
            logger.error(f"数据库设置错误: {e}")
            return
    
    script_start_time = time.time()

    # --- 1. 参数校验和模型选择 ---
    if not model and not all_models:
        logger.error("错误: 必须提供 '-m/--model <name>' 或 '-a/--all-models' 参数之一。")
        click.echo(click.get_current_context().get_help())
        return
    if model and all_models:
        logger.error("错误: '--model' 和 '--all-models' 参数是互斥的，请只使用一个。")
        return
    if not id_file and not id_dir:
        logger.error("错误: 必须提供 '-f/--id-file' 或 '-d/--id-dir' 参数之一。")
        click.echo(click.get_current_context().get_help())
        return
    if id_file and id_dir:
        logger.error("错误: '--id-file' 和 '--id-dir' 参数是互斥的，请只使用一个。")
        return

    available_models = llm_factory.list_configured_models().keys()
    if not available_models:
        logger.error("错误: 配置文件中没有找到任何 [Model.*] 配置。")
        return

    models_to_run = list(available_models) if all_models else [model]
    if not all(m in available_models for m in models_to_run):
        logger.error(f"错误: 指定模型不在配置中。请求: {models_to_run}, 可用: {list(available_models)}")
        return
  
    # --- [新增] 执行健康检查 ---
    # 使用 asyncio.run 来执行异步的健康检查函数
    if not asyncio.run(health_checker.run_all_checks(models_to_run)):
        # 详细的错误信息已在 health_checker 中打印
        logger.critical("任务因健康检查失败而中止。")
        return
    # -----------------------------

    # --- 2. 确定ID文件(s)和模型-文件映射 ---
    tasks_to_distribute: List[Tuple[str, str]] = [] 

    if id_file:
        tasks_to_distribute = [(model_name, id_file) for model_name in models_to_run]
    elif id_dir:
        id_files_in_dir = sorted([
            str(p.resolve()) for p in Path(id_dir).glob('*.txt') if p.is_file()
        ])
        if not id_files_in_dir:
            logger.error(f"错误: 目录 '{id_dir}' 中没有找到任何 .txt 文件。")
            return
        if len(models_to_run) != len(id_files_in_dir):
            logger.error(f"错误: 模型数量 ({len(models_to_run)}) 与目录 '{id_dir}' 中的 .txt 文件数量 ({len(id_files_in_dir)}) 不匹配。")
            logger.error(f"模型: {models_to_run}\nID文件: {[Path(f).name for f in id_files_in_dir]}")
            return
        tasks_to_distribute = list(zip(models_to_run, id_files_in_dir))

    # --- 3. 获取并发设置 ---
    try:
        llm_config = config_manager.get_llm_config()
        max_workers = llm_config.get('max_workers', 1)
        max_model_pipelines = llm_config.get('max_model_pipelines', 1)
    except Exception as e:
        logger.error(f"从配置加载并发设置失败: {e}。将使用默认值 1。")
        max_workers = 1
        max_model_pipelines = 1

    # --- 4. 记录启动信息 ---
    logger.info("=" * 80)
    logger.info("诗词ID分发标注工具启动")
    logger.info(f"目标任务总数: {len(tasks_to_distribute)}")
    logger.info(f"强制重跑: {force_rerun}, 全新开始: {fresh_start}, 批次大小: {chunk_size}")
    logger.info(f"模型间最大并发数 (max_model_pipelines): {max_model_pipelines}")
    logger.info(f"模型内最大并发数 (max_workers): {max_workers}")
    if fresh_start:
        logger.info("注意: 已启用全新开始模式，将忽略并删除所有现有进度文件。")
    logger.info("将要执行的任务对:")
    for model_name, current_id_file in tasks_to_distribute:
        logger.info(f"  - 模型: [{model_name}] <---> 文件: [{Path(current_id_file).name}]")
    logger.info("=" * 80)
    
    if not tasks_to_distribute:
        logger.warning("没有要执行的任务。程序退出。")
        return

    # --- 5. 使用主线程池并发执行所有任务 ---
    logger.info("开始并发执行所有任务...")
    
    with ThreadPoolExecutor(max_workers=max_model_pipelines, thread_name_prefix="ModelPipeline") as executor:
        future_to_task = {
            executor.submit(
                run_annotation_for_model,
                model=model_name,
                id_file=current_id_file,
                force_rerun=force_rerun,
                chunk_size=chunk_size,
                fresh_start=fresh_start,
                max_workers=max_workers
            ): (model_name, Path(current_id_file).name)
            for model_name, current_id_file in tasks_to_distribute
        }

        for future in as_completed(future_to_task):
            task_info = future_to_task[future]
            try:
                future.result()
                logger.info(f"主线程监控到任务 [{task_info[0]}]-[{task_info[1]}] 已成功结束。")
            except Exception as e:
                logger.error(f"主线程捕获到任务 [{task_info[0]}]-[{task_info[1]}] 执行期间发生严重错误: {e}", exc_info=True)
        
        # 显示进度文件状态
        progress_files = list(Path(".progress_cache").glob("state_*.json")) if Path(".progress_cache").exists() else []
        if progress_files:
            logger.info(f"注意: 仍有 {len(progress_files)} 个未完成任务的进度文件存在于 .progress_cache 目录中。")
            logger.info("这些文件将在对应任务下次运行时自动加载，如需重新开始请使用 --fresh-start 参数。")
        else:
            logger.info("所有任务已完成，进度文件已清理。")

    total_runtime = time.time() - script_start_time
    logger.info("=" * 80)
    logger.info(f"所有指定的模型任务均已执行完毕。总耗时: {total_runtime:.2f} 秒。")
    logger.info("=" * 80)


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
