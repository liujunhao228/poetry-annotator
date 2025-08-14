#!/usr/bin/env python3
"""
从模型特定日志中恢复失败任务的工具 (适配 V6+ 日志结构)

此脚本会分析 `logs/{model_name}/` 目录下的日志文件，提取所有标注失败的诗词ID，
并将这些ID写入一个新的文本文件，以便后续使用 distribute_tasks.py 重新处理。
"""

import re
import sys
from pathlib import Path
from typing import List, Set
import click

# --- 配置 ---
# 用于匹配失败日志行的正则表达式
# 匹配 annotator.py 中 _annotate_single_poem 方法记录的最终失败日志
FAILED_LOG_PATTERN = re.compile(r"诗词ID\s+(\d+)\s+标注流程在所有重试后最终失败:")

# --- 核心函数 ---

def find_model_log_files(model_name: str, log_root_dir: str = "logs") -> List[Path]:
    """
    查找指定模型的所有日志文件。

    Args:
        model_name: 模型名称。
        log_root_dir: 根日志目录路径。

    Returns:
        包含所有日志文件 Path 对象的列表。
    """
    model_log_dir = Path(log_root_dir) / model_name
    if not model_log_dir.exists():
        print(f"警告: 模型日志目录不存在: {model_log_dir}", file=sys.stderr)
        return []

    log_files = list(model_log_dir.glob("*.log"))
    print(f"信息: 在目录 '{model_log_dir}' 中找到 {len(log_files)} 个日志文件。")
    return log_files


def extract_failed_ids_from_log(log_file_path: Path) -> Set[int]:
    """
    从单个日志文件中提取失败的诗词ID。

    Args:
        log_file_path: 日志文件的 Path 对象。

    Returns:
        包含失败诗词ID的集合。
    """
    failed_ids = set()
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                # 查找匹配的失败日志行
                match = FAILED_LOG_PATTERN.search(line)
                if match:
                    try:
                        poem_id = int(match.group(1))
                        failed_ids.add(poem_id)
                    except ValueError:
                        print(f"警告: 在文件 {log_file_path} 第 {line_number} 行发现无效ID: '{match.group(1)}'")
    except Exception as e:
        print(f"错误: 读取或处理日志文件 '{log_file_path}' 时出错: {e}", file=sys.stderr)
        
    print(f"信息: 从文件 '{log_file_path.name}' 中提取到 {len(failed_ids)} 个唯一失败ID。")
    return failed_ids


def consolidate_ids(all_failed_id_sets: List[Set[int]]) -> List[int]:
    """
    合并所有从日志文件中提取的ID集合。

    Args:
        all_failed_id_sets: 包含多个ID集合的列表。

    Returns:
        去重并排序后的ID列表。
    """
    if not all_failed_id_sets:
        return []
        
    # 使用 set.union 合并所有集合并自动去重
    consolidated_set = set().union(*all_failed_id_sets)
    # 转换为列表并排序
    consolidated_list = sorted(list(consolidated_set))
    print(f"信息: 合并后总共得到 {len(consolidated_list)} 个唯一失败ID。")
    return consolidated_list


def write_recovery_file(ids: List[int], output_path: Path):
    """
    将ID列表写入恢复文件。

    Args:
        ids: 要写入的ID列表。
        output_path: 输出文件的 Path 对象。
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for poem_id in ids:
                f.write(f"{poem_id}\n")
        print(f"成功: 已将 {len(ids)} 个ID写入恢复文件: {output_path}")
    except Exception as e:
        print(f"错误: 写入恢复文件 '{output_path}' 失败: {e}", file=sys.stderr)
        raise


# --- 主入口 ---

@click.command()
@click.option('--model', '-m', required=True, help='指定要分析日志的模型名称。')
@click.option('--output-dir', '-o', default='ids/recovery', show_default=True, 
              help='指定存放恢复ID文件的输出目录。')
@click.option('--log-dir', '-l', default='logs', show_default=True, 
              help='指定根日志目录。')
@click.option('--output-filename-suffix', '-s', default='', 
              help='为输出文件添加自定义后缀。')
def main(model: str, output_dir: str, log_dir: str, output_filename_suffix: str):
    """
    主函数：执行从模型日志恢复失败ID的完整流程。
    """
    print("=" * 60)
    print(f"开始为模型 '{model}' 从日志恢复失败任务ID...")
    print(f"日志目录: {log_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)

    # 1. 查找日志文件
    log_files = find_model_log_files(model, log_dir)
    if not log_files:
        print("信息: 未找到任何日志文件，无需恢复。")
        return

    # 2. 从所有日志文件中提取失败ID
    all_failed_id_sets = []
    for log_file in log_files:
        failed_ids = extract_failed_ids_from_log(log_file)
        all_failed_id_sets.append(failed_ids)

    # 3. 合并ID
    consolidated_ids = consolidate_ids(all_failed_id_sets)
    if not consolidated_ids:
        print("信息: 未从日志中发现任何失败的ID。")
        return

    # 4. 构造输出文件路径
    output_path_obj = Path(output_dir)
    suffix_part = f"_{output_filename_suffix}" if output_filename_suffix else ""
    timestamp = "" # 为了简化，这里不加时间戳，由用户通过后缀控制
    output_filename = f"recovery_ids_{model}{suffix_part}.txt"
    final_output_path = output_path_obj / output_filename

    # 5. 写入恢复文件
    write_recovery_file(consolidated_ids, final_output_path)

    print("=" * 60)
    print(f"恢复流程完成。共恢复 {len(consolidated_ids)} 个失败ID。")
    print(f"请使用以下命令重新处理这些ID:")
    print(f"  python scripts/distribute_tasks.py -m {model} -f \"{final_output_path}\"")
    print("=" * 60)


if __name__ == '__main__':
    main()
