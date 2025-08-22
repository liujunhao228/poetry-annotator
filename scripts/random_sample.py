import random
import argparse
import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data import DataManager, get_data_manager
from src.config import config_manager


def get_random_poem_ids(db_name, sample_size=1, exclude_annotated=False, model_identifier=None, active_only=False):
    """
    高效随机抽取诗词ID。
    新增功能：可以通过 exclude_annotated 和 model_identifier 参数控制是否排除已标注的诗词。
    新增功能：可以通过 active_only 参数控制是否只抽取 data_status 为 'active' 的诗词。
    """
    try:
        # 获取指定数据库的数据管理器
        data_manager = get_data_manager(db_name)
        db_adapter = data_manager.db_adapter
        
        # --- 构建查询条件 ---
        where_conditions = []
        query_params = []
        
        # 如果需要只抽取 active 状态的诗词
        if active_only:
            where_conditions.append("data_status = ?")
            query_params.append('active')
        
        # 如果需要排除已标注的诗词
        completed_ids_list = []
        if exclude_annotated:
            if model_identifier:
                # 查询指定模型已成功标注的诗词ID
                completed_query = """
                    SELECT poem_id FROM annotations 
                    WHERE model_identifier = ? AND status = 'completed'
                """
                rows = db_adapter.execute_query(completed_query, (model_identifier,))
                completed_ids = {row[0] for row in rows}
            else:
                # 查询所有已成功标注的诗词ID（不区分模型）
                completed_query = """
                    SELECT poem_id FROM annotations 
                    WHERE status = 'completed'
                """
                rows = db_adapter.execute_query(completed_query)
                completed_ids = {row[0] for row in rows}
            
            if completed_ids:
                # 构造排除已完成ID的条件
                placeholders = ','.join('?' * len(completed_ids))
                where_conditions.append(f"id NOT IN ({placeholders})")
                # 注意：completed_ids_list 不直接添加到 query_params，而是在后续动态拼接查询时处理
                completed_ids_list = list(completed_ids)
        
        # 构建WHERE子句
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
            # query_params 已经包含了 active_only 的参数
            # completed_ids_list 的参数在后续动态拼接查询时处理
        
        # 获取最大ID和符合条件的记录总数
        rows = db_adapter.execute_query("SELECT MAX(id) FROM poems")
        max_id_result = rows[0] if rows else [None]
        max_id = max_id_result[0] if max_id_result else 0
        
        count_query = f"SELECT COUNT(id) FROM poems {where_clause}"
        rows = db_adapter.execute_query(count_query, tuple(query_params))
        total_records_result = rows[0] if rows else [None]
        total_records = total_records_result[0] if total_records_result else 0
        
        if not max_id or total_records == 0:
            if exclude_annotated and model_identifier:
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
            rows = db_adapter.execute_query(select_query, tuple(query_params))
            all_ids = [row[0] for row in rows]
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
                # 如果启用了 active_only，query_params_local 需要包含 'active' 参数
                if active_only:
                    query += " AND data_status = ?"
                    query_params_local.append('active')
                    
                if exclude_annotated and completed_ids_list:
                    completed_placeholders = ','.join('?' * len(completed_ids_list))
                    query += f" AND id NOT IN ({completed_placeholders})"
                    query_params_local.extend(completed_ids_list)
                
                rows = db_adapter.execute_query(query, tuple(query_params_local))
                # 只添加需要的数量，避免超过sample_size
                fetched_ids = [row[0] for row in rows]
                for pid in fetched_ids:
                    if len(selected_ids) < sample_size:
                        selected_ids.add(pid)
                    else:
                        break
        
        return list(selected_ids)
    
    except Exception as e:
        print(f"发生未知错误: {e}", file=sys.stderr)
        return []


def get_db_path_by_name(db_name):
    """
    根据数据库名称获取数据库路径
    """
    db_config = config_manager.get_effective_database_config()
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
                        
    parser.add_argument('--exclude-annotated', action='store_true',
                        help='启用排除已标注诗词功能。如果不指定 --model 参数，则排除所有已标注的诗词（不管标识符是什么）')
    parser.add_argument('--model', type=str, 
                        help='模型标识符，用于排除已标注诗词 (与 --exclude-annotated 配合使用)。如果不指定，则排除所有已标注的诗词')
    parser.add_argument('--active-only', action='store_true',
                        help='只抽取状态为 active 的诗词')
                        
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

    # --- 获取数据库名称 ---
    db_name = "default"
    if args.db_name:
        db_name = args.db_name
    elif args.db and args.db != 'poetry.db':
        # 如果指定了具体的数据库路径，需要根据路径找到对应的数据库名称
        db_config = config_manager.get_effective_database_config()
        if 'db_paths' in db_config:
            db_paths = db_config['db_paths']
            for name, path in db_paths.items():
                if os.path.abspath(path) == os.path.abspath(args.db):
                    db_name = name
                    break

    # --- 获取诗词ID ---
    poem_ids = get_random_poem_ids(
        db_name, 
        args.count, 
        exclude_annotated=args.exclude_annotated,
        model_identifier=args.model,
        active_only=args.active_only  # 传递 active_only 参数
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