import json
import logging
import argparse
import sqlite3
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data import get_data_manager

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_duplicate_full_text_groups(output_dir: str, source_dir: str) -> List[Dict[str, Any]]:
    """
    在数据库中查找 full_text 字段内容相同的诗词ID组。

    此方法非常节省内存，因为它利用 SQL 的 GROUP BY 和 HAVING 子句，
    让数据库引擎处理所有繁重的数据聚合工作。Python 脚本只接收
    和处理最终的、已经分组好的结果，而不是将整个表加载到内存中。

    Args:
        output_dir (str): 项目的输出目录，用于派生项目名称和数据库路径。
        source_dir (str): 数据源目录。

    Returns:
        List[Dict[str, Any]]: 一个包含重复项信息的列表。每个字典代表一个重复组，
                               包含 'ids' (ID列表) 和 'text_preview' (文本预览)。
    """
    logging.info(f"开始在项目输出目录 '{output_dir}' 中查找重复的 full_text 内容...")
    
    # 获取数据管理器
    data_manager = get_data_manager(output_dir=output_dir, source_dir=source_dir)
    
    # 获取数据库路径
    raw_data_db_path = data_manager.separate_db_paths.get('raw_data')
    if not raw_data_db_path:
        logging.error("无法获取原始数据数据库路径。")
        return []
    
    # 获取数据库连接
    conn = sqlite3.connect(raw_data_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # SQL 查询:
    # 1. GROUP BY full_text: 将具有相同 full_text 内容的行分为一组。
    # 2. HAVING COUNT(id) > 1: 筛选出那些成员数量大于1的组，即存在重复的组。
    # 3. GROUP_CONCAT(id): 将每个组内的所有 ID 连接成一个逗号分隔的字符串。
    # 4. SELECT ...: 选择连接后的ID字符串和对应的 full_text。
    query = """
        SELECT
            GROUP_CONCAT(id) as ids,
            full_text
        FROM
            poems
        GROUP BY
            full_text
        HAVING
            COUNT(id) > 1
        ORDER BY
            COUNT(id) DESC;
    """

    duplicate_groups = []
    try:
        logging.info("正在执行查询，这可能需要一些时间，具体取决于数据库大小...")
        cursor.execute(query)
        rows = cursor.fetchall()

        # 逐行处理查询结果，避免一次性加载所有结果到内存
        for row in rows:
            ids_str, full_text = row
            
            # 将逗号分隔的ID字符串转换为整数列表
            id_list = sorted([int(id_val) for id_val in ids_str.split(',')])
            
            # 创建一个文本预览，避免在日志或输出中打印过长的文本
            text_preview = (full_text[:70] + '...') if len(full_text) > 70 else full_text
            text_preview_cleaned = text_preview.replace('\n', ' ')

            duplicate_groups.append({
                "ids": id_list,
                "text_preview": text_preview_cleaned
            })
            logging.debug(f"发现重复组: IDs {id_list} - 文本: {text_preview_cleaned}")

    except Exception as e:
        logging.error(f"数据库操作失败: {e}")
        # 如果出现问题，返回空列表
        return []
    finally:
        conn.close()

    return duplicate_groups

def main():
    """
    脚本主入口。
    """
    parser = argparse.ArgumentParser(
        description='在数据库的 poems 表中查找 full_text 内容重复的 ID 组。',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='指定项目输出目录，用于派生项目名称和数据库路径。'
    )
    parser.add_argument(
        '--source-dir',
        type=str,
        required=True,
        help='指定数据源目录。'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='将结果保存为JSON文件的路径。如果未指定，则打印到控制台。'
    )

    args = parser.parse_args()
    
    # 查找重复组
    groups = find_duplicate_full_text_groups(output_dir=args.output_dir, source_dir=args.source_dir)

    if groups:
        logging.info(f"查询完成！总共找到 {len(groups)} 个内容重复的组。")
        
        # 准备仅包含ID列表的最终结果，以满足核心需求
        id_groups = [group['ids'] for group in groups]

        if args.output_file:
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    # 将包含预览的详细信息写入文件，更具可读性
                    json.dump(groups, f, ensure_ascii=False, indent=2)
                logging.info(f"结果已成功保存到: {args.output_file}")
            except IOError as e:
                logging.error(f"无法写入文件 {args.output_file}: {e}")
        else:
            print("\n" + "="*50)
            print("发现以下 full_text 内容重复的 ID 组:")
            print("="*50)
            # 为了清晰地输出到控制台，我们打印带有预览的格式
            for group in groups:
                 print(f"ID 组: {group['ids']} (共 {len(group['ids'])} 个)")
                 print(f"   文本预览: {group['text_preview']}\n")
            
            # 如果需要严格按照 "ID组列表" 的格式输出，可以取消下面这行的注释
            # print("\n严格格式的ID组列表:")
            # print(json.dumps(id_groups, indent=2))

    else:
        logging.info("查询完成，未找到任何 full_text 内容重复的记录。")

if __name__ == '__main__':
    main()
