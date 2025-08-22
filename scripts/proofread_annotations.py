# scripts/proofread_annotations.py

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import List, Generator

# 确保能正确导入项目模块
try:
    from src.data.manager import DataManager
    from src.config import config_manager
    from src.logging_config import setup_default_logging, get_logger
except ImportError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from src.data.manager import DataManager
    from src.config import config_manager
    from src.logging_config import setup_default_logging, get_logger

# 使用与项目其他部分一致的日志记录器
# 请确保您的 logging_config.py 在 src/ 目录中
# 如果没有，可以暂时替换为 logging.basicConfig
try:
    setup_default_logging()
    logger = get_logger(__name__)
except NameError:
    # 备用日志配置
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)


def read_ids_in_chunks(file_path: str, chunk_size: int = 5000) -> Generator[List[int], None, None]:
    """
    以内存友好的方式从文件中分块读取ID。
    这是一个生成器，每次只在内存中保留一个块。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk.append(int(line))
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                except ValueError:
                    logger.warning(f"在ID文件中发现非整数行，已跳过: '{line}'")
            if chunk:
                yield chunk
    except FileNotFoundError:
        logger.error(f"ID文件未找到: {file_path}")
        raise


def proofread_annotations(db_path: str, id_file_path: str, model_identifier: str, 
                          output_dir: str, chunk_size: int):
    """
    校对诗词标注状态的主函数。
    """
    logger.info("校对任务开始...")
    logger.info(f"数据库: {db_path}")
    logger.info(f"ID文件: {id_file_path}")
    logger.info(f"校对模型: '{model_identifier}'")
    logger.info(f"查询批次大小: {chunk_size}")

    dm = DataManager(db_path)
    
    # 初始化集合来存储所有ID
    all_target_ids = set()
    completed_ids = set()
    
    # 第一遍：读取所有目标ID并统计总数
    try:
        with open(id_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_target_ids.add(int(line))
                    except ValueError:
                        pass # 警告已在 read_ids_in_chunks 中处理
        total_ids_to_check = len(all_target_ids)
        if total_ids_to_check == 0:
            logger.warning("ID文件为空或不包含任何有效ID。任务结束。")
            return
    except FileNotFoundError:
        return # 错误已在 read_ids_in_chunks 中记录

    logger.info(f"从文件中读取到 {total_ids_to_check} 个唯一ID待检查。")

    # 第二遍：分块检查
    processed_count = 0
    try:
        from tqdm import tqdm
        progress_bar = tqdm(total=total_ids_to_check, desc="校对进度", unit="个ID")
    except ImportError:
        logger.warning("tqdm 未安装。将不显示进度条。可运行 'pip install tqdm' 安装。")
        progress_bar = None

    for id_chunk in read_ids_in_chunks(id_file_path, chunk_size):
        # 调用新添加的高效方法
        completed_in_chunk = dm.get_completed_poem_ids(id_chunk, model_identifier)
        completed_ids.update(completed_in_chunk)
        
        processed_count += len(id_chunk)
        if progress_bar:
            progress_bar.update(len(id_chunk))

    if progress_bar:
        progress_bar.close()

    # 计算待处理的ID
    # 使用集合操作，非常高效
    pending_ids = all_target_ids - completed_ids

    # --- 生成报告 ---
    logger.info("=" * 60)
    logger.info("校对结果报告")
    logger.info("-" * 60)
    logger.info(f"总计检查ID数: {total_ids_to_check}")
    logger.info(f"已成功标注数: {len(completed_ids)}")
    logger.info(f"待处理 (失败/未运行) 数: {len(pending_ids)}")
    
    completion_rate = (len(completed_ids) / total_ids_to_check * 100) if total_ids_to_check > 0 else 0
    logger.info(f"完成率: {completion_rate:.2f}%")
    logger.info("=" * 60)

    # --- 输出到文件 ---
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        completed_file = output_path / f"completed_{model_identifier}.txt"
        pending_file = output_path / f"pending_{model_identifier}.txt"

        try:
            with open(completed_file, 'w', encoding='utf-8') as f:
                for poem_id in sorted(list(completed_ids)):
                    f.write(f"{poem_id}\n")
            logger.info(f"已完成的ID列表已保存至: {completed_file}")

            with open(pending_file, 'w', encoding='utf-8') as f:
                for poem_id in sorted(list(pending_ids)):
                    f.write(f"{poem_id}\n")
            logger.info(f"待处理的ID列表已保存至: {pending_file}")
            
        except IOError as e:
            logger.error(f"写入输出文件时出错: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="校对诗词ID列表中的所有诗词是否都已成功标注。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 尝试从配置中获取默认数据库路径
    default_db_path = None
    try:
        default_db_path = config_manager.get_database_config()['db_path']
    except Exception:
        pass

    parser.add_argument('--db-path', type=str, default=default_db_path,
                        help="SQLite数据库文件路径。如果未提供，则尝试从config.ini读取。")
    parser.add_argument('--id-file', type=str, required=True,
                        help="包含待校对诗词ID的文本文件路径（每行一个ID）。")
    parser.add_argument('--model', type=str, required=True,
                        help="要校对的标注模型标识符 (例如 'glm-4-flash')。")
    parser.add_argument('--output-dir', type=str, default="data/proofread_results",
                        help="用于存放'已完成'和'待处理'ID列表的输出目录。")
    parser.add_argument('--chunk-size', type=int, default=5000,
                        help="每次从数据库查询的ID数量。调整此值以平衡性能和内存占用。")
    
    args = parser.parse_args()

    if not args.db_path:
        parser.error("未能从config.ini获取数据库路径，请使用 --db-path 手动指定。")

    proofread_annotations(
        db_path=args.db_path,
        id_file_path=args.id_file,
        model_identifier=args.model,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size
    )
