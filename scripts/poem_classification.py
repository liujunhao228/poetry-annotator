#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诗词预处理分类脚本
用于依照可配置的字典进行关键字匹配，对诗词进行预处理分类
支持可配置的分类与对应字典
参考 scripts/data_cleaning.py 的实现逻辑
"""

import argparse
import sys
import os
import json
import yaml  # 需要添加 pyyaml 依赖

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入 DataManager 和 get_data_manager
# 假设 src/data/manager.py 和 src/config/config_manager.py 存在
from src.data.manager import DataManager, get_data_manager
from src.config import config_manager


# --- 配置加载函数 ---
def load_classification_config(config_path: str = None) -> dict:
    """ 加载诗词分类的配置文件
    :param config_path: 配置文件路径，默认为 config/classification_rules.yaml
    :return: 解析后的配置字典
    """
    if config_path is None:
        config_path = os.path.join(project_root, 'config', 'classification_rules.yaml')
    
    if not os.path.exists(config_path):
        print(f"警告: 配置文件 {config_path} 不存在，将使用默认空规则。")
        # 返回一个空字典，允许脚本在没有配置时也能运行，但没有实际分类规则
        return {} 
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"成功加载配置文件: {config_path}")
        return config if config is not None else {} # 处理空 YAML 文件的情况
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration file {config_path}: {e}")
        raise # 抛出解析错误，因为它阻止了功能的正常运行
    except Exception as e:
        print(f"加载配置文件 {config_path} 时出错: {e}")
        raise


def contains_keywords_in_fields(poem_data: dict, keywords: list[str], fields: list[str]) -> bool:
    """ 检查指定字段的内容是否包含给定的关键词列表中的任意一个关键词。
    
    此函数在 Python 中处理文本，因为灵活的关键词匹配（例如，跨多个字段的 OR 逻辑，
    或特定字符串包含）比通过复杂的 SQL `LIKE` 查询来动态处理规则更有效。
    
    :param poem_data: 包含诗词字段的字典 (e.g., {'title': '...', 'full_text': '...'}).
    :param keywords: 要查找的关键词列表
    :param fields: 要检查的字段列表
    :return: 如果在任何指定字段中找到任何关键词则返回 True，否则返回 False
    """
    if not keywords: # 如果没有提供关键词，则不可能包含任何关键词
        return False
        
    for field in fields:
        content = str(poem_data.get(field, "") or "") # 确保内容是字符串
        for keyword in keywords:
            if keyword and keyword in content: # 确保关键词非空，避免 'in' 操作符对空字符串的行为
                return True
    return False


def classify_poems_data(db_name: str = "default", dry_run: bool = False, config_path: str = None) -> dict:
    """
    对诗词数据进行预处理分类
    通过配置文件自定义分类规则与检测字段范围。
    此函数将所有诗词数据加载到内存中进行分类，然后批量更新数据库。
    
    :param db_name: 数据库名称
    :param dry_run: 是否为试运行（不实际修改数据）
    :param config_path: 配置文件路径
    :return: 分类统计信息
    """
    print(f"开始对数据库 '{db_name}' 的诗词数据进行预处理分类...")
    if dry_run:
        print("【试运行模式】不会实际修改数据")
    
    # 加载配置
    config = load_classification_config(config_path)
    rules = config.get('rules', {})
    global_settings = config.get('global_settings', {})
    default_fields = global_settings.get('default_check_fields', ["title", "full_text"])
    classification_field = global_settings.get('classification_field', 'pre_classification')
    
    # 获取数据管理器
    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    # 统计信息
    stats = {
        'total_poems_scanned': 0,        # 扫描的诗词总数
        'classified_this_run': 0,        # 本次运行中被分类或重新分类的诗词数 (会触发更新)
        'updated_in_db': 0,              # 实际被更新到数据库的诗词数
        'errors': 0,                     # 遇到的错误数
        'skipped_unchanged': 0,          # 因分类结果未改变而跳过的诗词数
        'classification_distribution': {} # 按分类的统计（本次运行确定的新分类）
    }
    
    # 初始化按分类统计
    for rule_name, rule_config in rules.items():
        category = rule_config.get('category', rule_name) # 使用规则中定义的 category，否则使用规则名
        stats['classification_distribution'][category] = 0
        
    try:
        # 获取所有诗词记录的ID、标题、全文及现有预分类字段
        # 这种方法将所有必要数据加载到内存中，以便在 Python 端进行灵活处理。
        # 对于超大型数据集，如果内存成为瓶颈，可以考虑使用 LIMIT/OFFSET 进行分批处理。
        query = f"""
            SELECT id, title, full_text, {classification_field}
            FROM poems
        """
        rows = db_adapter.execute_query(query)
        stats['total_poems_scanned'] = len(rows)
        
        print(f"总共找到 {stats['total_poems_scanned']} 首诗词待处理。")
        
        # 存储待更新的诗词信息：poem_id -> new_classification_list
        poems_to_update: dict[int, list[str]] = {}
        
        # 遍历所有诗词进行分类
        for row in rows:
            poem_id = row[0]
            current_title = row[1] or ""
            current_full_text = row[2] or ""
            existing_classification_json = row[3] # 数据库中已有的分类 JSON 字符串 (可能为 NULL)
            
            poem_data = {
                'id': poem_id,
                'title': current_title,
                'full_text': current_full_text
            }
            
            # 为当前诗词识别的分类（使用集合避免重复）
            identified_categories = set()
            
            # 应用每条分类规则
            for rule_name, rule_config in rules.items():
                if not rule_config.get('enabled', False):
                    continue
                
                keywords = rule_config.get('keywords', [])
                fields = rule_config.get('fields', default_fields)
                category_to_assign = rule_config.get('category', rule_name)
                
                if contains_keywords_in_fields(poem_data, keywords, fields):
                    identified_categories.add(category_to_assign)
            
            # 将分类列表排序，以确保 JSON 字符串的一致性 (例如 ["A", "B"] 总是相同)
            new_classification_list = sorted(list(identified_categories))
            
            # 将分类列表转换为 JSON 字符串或None (如果为空)
            if new_classification_list:
                new_classification_json = json.dumps(new_classification_list, ensure_ascii=False)
            else:
                new_classification_json = None # 如果没有分类，存储为 NULL
            
            # 比较新分类与现有分类，判断是否需要更新
            # 解析现有分类，确保比较的公平性
            parsed_existing_categories = []
            if existing_classification_json:
                try:
                    parsed_existing = json.loads(existing_classification_json)
                    if isinstance(parsed_existing, list):
                        parsed_existing_categories = sorted(parsed_existing)
                except json.JSONDecodeError:
                    # 如果现有字符串不是有效的 JSON 列表，则视为没有有效分类
                    parsed_existing_categories = [] 
            
            # 将解析后的现有分类也转换为统一的 JSON 字符串形式，以便比较
            existing_classification_json_effective = json.dumps(parsed_existing_categories, ensure_ascii=False) if parsed_existing_categories else None
            
            # 如果新分类与数据库中现有分类不同，则标记为待更新
            if new_classification_json != existing_classification_json_effective:
                poems_to_update[poem_id] = new_classification_list
                stats['classified_this_run'] += 1 # 计数需要更新的诗词
            else:
                stats['skipped_unchanged'] += 1 # 计数无需更新的诗词
            
            # 更新分类分布统计（基于新确定的分类，而非数据库中现有的）
            for cat in new_classification_list:
                stats['classification_distribution'][cat] += 1
        
        print(f"\n已为 {len(poems_to_update)} 首诗词确定分类 (共扫描 {stats['total_poems_scanned']} 首)。")
        print(f"因分类结果未改变而跳过更新的诗词有：{stats['skipped_unchanged']} 首。")
        
        # 如果不是试运行模式，则执行数据库更新
        if not dry_run:
            if poems_to_update:
                try:
                    # 使用事务来批量更新，显著提高 SQLite 的写入性能
                    db_adapter.begin_transaction()
                    update_count = 0
                    for poem_id, categories_list in poems_to_update.items():
                        categories_json = json.dumps(categories_list, ensure_ascii=False) if categories_list else None
                        
                        update_query = f"""
                            UPDATE poems 
                            SET {classification_field} = ?
                            WHERE id = ?
                        """
                        # commit=False 表示在循环中不立即提交，而是等待事务结束统一提交
                        rowcount = db_adapter.execute_update(update_query, (categories_json, poem_id), commit=False)
                        update_count += rowcount
                        
                    db_adapter.commit_transaction() # 提交所有待处理的更新
                    stats['updated_in_db'] = update_count
                    print(f"成功更新了数据库中 {stats['updated_in_db']} 首诗词的分类信息。")
                except Exception as e:
                    db_adapter.rollback_transaction() # 发生错误时回滚事务
                    print(f"数据库更新时出错: {e}")
                    stats['errors'] += len(poems_to_update) # 将所有待更新的都计入错误
            else:
                print("没有诗词需要更新分类。")
        else:
            stats['updated_in_db'] = len(poems_to_update) # 试运行模式下，'updated_in_db' 表示会更新的数量
            print(f"试运行模式：将有 {stats['updated_in_db']} 首诗词被更新。")
        
        print("诗词预处理分类完成。")
        return stats
        
    except Exception as e:
        print(f"诗词预处理分类过程中发生意外错误: {e}")
        stats['errors'] = stats['total_poems_scanned'] # 主流程出错，将所有扫描的诗词都计入错误
        return stats


def reset_pre_classification(db_name: str = "default", dry_run: bool = False, config_path: str = None) -> dict:
    """
    重置所有诗词的预分类字段（设置为 NULL）。
    
    :param db_name: 数据库名称
    :param dry_run: 是否为试运行（不实际修改数据）
    :param config_path: 配置文件路径 (用于获取 classification_field 名称，非必需)
    :return: 重置统计信息
    """
    print(f"开始重置数据库 '{db_name}' 的诗词预分类...")
    if dry_run:
        print("【试运行模式】不会实际修改数据")
    
    # 从配置中获取 classification_field 名称，或使用默认值
    config = load_classification_config(config_path)
    global_settings = config.get('global_settings', {})
    classification_field = global_settings.get('classification_field', 'pre_classification')

    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    stats = {
        'total_with_classification': 0, # 当前有分类数据的诗词总数 (非空字符串或非 NULL)
        'reset_count': 0,               # 实际被重置的诗词数
        'errors': 0                     # 错误计数
    }
    
    try:
        # 统计当前分类字段非 NULL 或非空字符串的诗词数量
        count_query = f"""
            SELECT COUNT(*) FROM poems 
            WHERE {classification_field} IS NOT NULL AND {classification_field} != ''
        """
        rows = db_adapter.execute_query(count_query)
        stats['total_with_classification'] = rows[0][0] if rows and rows[0] else 0
        
        print(f"找到 {stats['total_with_classification']} 首具有现有预分类数据的诗词。")
        
        if stats['total_with_classification'] > 0:
            if not dry_run:
                # 将所有预分类字段设置为 NULL
                update_query = f"""
                    UPDATE poems SET {classification_field} = NULL
                """
                
                try:
                    rowcount = db_adapter.execute_update(update_query)
                    stats['reset_count'] = rowcount
                    print(f"已将 {rowcount} 首诗词的预分类重置为 NULL。")
                except Exception as e:
                    print(f"重置诗词预分类时出错: {e}")
                    stats['errors'] = stats['total_with_classification']
            else:
                stats['reset_count'] = stats['total_with_classification']
                print(f"试运行模式：将重置 {stats['reset_count']} 首诗词的预分类。")
        else:
            print("没有诗词具有现有预分类数据需要重置。")
            
        print("预分类重置完成。")
        return stats
        
    except Exception as e:
        print(f"重置预分类过程中发生意外错误: {e}")
        stats['errors'] = stats['total_with_classification']
        return stats


def get_classification_report(db_name: str = "default", config_path: str = None) -> dict:
    """
    获取预分类报告。
    本报告修正了原先的统计问题，能准确统计各个独立分类的诗词数量。
    
    :param db_name: 数据库名称
    :param config_path: 配置文件路径 (用于获取 classification_field 名称)
    :return: 分类报告
    """
    print(f"生成数据库 '{db_name}' 的预分类报告...")
    
    # 从配置中获取 classification_field 名称，或使用默认值
    config = load_classification_config(config_path)
    global_settings = config.get('global_settings', {})
    classification_field = global_settings.get('classification_field', 'pre_classification')

    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    report = {
        'total_poems': 0,                # 数据库中的诗词总数
        'effectively_classified': 0,     # 具有有效、非空分类列表的诗词数
        'unclassified_null': 0,          # pre_classification 字段为 NULL 的诗词数
        'unclassified_empty_string': 0,  # pre_classification 字段为空字符串 '' 的诗词数
        'unclassified_empty_or_invalid_json': 0, # pre_classification 为 '[]', '{}' 或其他无效 JSON 的诗词数
        'by_individual_category': {},    # 统计每个独立分类的诗词数量
        'multiple_categories_poems': 0   # 被分配了多个分类的诗词数
    }
    
    try:
        # 首先，从数据库获取整体统计信息
        summary_query = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN {classification_field} IS NULL THEN 1 END) as null_count,
                COUNT(CASE WHEN {classification_field} = '' THEN 1 END) as empty_string_count
            FROM poems
        """
        summary_rows = db_adapter.execute_query(summary_query)
        if summary_rows and summary_rows[0]:
            report['total_poems'] = summary_rows[0][0]
            report['unclassified_null'] = summary_rows[0][1]
            report['unclassified_empty_string'] = summary_rows[0][2]
        
        # 然后，获取所有非 NULL 和非空字符串的分类数据，在 Python 中进行详细解析和统计
        classification_data_query = f"""
            SELECT {classification_field}
            FROM poems
            WHERE {classification_field} IS NOT NULL AND {classification_field} != ''
        """
        classified_rows = db_adapter.execute_query(classification_data_query)
        
        for row in classified_rows:
            classification_json_str = row[0]
            
            # 根据解析的 JSON 进行分类和计数
            try:
                categories = json.loads(classification_json_str)
                if isinstance(categories, list) and categories: # 检查是否是有效的非空列表
                    report['effectively_classified'] += 1
                    if len(categories) > 1:
                        report['multiple_categories_poems'] += 1
                        
                    for category in categories:
                        if isinstance(category, str): # 确保分类是字符串
                            report['by_individual_category'][category] = report['by_individual_category'].get(category, 0) + 1
                        else:
                            # 列表中包含非字符串元素，视为无效的 JSON 内容
                            report['unclassified_empty_or_invalid_json'] += 1
                            break # 跳出当前分类列表，避免重复计数
                else: 
                    # JSON 是空列表 '[]' 或非列表结构 (如 {})，视为没有有效分类
                    report['unclassified_empty_or_invalid_json'] += 1
            except json.JSONDecodeError:
                # 字符串不是有效的 JSON 格式 (例如：'{ }', 'abc')，视为无效分类
                report['unclassified_empty_or_invalid_json'] += 1
            except Exception as e:
                # 捕获处理过程中其他意外错误
                print(f"警告: 处理分类 '{classification_json_str}' 时出错: {e}")
                report['unclassified_empty_or_invalid_json'] += 1 # 视为未分类


        # 确保所有在配置中定义的类别都在报告中显示，即使数量为 0
        all_defined_categories = set()
        for rule_name, rule_config in config.get('rules', {}).items():
            if rule_config.get('enabled', False): # 只考虑启用的规则
                all_defined_categories.add(rule_config.get('category', rule_name))
        
        for category in sorted(list(all_defined_categories)): # 按字母顺序排序，保持输出一致性
            report['by_individual_category'].setdefault(category, 0)

        # 对分类统计结果按数量降序排序，方便查看
        report['by_individual_category'] = dict(sorted(report['by_individual_category'].items(), key=lambda item: item[1], reverse=True))

        print("预分类报告生成完成。")
        return report
        
    except Exception as e:
        print(f"生成分类报告时发生意外错误: {e}")
        return report # 返回部分报告，并指出错误


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗词预处理分类工具')
    parser.add_argument('--db-name', type=str, default='default', help='数据库名称（从配置文件中获取）')
    parser.add_argument('--classify', action='store_true', help='执行预处理分类')
    parser.add_argument('--reset', action='store_true', help='重置所有预分类为NULL')
    parser.add_argument('--report', action='store_true', help='生成分类报告')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式，不实际修改数据')
    parser.add_argument('--config', type=str, help='自定义配置文件路径 (默认: config/classification_rules.yaml)')
    
    args = parser.parse_args()
    
    # 检查参数：只能指定一个操作
    actions_count = sum([args.classify, args.reset, args.report])
    if actions_count == 0:
        parser.print_help()
        sys.exit(1)
    elif actions_count > 1:
        print("错误：只能指定一个操作（--classify, --reset, 或 --report）。")
        sys.exit(1)
    
    # 执行相应的操作
    if args.classify:
        stats = classify_poems_data(args.db_name, args.dry_run, args.config)
        print("\n--- 诗词预处理分类统计 ---")
        print(f"总计扫描诗词数: {stats['total_poems_scanned']}")
        print(f"本次运行分类/重新分类诗词数 (待更新): {stats['classified_this_run']}")
        print(f"因分类结果未改变而跳过的诗词数: {stats['skipped_unchanged']}")
        print(f"实际更新到数据库的诗词数: {stats['updated_in_db']}")
        print(f"处理过程中遇到的错误数: {stats['errors']}")
        print("\n本次运行确定的分类分布（每首诗可能包含多个分类）：")
        if stats['classification_distribution']:
            # 按数量降序排序
            sorted_categories = sorted(stats['classification_distribution'].items(), key=lambda item: item[1], reverse=True)
            for category, count in sorted_categories:
                if count > 0: # 只显示有计数的分类
                    print(f"  '{category}': {count} 首")
        else:
            print("  未分配任何分类。")
        
    elif args.reset:
        stats = reset_pre_classification(args.db_name, args.dry_run, args.config)
        print("\n--- 预分类重置统计 ---")
        print(f"数据库中具有现有分类数据的诗词数: {stats['total_with_classification']}")
        print(f"重置字段数量 (试运行则为会重置的数量): {stats['reset_count']}")
        print(f"处理过程中遇到的错误数: {stats['errors']}")
        
    elif args.report:
        report = get_classification_report(args.db_name, args.config)
        print("\n--- 诗词预分类报告 ---")
        print(f"数据库中诗词总数: {report['total_poems']}")
        print(f"有效分类诗词数 (具有有效、非空分类列表): {report['effectively_classified']}")
        print(f"  - 具有多个分类的诗词数: {report['multiple_categories_poems']}")
        print(f"未分类诗词数 (字段为 NULL): {report['unclassified_null']}")
        print(f"未分类诗词数 (字段为空字符串 ''): {report['unclassified_empty_string']}")
        print(f"未分类诗词数 (字段为无效 JSON): {report['unclassified_empty_or_invalid_json']}")
        
        print("\n--- 各独立分类诗词分布 (从有效分类诗词中汇总) ---")
        if report['by_individual_category']:
            for category, count in report['by_individual_category'].items():
                print(f"  '{category}': {count} 首")
        else:
            print("  未找到任何独立分类数据。")

if __name__ == "__main__":
    main()

