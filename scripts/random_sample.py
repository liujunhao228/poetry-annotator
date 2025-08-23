import random
import argparse
import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data import get_data_manager
from src.config import config_manager


def get_random_poem_ids(db_name, sample_size=1, exclude_annotated=False, model_identifier=None, active_only=False):\n    \"\"\"\n    高效随机抽取诗词ID。\n    新增功能：可以通过 exclude_annotated 和 model_identifier 参数控制是否排除已标注的诗词。\n    新增功能：可以通过 active_only 参数控制是否只抽取 data_status 为 'active' 的诗词。\n    \"\"\"\n    try:\n        # 获取指定数据库的数据管理器\n        data_manager = get_data_manager(db_name)\n        # 使用原始数据数据库适配器查询 poems 表\n        poems_db_adapter = data_manager.db_adapter\n        # 使用标注数据数据库适配器查询 annotations 表\n        annotations_db_adapter = data_manager.annotation_db\n        \n        # --- 构建查询条件 ---\n        where_conditions = []\n        query_params = []\n        \n        # 如果需要只抽取 active 状态的诗词\n        if active_only:\n            where_conditions.append(\"data_status = ?\")\n            query_params.append('active')\n        \n        # 如果需要排除已标注的诗词\n        completed_ids_list = []\n        if exclude_annotated:\n            if model_identifier:\n                # 查询指定模型已成功标注的诗词ID\n                completed_query = \"\"\"\n                    SELECT poem_id FROM annotations \n                    WHERE model_identifier = ? AND status = 'completed'\n                \"\"\"\n                rows = annotations_db_adapter.execute_query(completed_query, (model_identifier,))\n                completed_ids = {row[0] for row in rows}\n            else:\n                # 查询所有已成功标注的诗词ID（不区分模型）\n                completed_query = \"\"\"\n                    SELECT poem_id FROM annotations \n                    WHERE status = 'completed'\n                \"\"\"\n                rows = annotations_db_adapter.execute_query(completed_query)\n                completed_ids = {row[0] for row in rows}\n            \n            if completed_ids:\n                # 构造排除已完成ID的条件\n                placeholders = ','.join('?' * len(completed_ids))\n                where_conditions.append(f\"id NOT IN ({placeholders})\")\n                # 注意：completed_ids_list 不直接添加到 query_params，而是在后续动态拼接查询时处理\n                completed_ids_list = list(completed_ids)\n        \n        # 构建WHERE子句\n        where_clause = \"\"\n        if where_conditions:\n            where_clause = \"WHERE \" + \" AND \".join(where_conditions)\n            # query_params 已经包含了 active_only 的参数\n            # completed_ids_list 的参数在后续动态拼接查询时处理\n        \n        # 获取最大ID和符合条件的记录总数\n        rows = poems_db_adapter.execute_query(\"SELECT MAX(id) FROM poems\")\n        max_id_result = rows[0] if rows else [None]\n        max_id = max_id_result[0] if max_id_result else 0\n        \n        count_query = f\"SELECT COUNT(id) FROM poems {where_clause}\"\n        rows = poems_db_adapter.execute_query(count_query, tuple(query_params))\n        total_records_result = rows[0] if rows else [None]\n        total_records = total_records_result[0] if total_records_result else 0\n        \n        if not max_id or total_records == 0:\n            if exclude_annotated and model_identifier:\n                print(\"数据库中没有符合条件的诗词记录。\", file=sys.stderr)\n            else:\n                print(\"数据库中没有诗词记录。\", file=sys.stderr)\n            return []\n        \n        # 确保请求的数量不超过总记录数，且不为负数或零\n        sample_size = min(sample_size, total_records)\n        if sample_size <= 0:\n            return []\n\n        selected_ids = set()\n        \n        # 优化策略：如果所需ID数量占总数较大比例\n        if sample_size > total_records / 2: \n            select_query = f\"SELECT id FROM poems {where_clause}\"\n            rows = poems_db_adapter.execute_query(select_query, tuple(query_params))\n            all_ids = [row[0] for row in rows]\n            random.shuffle(all_ids) \n            selected_ids.update(all_ids[:sample_size]) \n        else:\n            # 传统随机抽样\n            while len(selected_ids) < sample_size:\n                ids_to_fetch_more = sample_size - len(selected_ids)\n                candidates_k = min(max_id, ids_to_fetch_more * 2 if ids_to_fetch_more > 0 else 1) \n                \n                if candidates_k <= 0: break\n                potential_candidate_ids = random.sample(range(1, max_id + 1), candidates_k)\n                if not potential_candidate_ids: break\n\n                placeholders = ','.join('?' * len(potential_candidate_ids))\n                \n                # --- 动态拼接查询语句 --- \n                query = f\"SELECT id FROM poems WHERE id IN ({placeholders})\"\n                query_params_local = list(potential_candidate_ids)\n                \n                # 添加过滤条件\n                # 如果启用了 active_only，query_params_local 需要包含 'active' 参数\n                if active_only:\n                    query += \" AND data_status = ?\"\n                    query_params_local.append('active')\n                    \n                if exclude_annotated and completed_ids_list:\n                    completed_placeholders = ','.join('?' * len(completed_ids_list))\n                    query += f\" AND id NOT IN ({completed_placeholders})\"\n                    query_params_local.extend(completed_ids_list)\n                \n                rows = poems_db_adapter.execute_query(query, tuple(query_params_local))\n                # 只添加需要的数量，避免超过sample_size\n                fetched_ids = [row[0] for row in rows]\n                for pid in fetched_ids:\n                    if len(selected_ids) < sample_size:\n                        selected_ids.add(pid)\n                    else:\n                        break\n        \n        return list(selected_ids)\n    \n    except Exception as e:\n        print(f\"发生未知错误: {e}\", file=sys.stderr)\n        return []


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
        parser.error("错误: --db 参数已废弃，请使用 --db-name 参数指定数据库名称。")

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