import sqlite3
import random
import argparse
import sys
import os

def get_random_poem_ids(db_path, sample_size=1, filter_enabled=False):
    """
    高效随机抽取诗词ID。
    新增功能：可以通过 filter_enabled 参数控制是否过滤掉包含'□'（缺字标记）的诗词。
    """
    # --- 【修改】根据实际数据结构调整过滤子句 ---
    # 检测的字段为：rhythmic (词牌名), author (作者), full_text (完整文本)
    filter_clause = ""
    if filter_enabled:
        # 使用 SQLite 的拼接操作符 || 将字段内容合并，然后一次性检查。
        # IFNULL 用于处理字段值为 NULL 的情况，避免整个表达式结果为 NULL。
        filter_clause = " (IFNULL(rhythmic, '') || IFNULL(author, '') || IFNULL(full_text, '')) NOT LIKE '%□%' "
    
    conn = None 
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # --- 根据是否存在 filter_clause 构建查询 --- (此部分逻辑无需修改)
        where_for_count = f"WHERE {filter_clause}" if filter_enabled else ""
        
        # 获取最大ID和符合条件的记录总数
        cursor.execute("SELECT MAX(id) FROM poems")
        max_id_result = cursor.fetchone()
        max_id = max_id_result[0] if max_id_result else 0
        
        cursor.execute(f"SELECT COUNT(id) FROM poems {where_for_count}")
        total_records_result = cursor.fetchone()
        total_records = total_records_result[0] if total_records_result else 0
        
        if not max_id or total_records == 0:
            if filter_enabled:
                print("数据库中没有符合条件的诗词记录。", file=sys.stderr)
            else:
                print("数据库中没有诗词记录。", file=sys.stderr)
            return []
        
        # 确保请求的数量不超过总记录数，且不为负数或零
        sample_size = min(sample_size, total_records)
        if sample_size <= 0:
            return []

        selected_ids = set()
        
        # 优化策略：如果所需ID数量占总数较大比例
        if sample_size > total_records / 2: 
            where_for_select_all = f"WHERE {filter_clause}" if filter_enabled else ""
            cursor.execute(f"SELECT id FROM poems {where_for_select_all}")
            all_ids = [row[0] for row in cursor.fetchall()]
            random.shuffle(all_ids) 
            selected_ids.update(all_ids[:sample_size]) 
        else:
            # 传统随机抽样
            while len(selected_ids) < sample_size:
                ids_to_fetch_more = sample_size - len(selected_ids)
                candidates_k = min(max_id, ids_to_fetch_more * 2 if ids_to_fetch_more > 0 else 1) 
                
                if candidates_k <= 0: break
                potential_candidate_ids = random.sample(range(1, max_id + 1), candidates_k)
                if not potential_candidate_ids: break

                placeholders = ','.join('?' * len(potential_candidate_ids))
                
                # --- 动态拼接查询语句 --- (此部分逻辑无需修改)
                query = f"SELECT id FROM poems WHERE id IN ({placeholders})"
                if filter_enabled:
                    query += f" AND {filter_clause}"
                
                cursor.execute(query, potential_candidate_ids)
                selected_ids.update(row[0] for row in cursor.fetchall())
        
        return list(selected_ids)
    
    except sqlite3.Error as e:
        # --- 【修改】更新错误提示信息 ---
        if "no such column" in str(e) and filter_enabled:
             print(f"数据库错误: {e}", file=sys.stderr)
             print("错误提示：筛选功能要求 poems 表中包含 rhythmic, author, 和 full_text 列。", file=sys.stderr)
             print("如果您的列名不同，请修改 'random_sample.py' 脚本中的 'filter_clause' 变量。", file=sys.stderr)
        else:
            print(f"数据库错误: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"发生未知错误: {e}", file=sys.stderr)
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='随机抽取诗词ID并输出到文件')
    parser.add_argument('--db', type=str, default='poetry.db', help='SQLite数据库文件路径 (默认: poetry.db)')
    parser.add_argument('-n', '--count', type=int, default=1, help='要抽取的诗词ID数量 (默认: 1)')
    
    parser.add_argument('--filter-missing', action='store_true', 
                        help='启用筛选功能，排除任何内容含有“□”符号的诗词。')
                        
    parser.add_argument('--sort', action='store_true', help='按ID升序排序输出到文件')
    parser.add_argument('--no-shuffle', action='store_true', help='禁用默认的输出随机排序 (与 --sort 互斥，若两者都不选则默认随机排序)')

    parser.add_argument('--output-file', type=str, 
                        help='指定输出文件完整路径 (例: /path/to/my_ids.txt)。此参数与 --output-dir 和 --num-files 互斥。')
    parser.add_argument('--output-dir', type=str, 
                        help='指定输出文件存放的目录。与 --output-file 互斥。')
    parser.add_argument('--num-files', type=int, default=1, 
                        help='指定分段输出的文件个数 (默认: 1)。此参数与 --output-file 互斥。')

    args = parser.parse_args()

    # --- 互斥参数检查 ---
    if args.output_file:
        if args.output_dir:
            parser.error("错误: --output-file 和 --output-dir 参数不能同时使用。")
        if args.num_files != 1: 
            parser.error("错误: 当指定 --output-file 参数时，不支持分段输出 (--num-files 必须为1或不指定)。")

    # --- 获取诗词ID ---
    poem_ids = get_random_poem_ids(args.db, args.count, filter_enabled=args.filter_missing)
    
    if not poem_ids:
        print("未获取到任何诗词ID，程序退出。", file=sys.stderr)
        sys.exit(1)
    
    if len(poem_ids) > args.count:
        poem_ids = random.sample(poem_ids, args.count)
    elif len(poem_ids) < args.count:
        print(f"警告: 数据库中可用ID数量 ({len(poem_ids)}) 少于请求数量 ({args.count})。将输出所有可用ID。", file=sys.stderr)

    # --- 后续代码无需改动 ---
    if args.sort:
        poem_ids.sort()
    elif not args.no_shuffle:
        random.shuffle(poem_ids)

    output_segments = []

    if args.output_file:
        output_segments.append((args.output_file, poem_ids))
    else:
        base_output_dir = "."
        if args.output_dir:
            base_output_dir = args.output_dir
        elif args.num_files > 1:
            base_output_dir = "ids"
        
        if base_output_dir != ".":
            try:
                os.makedirs(base_output_dir, exist_ok=True)
            except OSError as e:
                print(f"错误: 无法创建输出目录 '{base_output_dir}': {e}", file=sys.stderr)
                sys.exit(1)
        
        if args.num_files == 1:
            file_path = os.path.join(base_output_dir, "ids.txt")
            output_segments.append((file_path, poem_ids))
        else:
            total_ids = len(poem_ids)
            ids_base_per_file = total_ids // args.num_files
            remainder_ids = total_ids % args.num_files
            current_idx = 0
            for i in range(args.num_files):
                segment_size = ids_base_per_file + (1 if i < remainder_ids else 0)
                segment_ids = poem_ids[current_idx : current_idx + segment_size]
                file_name = f"ids_{i + 1:03d}.txt" 
                file_path = os.path.join(base_output_dir, file_name)
                output_segments.append((file_path, segment_ids))
                current_idx += segment_size

    for file_path, ids_segment in output_segments:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for pid in ids_segment:
                    f.write(f"{pid}\n")
            print(f"ID已成功输出至: {file_path}")
        except IOError as e:
            print(f"错误: 写入文件失败 '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)
    
    print("所有ID输出完成。")
