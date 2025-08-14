# recover_from_log_v6.py
"""
从日志文件中恢复因意外中断而未保存的标注数据。
V6更新：
- 适配新的单行JSON日志格式（由src/annotation_data_logger.py生成）
- 每行是一个独立的JSON对象，包含poem_id和annotation_data
"""
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import sqlite3
import click
import sys
import os

# --- 模块导入 ---
# 确保可以从项目根目录正确导入src模块
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 初始化全局变量
config_manager = None
DataManager = None

try:
    from src.config_manager import config_manager
    from src.data_manager import DataManager
except ImportError as e:
    print(f"警告：无法导入 config_manager 或 DataManager: {e}")
    print("请确保此脚本位于项目根目录，并且 `src` 目录在 python path 中。")

# --- 配置区 ---
DEFAULT_CACHE_DIR = '.recovery_cache'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_and_validate_json_blocks(log_file_path: str, cache_file_path: str) -> List[List[Dict[str, Any]]]:
    """
    从新格式的日志文件中提取并验证JSON块。
    新格式：每行一个独立的JSON对象，包含poem_id和annotation_data字段
    """
    cache_path = Path(cache_file_path)
    if cache_path.exists():
        logging.info(f"发现缓存 '{cache_path.name}'，直接从缓存加载...")
        try:
            with cache_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"成功从缓存加载 {len(data)} 个有效标注数据块。")
            return data
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"读取缓存文件失败: {e}。将重新解析日志文件。")

    logging.info("未找到缓存，开始从日志文件中提取JSON块...")
    
    log_file = Path(log_file_path)
    if not log_file.exists():
        logging.error(f"日志文件未找到: {log_file_path}")
        return []
        
    validated_json_blocks = []
    
    with log_file.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                # 解析单行JSON
                log_entry = json.loads(line)
                
                # 验证必需字段
                if not isinstance(log_entry, dict):
                    logging.debug(f"第{line_num}行: 不是有效的JSON对象")
                    continue
                    
                if 'poem_id' not in log_entry or 'annotation_data' not in log_entry:
                    logging.debug(f"第{line_num}行: 缺少必需字段poem_id或annotation_data")
                    continue
                
                # annotation_data应该是一个列表
                annotation_data = log_entry['annotation_data']
                if not isinstance(annotation_data, list) or not annotation_data:
                    logging.debug(f"第{line_num}行: annotation_data不是有效的列表或为空")
                    continue
                
                # 验证列表中的每个元素是否包含必需字段
                valid_items = []
                for item in annotation_data:
                    if isinstance(item, dict) and 'sentence_id' in item and 'sentence_text' in item:
                        valid_items.append(item)
                
                if not valid_items:
                    logging.debug(f"第{line_num}行: annotation_data中没有有效的标注项")
                    continue
                
                # 将验证后的数据添加到结果中
                validated_json_blocks.append(valid_items)
                
            except json.JSONDecodeError as e:
                logging.warning(f"第{line_num}行: JSON解析失败 - {e}")
            except Exception as e:
                logging.warning(f"第{line_num}行: 处理时发生错误 - {e}")

    logging.info(f"扫描完成，成功解析了 {len(validated_json_blocks)} 个有效标注数据块。")

    if validated_json_blocks:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.open('w', encoding='utf-8') as f:
                json.dump(validated_json_blocks, f, ensure_ascii=False, indent=2)
            logging.info(f"已将解析结果缓存到 '{cache_path}'。")
        except IOError as e:
            logging.error(f"写入缓存文件失败: {e}")

    return validated_json_blocks

def search_poems_by_sentence(cursor: sqlite3.Cursor, sentence_text: str, candidate_ids: Optional[List[int]] = None) -> List[int]:
    cleaned_text = re.sub(r'[，。？！\s]', '', sentence_text.strip())
    if not cleaned_text:
        return candidate_ids if candidate_ids is not None else []
    query = "SELECT id FROM poems WHERE REPLACE(REPLACE(REPLACE(REPLACE(full_text, '，', ''), '。', ''), '？', ''), '！', '') LIKE ?"
    params = [f'%{cleaned_text}%']
    if candidate_ids:
        if not candidate_ids: return []
        placeholders = ','.join('?' * len(candidate_ids))
        query += f" AND id IN ({placeholders})"
        params.extend(candidate_ids)
    cursor.execute(query, params)
    return [row[0] for row in cursor.fetchall()]

def find_poem_id_for_annotation(cursor: sqlite3.Cursor, annotation_block: List[Dict[str, Any]]) -> Optional[int]:
    sentences = [item['sentence_text'] for item in annotation_block if item.get('sentence_text')]
    if not sentences: return None
    candidate_ids = search_poems_by_sentence(cursor, sentences[0])
    logging.debug(f"第一句 '{sentences[0][:30]}...' 匹配到 {len(candidate_ids)} 个候选ID。")
    if len(candidate_ids) == 1: return candidate_ids[0]
    if len(candidate_ids) == 0: 
        logging.warning(f"警告：第一句 '{sentences[0][:30]}...' 未在数据库中匹配到任何诗词！")
        return None
    for i, sentence in enumerate(sentences[1:], start=2):
        if len(candidate_ids) <= 1: break
        previous_count = len(candidate_ids)
        candidate_ids = search_poems_by_sentence(cursor, sentence, candidate_ids)
        logging.debug(f"  使用第 {i} 句筛选，候选从 {previous_count} -> {len(candidate_ids)}。")
        if len(candidate_ids) == 1: return candidate_ids[0]
        if len(candidate_ids) == 0: 
            logging.warning(f"警告：在筛选过程中，候选ID归零。块无法匹配。")
            return None
    if len(candidate_ids) > 1:
        logging.warning(f"警告：所有句子用完后仍有 {len(candidate_ids)} 个候选 {candidate_ids[:5]}...，匹配模糊，已跳过。")
        return None
    return None

def process_single_log(log_path: Path, model_identifier: str, dry_run: bool, db_path: str) -> Dict[str, int]:
    logging.info("-" * 80)
    logging.info(f"开始处理日志文件: {log_path.name}")
    cache_dir = Path(DEFAULT_CACHE_DIR)
    cache_file_path = cache_dir / f"{log_path.stem}.cache.json"
    valid_annotations = extract_and_validate_json_blocks(str(log_path), str(cache_file_path))
    if not valid_annotations:
        logging.warning("未能从该文件中提取任何有效标注数据。")
        return {'recovered': 0, 'unmatched': 0, 'saved': 0, 'failed_save': 0}
    if DataManager is None:
        logging.error("DataManager 模块未成功加载。无法继续执行数据库操作。")
        return {'recovered': 0, 'unmatched': len(valid_annotations), 'saved': 0, 'failed_save': 0}
    try:
        dm = DataManager(db_path=db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        logging.error(f"连接数据库 '{db_path}' 或实例化DataManager失败: {e}")
        return {'recovered': 0, 'unmatched': len(valid_annotations), 'saved': 0, 'failed_save': 0}
    recovered_data: Dict[int, List[Dict[str, Any]]] = {}
    unmatched_annotations: List[List[Dict[str, Any]]] = []
    for annotation_block in tqdm(valid_annotations, desc=f"匹配 {log_path.stem}", unit="块"):
        poem_id = find_poem_id_for_annotation(cursor, annotation_block)
        if poem_id:
            if poem_id in recovered_data:
                logging.warning(f"诗词ID {poem_id} 在文件 {log_path.name} 中存在重复匹配，将覆盖。")
            recovered_data[poem_id] = annotation_block
        else:
            unmatched_annotations.append(annotation_block)
    conn.close()
    logging.info(f"文件 '{log_path.name}' 匹配完成 - 成功: {len(recovered_data)}, 失败: {len(unmatched_annotations)}")
    stats = {'recovered': len(recovered_data), 'unmatched': len(unmatched_annotations), 'saved': 0, 'failed_save': 0}
    if not recovered_data:
        return stats
    if dry_run:
        logging.warning(f"[试运行] 模式：找到 {len(recovered_data)} 条记录准备写入，但不会实际操作。")
        for i, (poem_id, anno_list) in enumerate(recovered_data.items()):
            if i >= 3: break
            logging.info(f"  [试运行样本] 待写入 Poem ID: {poem_id}, 内容: {str(anno_list[0])[:100]}...")
    else:
        logging.info(f"开始将 {len(recovered_data)} 条恢复的数据写入数据库...")
        for poem_id, anno_list in tqdm(recovered_data.items(), desc=f"保存 {log_path.stem}", unit="条"):
            anno_str = json.dumps(anno_list, ensure_ascii=False)
            success = dm.save_annotation(poem_id=poem_id, model_identifier=model_identifier, status='completed', annotation_result=anno_str)
            if success:
                stats['saved'] += 1
            else:
                stats['failed_save'] += 1
        logging.info(f"数据库写入完成 - 成功: {stats['saved']}, 失败: {stats['failed_save']}")
    return stats


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--file', 'log_file_path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), help='要处理的单个日志文件路径。')
@click.option('--dir', 'log_dir_path', type=click.Path(exists=True, file_okay=False, resolve_path=True), help='包含日志文件 (*.log) 的目录路径。')
@click.option('--model', 'model_identifier', required=True, help='保存标注到数据库时使用的模型标识符, 例如 "gemini-2.5-flash"。')
@click.option('--db-path', 'db_path_override', type=click.Path(dir_okay=False), help='手动指定数据库文件路径，覆盖配置文件中的设置。')
@click.option('--write', 'dry_run', is_flag=True, default=True, help='使用此标志以实际写入数据库。默认为试运行（不写入）。')
def cli(log_file_path, log_dir_path, model_identifier, db_path_override, dry_run):
    """
    从日志文件或目录中恢复标注数据并导入数据库。
    """
    db_path = db_path_override
    if not db_path:
        if config_manager:
            try:
                db_path = config_manager.get_database_config()['db_path']
                logging.info(f"从配置文件加载数据库路径: {db_path}")
            except Exception:
                db_path = './poetry.db'
                logging.warning(f"无法从配置加载，使用默认数据库路径: {db_path}")
        else:
            db_path = './poetry.db'
            logging.warning(f"ConfigManager未加载，使用默认数据库路径: {db_path}")

    if not Path(db_path).is_file():
        logging.error(f"数据库文件未找到: {db_path}")
        logging.error("请确保路径正确，或使用 --db-path 指定。如果数据库尚未创建，请先运行主程序进行初始化。")
        return
        
    if not log_file_path and not log_dir_path:
        raise click.UsageError("错误: 必须提供 '--file' 或 '--dir' 参数之一。")
    if log_file_path and log_dir_path:
        raise click.UsageError("错误: '--file' 和 '--dir' 参数是互斥的。")

    if log_file_path:
        files_to_process = [Path(log_file_path)]
    else:
        log_dir = Path(log_dir_path)
        files_to_process = sorted(list(log_dir.glob('*.log')))
        if not files_to_process:
            logging.error(f"在目录 '{log_dir}' 中未找到任何 .log 文件。")
            return

    logging.info(f"将要处理 {len(files_to_process)} 个日志文件。")
    logging.info(f"模型标识符: '{model_identifier}'")
    logging.info(f"数据库路径: '{db_path}'")
    if dry_run:
        logging.warning("!!! 当前为[试运行 DRY RUN]模式，不会向数据库写入任何数据。要实际写入，请使用 --write 标志。!!!")

    total_stats = {'recovered': 0, 'unmatched': 0, 'saved': 0, 'failed_save': 0}

    for log_path in files_to_process:
        stats = process_single_log(log_path, model_identifier, dry_run, db_path)
        for key in total_stats:
            total_stats[key] += stats[key]

    logging.info("=" * 80)
    logging.info("所有日志文件处理完毕 - 最终汇总报告")
    logging.info("=" * 80)
    logging.info(f"总成功匹配记录数: {total_stats['recovered']}")
    logging.info(f"总未匹配数据块数: {total_stats['unmatched']}")
    if not dry_run:
        logging.info(f"总成功保存记录数: {total_stats['saved']}")
        logging.info(f"总保存失败记录数: {total_stats['failed_save']}")
    else:
        logging.info(f"(试运行) 准备写入数据库的记录数: {total_stats['recovered']}")
    logging.info("=" * 80)

if __name__ == '__main__':
    cli()