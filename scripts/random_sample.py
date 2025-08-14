import sqlite3
import random
import argparse
import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_manager import DataManager
from src.config_manager import config_manager

def get_random_poem_ids(db_path, sample_size=1, filter_enabled=False, exclude_annotated=False, model_identifier=None):
    """
    高效随机抽取诗词ID。
    新增功能：可以通过 filter_enabled 参数控制是否过滤掉包含'□'（缺字标记）的诗词。
    新增功能：可以通过 exclude_annotated 和 model_identifier 参数控制是否排除已标注的诗词。
    """
    # --- 根据实际数据结构调整过滤子句 ---
    # 检测的字段为：title (标题), author (作者), full_text (完整文本)
    filter_clause = ""
    if filter_enabled:
        # 使用 SQLite 的拼接操作符 || 将字段内容合并，然后一次性检查。
        # IFNULL 用于处理字段值为 NULL 的情况，避免整个表达式结果为 NULL。
        filter_clause = " (IFNULL(title, '') || IFNULL(author, '') || IFNULL(full_text, '')) NOT LIKE '%□%' "
    
    conn = None 
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # --- 构建查询条件 ---
        where_conditions = []
        if filter_enabled:
            where_conditions.append(filter_clause)
        
        # 如果需要排除已标注的诗词
        completed_ids_list = []
        if exclude_annotated:
            if model_identifier:
                # 查询指定模型已成功标注的诗词ID
                completed_query = """
                    SELECT poem_id FROM annotations 
                    WHERE model_identifier = ? AND status = 'completed'
                """
                cursor.execute(completed_query, (model_identifier,))
                completed_ids = {row[0] for row in cursor.fetchall()}
            else:
                # 查询所有已成功标注的诗词ID（不区分模型）
                completed_query = """
                    SELECT poem_id FROM annotations 
                    WHERE status = 'completed'
                """
                cursor.execute(completed_query)
                completed_ids = {row[0] for row in cursor.fetchall()}
            
            if completed_ids:
                # 构造排除已完成ID的条件
                placeholders = ','.join('?' * len(completed_ids))
                where_conditions.append(f"id NOT IN ({placeholders})")
                completed_ids_list = list(completed_ids)
        
        # 构建WHERE子句
        where_clause = ""
        query_params = []
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
            if exclude_annotated and model_identifier:
                query_params.extend([model_identifier] + completed_ids_list)
            elif exclude_annotated and not model_identifier:
                query_params.extend(completed_ids_list)
            elif completed_ids_list:
                query_params.extend(completed_ids_list)
        
        # 获取最大ID和符合条件的记录总数
        cursor.execute("SELECT MAX(id) FROM poems")
        max_id_result = cursor.fetchone()
        max_id = max_id_result[0] if max_id_result else 0
        
        count_query = f"SELECT COUNT(id) FROM poems {where_clause}"
        cursor.execute(count_query, query_params)
        total_records_result = cursor.fetchone()
        total_records = total_records_result[0] if total_records_result else 0
        
        if not max_id or total_records == 0:
            if filter_enabled or (exclude_annotated and model_identifier) or (exclude_annotated and not model_identifier):
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
            select_query = f"SELECT id FROM poems {where_clause}"
            cursor.execute(select_query, query_params)
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
                
                # --- 动态拼接查询语句 --- 
                query = f"SELECT id FROM poems WHERE id IN ({placeholders})"
                query_params_local = list(potential_candidate_ids)
                
                # 添加过滤条件
                if where_conditions:
                    query += f" AND {filter_clause}" if filter_enabled else ""
                    if exclude_annotated and model_identifier and completed_ids_list:
                        completed_placeholders = ','.join('?' * len(completed_ids_list))
                        query += f" AND id NOT IN ({completed_placeholders})"
                        query_params_local.extend(completed_ids_list)
                    elif exclude_annotated and not model_identifier and completed_ids_list:
                        completed_placeholders = ','.join('?' * len(completed_ids_list))
                        query += f" AND id NOT IN ({completed_placeholders})"
                        query_params_local.extend(completed_ids_list)
                
                cursor.execute(query, query_params_local)
                # 只添加需要的数量，避免超过sample_size
                fetched_ids = [row[0] for row in cursor.fetchall()]
                for pid in fetched_ids:
                    if len(selected_ids) < sample_size:
                        selected_ids.add(pid)
                    else:
                        break
        
        return list(selected_ids)
    
    except sqlite3.Error as e:
        # --- 更新错误提示信息 ---
        if "no such column" in str(e) and filter_enabled:
             print(f"数据库错误: {e}", file=sys.stderr)
             print("错误提示：筛选功能要求 poems 表中包含 title, author, 和 full_text 列。", file=sys.stderr)
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

def get_db_path_by_name(db_name):
    """
    根据数据库名称获取数据库路径
    """
    db_config = config_manager.get_database_config()
    if 'db_paths' in db_config:
        db_paths = db_config['db_paths']
        if db_name in db_paths:
            return db_paths[db_name]
        else:
            raise ValueError(f"数据库 '{db_name}' 未在配置中定义。")
    elif 'db_path' in db_config and db_name == "default":
        return db_config['db_path']
    else:
        raise ValueError(f"无法找到数据库 '{db_name}' 的配置。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='随机抽取诗词ID并输出到文件')
    parser.add_argument('--db', type=str, default='poetry.db', help='SQLite数据库文件路径 (默认: poetry.db)')
    parser.add_argument('--db-name', type=str, help='数据库名称（从配置文件中获取路径）')
    parser.add_argument('-n', '--count', type=int, default=1, help='要抽取的诗词ID数量 (默认: 1)')
    
    parser.add_argument('--filter-missing', action='store_true', 
                        help='启用筛选功能，排除任何内容含有"□"符号的诗词。')
                        
    parser.add_argument('--exclude-annotated', action='store_true',
                        help='启用排除已标注诗词功能。如果不指定 --model 参数，则排除所有已标注的诗词（不管标识符是什么）')
    parser.add_argument('--model', type=str, 
                        help='模型标识符，用于排除已标注诗词 (与 --exclude-annotated 配合使用)。如果不指定，则排除所有已标注的诗词')
                        
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
    if args.db_name and args.db and args.db != 'poetry.db':
        parser.error("错误: --db-name 和 --db 参数不能同时使用。")
        
    if args.output_file:
        if args.output_dir:
            parser.error("错误: --output-file 和 --output-dir 参数不能同时使用。")
        if args.num_files != 1: 
            parser.error("错误: 当指定 --output-file 参数时，不支持分段输出 (--num-files 必须为1或不指定)。")
            
    # 检查 --exclude-annotated 和 --model 参数的使用
    # 现在允许 --exclude-annotated 不指定 --model，表示排除所有已标注的诗词
    pass

    # --- 获取数据库路径 ---
    db_path = args.db
    if args.db_name:
        try:
            db_path = get_db_path_by_name(args.db_name)
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

    # --- 获取诗词ID ---
    poem_ids = get_random_poem_ids(
        db_path, 
        args.count, 
        filter_enabled=args.filter_missing,
        exclude_annotated=args.exclude_annotated,
        model_identifier=args.model
    )
    
    # --- 处理输出排序 ---
    if args.sort:
        poem_ids.sort()
    elif not args.no_shuffle:
        random.shuffle(poem_ids)
        
    # --- 处理输出文件 ---
    if not poem_ids:
        print("未获取到任何诗词ID。", file=sys.stderr)
        sys.exit(1)
        
    # 确定输出文件路径和数量
    output_files = []
    if args.output_file:
        output_files.append(args.output_file)
        ids_per_file = [poem_ids]
    elif args.output_dir:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        num_files = max(1, args.num_files)
        
        # 如果只需要一个文件，则直接使用所有ID
        if num_files == 1:
            ids_per_file = [poem_ids]
        else:
            # 分割ID到多个文件
            ids_per_file = [poem_ids[i::num_files] for i in range(num_files)]
            
        # 修改文件名格式为 ids_001.txt
        for i in range(num_files):
            output_files.append(os.path.join(args.output_dir, f"ids_{i+1:03d}.txt"))
    else:
        # 默认输出到标准输出
        for pid in poem_ids:
            print(pid)
        sys.exit(0)
        
    # 写入文件
    for i, file_path in enumerate(output_files):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for pid in ids_per_file[i]:
                    f.write(f"{pid}\n")
            print(f"已将 {len(ids_per_file[i])} 个诗词ID写入文件: {file_path}")
        except IOError as e:
            print(f"写入文件 {file_path} 时出错: {e}", file=sys.stderr)
            sys.exit(1)
