#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据清洗脚本
用于清洗诗词数据，标记包含缺字、空内容或其他问题的数据
通过 config/cleaning_rules.yaml 配置文件支持自定义识别字典与检测字段范围
参考 scripts/random_sample.py 的实现逻辑
"""

import argparse
import sys
import os
from typing import List, Set, Dict, Any, Optional
import yaml # 需要添加 pyyaml 依赖

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.manager import DataManager, get_data_manager
from src.config import config_manager

# --- 新增：配置加载函数 ---
def load_cleaning_config(config_path: str = None) -> dict:
    """ 加载数据清洗的配置文件
    :param config_path: 配置文件路径，默认为 config/cleaning_rules.yaml
    :return: 解析后的配置字典
    """
    if config_path is None:
        config_path = os.path.join(project_root, 'config', 'cleaning_rules.yaml')
    
    if not os.path.exists(config_path):
        print(f"警告: 配置文件 {config_path} 不存在，将使用默认规则。")
        # 返回一个默认配置或抛出异常，这里简化处理
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"成功加载配置文件: {config_path}")
        return config
    except Exception as e:
        print(f"加载配置文件 {config_path} 时出错: {e}")
        raise


def clean_poems_data(db_name: str = "default", dry_run: bool = False, config_path: str = None) -> dict:
    """
    清洗诗词数据，标记有问题的数据
    支持通过配置文件自定义识别字典与检测字段范围
    :param db_name: 数据库名称
    :param dry_run: 是否为试运行（不实际修改数据）
    :param config_path: 配置文件路径
    :return: 清洗统计信息
    """
    print(f"开始清洗数据库 '{db_name}' 的诗词数据...")
    if dry_run:
        print("【试运行模式】不会实际修改数据")
    
    # 加载配置
    config = load_cleaning_config(config_path)
    rules = config.get('rules', {})
    global_settings = config.get('global_settings', {})
    default_fields = global_settings.get('default_check_fields', ["title", "author", "full_text"])
    
    # 获取数据管理器
    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    # 统计信息
    stats = {
        'total': 0,
        'by_rule': {},  # 按规则分类的统计
        'updated': 0,   
        'errors': 0     
    }
    
    # 初始化按规则统计
    for rule_name in rules.keys():
        stats['by_rule'][rule_name] = 0
        
    try:
        # 获取所有诗词记录的ID和基本字段
        # 注意：这里我们获取所有字段，因为配置可能需要检查任何字段
        query = """
            SELECT id, title, author, full_text, data_status
            FROM poems
        """
        rows = db_adapter.execute_query(query)
        stats['total'] = len(rows)
        
        print(f"总共找到 {stats['total']} 首诗词")
        
        # 准备按规则分类的ID列表
        ids_by_rule: Dict[str, List[int]] = {rule_name: [] for rule_name in rules.keys()}
        
        # 遍历所有诗词进行检查
        for row in rows:
            poem_data = {
                'id': row[0],
                'title': row[1] or "",
                'author': row[2] or "",
                'full_text': row[3] or "",
                'data_status': row[4]
            }
            poem_id = poem_data['id']
            
            # 按优先级检查规则
            matched_rule = None
            for rule_name, rule_config in rules.items():
                if not rule_config.get('enabled', False):
                    continue
                
                if rule_name == 'missing_char':
                    fields = rule_config.get('fields', default_fields)
                    symbols = rule_config.get('symbols', ["□"])
                    if contains_symbols_in_fields(poem_data, symbols, fields):
                        matched_rule = rule_name
                        break  # 高优先级，匹配后退出
                
                elif rule_name == 'empty_content':
                    if is_empty_content(poem_data, rule_config):
                        matched_rule = rule_name
                        break  # 中优先级
                
                elif rule_name == 'suspicious_symbols':
                    if contains_suspicious_symbols_in_brackets(poem_data, rule_config):
                        matched_rule = rule_name
                        break  # 低优先级
            
            if matched_rule:
                ids_by_rule[matched_rule].append(poem_id)
                stats['by_rule'][matched_rule] += 1
            elif rules.get('invalid_status', {}).get('enabled', False):
                # 如果没有匹配任何规则，并且启用了 invalid_status 检查，则检查状态
                valid_statuses = rules['invalid_status'].get('valid_statuses', 
                                                            ['active', 'missing_char', 'empty_content', 'suspicious'])
                current_status = poem_data['data_status']
                if current_status not in valid_statuses:
                    ids_by_rule['invalid_status'].append(poem_id)
                    stats['by_rule']['invalid_status'] += 1
        
        # 打印发现的统计信息
        for rule_name, count in stats['by_rule'].items():
            print(f"发现 {count} 首匹配 '{rule_name}' 规则的诗词")
        
        # 更新数据库中的数据状态字段
        if not dry_run:
            total_updated = 0
            processed_ids = set()  # 跟踪已处理的ID，避免重复更新
            
            # 按规则顺序更新，确保优先级
            rule_order = ['missing_char', 'empty_content', 'suspicious_symbols', 'invalid_status']
            for rule_name in rule_order:
                if rule_name not in rules or not rules[rule_name].get('enabled', False):
                    continue
                
                ids_to_update = [pid for pid in ids_by_rule[rule_name] if pid not in processed_ids]
                if not ids_to_update:
                    continue
                
                target_status = rules[rule_name]['status']
                placeholders = ','.join('?' * len(ids_to_update))
                update_query = f"""
                    UPDATE poems 
                    SET data_status = ?
                    WHERE id IN ({placeholders}) AND data_status != ?
                """
                try:
                    # 传递 target_status 两次，一次用于 SET，一次用于 WHERE 条件
                    params = [target_status] + list(ids_to_update) + [target_status]
                    rowcount = db_adapter.execute_update(update_query, tuple(params))
                    total_updated += rowcount
                    processed_ids.update(ids_to_update)
                    print(f"已将 {rowcount} 首诗词标记为 '{target_status}' 状态 (来自规则: {rule_name})")
                except Exception as e:
                    print(f"更新诗词状态 (规则: {rule_name}) 时出错: {e}")
                    stats['errors'] += len(ids_to_update)
            
            stats['updated'] = total_updated
            
        else:
            # 试运行模式
            stats['updated'] = sum(len(ids) for ids in ids_by_rule.values())
            print(f"试运行模式：将更新 {stats['updated']} 首诗词的状态")
        
        print("数据清洗完成")
        return stats
        
    except Exception as e:
        print(f"数据清洗过程中发生错误: {e}")
        stats['errors'] = stats['total']
        return stats

def clean_punctuation(text: str, punctuation_to_clean: str) -> str:
    """ 清除文本中的指定标点符号
    :param text: 原始文本
    :param punctuation_to_clean: 要清除的标点符号字符串
    :return: 清除标点符号后的文本
    """
    cleaned = text
    for p in punctuation_to_clean:
        cleaned = cleaned.replace(p, '')
    return cleaned

def contains_symbols_in_fields(poem_data: dict, symbols: List[str], fields: List[str]) -> bool:
    """ 检查指定字段的内容是否包含给定的符号列表中的任意一个符号。
    
    :param poem_data: 包含诗词字段的字典 (e.g., {'title': '...', 'full_text': '...'})
    :param symbols: 要查找的符号列表
    :param fields: 要检查的字段列表
    :return: 如果找到任何符号则返回 True，否则返回 False
    """
    content_to_check = "".join(poem_data.get(field, "") or "" for field in fields)
    for symbol in symbols:
        if symbol in content_to_check:
            return True
    return False

def is_empty_content(poem_data: dict, config_rule: dict) -> bool:
    """ 根据配置判断内容是否为空。
    
    :param poem_data: 包含诗词字段的字典
    :param config_rule: 配置文件中 empty_content 规则部分
    :return: 如果内容为空则返回 True，否则返回 False
    """
    fields_to_check = config_rule.get('fields', [])
    punctuation = config_rule.get('punctuation_to_clean', '')
    
    for field in fields_to_check:
        text = poem_data.get(field, "") or ""
        cleaned_text = clean_punctuation(text, punctuation)
        if cleaned_text.strip():
            return False  # 只要有一个字段不为空，就不算空内容
    return True  # 所有指定字段都为空内容

import re
def contains_suspicious_symbols_in_brackets(poem_data: dict, config_rule: dict) -> bool:
    """ 检查指定字段是否在括号内包含可疑符号。
    
    :param poem_data: 包含诗词字段的字典
    :param config_rule: 配置文件中 suspicious_symbols 规则部分
    :return: 如果在括号内找到可疑符号则返回 True，否则返回 False
    """
    fields_to_check = config_rule.get('fields', [])
    suspicious_symbols = config_rule.get('symbols', [])
    bracket_patterns = config_rule.get('bracket_patterns', [])
    
    content = "".join(poem_data.get(field, "") or "" for field in fields_to_check)
    for pattern in bracket_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            for symbol in suspicious_symbols:
                if symbol in match:
                    return True
    return False


def reset_data_status(db_name: str = "default", dry_run: bool = False, config_path: str = None) -> dict:
    """
    重置所有诗词的数据状态
    支持通过配置文件自定义有效的状态列表和重置后的默认状态
    :param db_name: 数据库名称
    :param dry_run: 是否为试运行（不实际修改数据）
    :param config_path: 配置文件路径
    :return: 重置统计信息
    """
    print(f"开始重置数据库 '{db_name}' 的诗词数据状态...")
    if dry_run:
        print("【试运行模式】不会实际修改数据")
    
    # 加载配置
    config = load_cleaning_config(config_path)
    invalid_status_rule = config.get('rules', {}).get('invalid_status', {})
    reset_to_status = invalid_status_rule.get('reset_to_status', 'active')
    valid_statuses = invalid_status_rule.get('valid_statuses', ['active', 'missing_char', 'empty_content', 'suspicious'])
    
    # 获取数据管理器
    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    stats = {
        'total': 0,
        'reset': 0,       
        'errors': 0
    }
    
    try:
        # 构建 NOT IN 子句
        placeholders = ','.join('?' * len(valid_statuses))
        count_query = f"""
            SELECT COUNT(*) FROM poems 
            WHERE data_status NOT IN ({placeholders}) OR data_status IS NULL OR data_status = ''
        """
        rows = db_adapter.execute_query(count_query, tuple(valid_statuses))
        stats['total'] = rows[0][0] if rows else 0
        
        print(f"找到 {stats['total']} 首状态异常的诗词（包括空状态）")
        
        if stats['total'] > 0:
            if not dry_run:
                update_query = "UPDATE poems SET data_status = ?"
                try:
                    rowcount = db_adapter.execute_update(update_query, (reset_to_status,))
                    stats['reset'] = rowcount
                    print(f"已将 {rowcount} 首诗词的状态重置为 '{reset_to_status}'")
                except Exception as e:
                    print(f"重置诗词状态时出错: {e}")
                    stats['errors'] = stats['total']
            else:
                stats['reset'] = stats['total']
                print(f"试运行模式：将重置 {stats['reset']} 首诗词的状态")
        
        print("数据状态重置完成")
        return stats
        
    except Exception as e:
        print(f"重置数据状态过程中发生错误: {e}")
        stats['errors'] = stats['total']
        return stats


def get_cleaning_report(db_name: str = "default", config_path: str = None) -> dict:
    """
    获取数据清洗报告
    支持通过配置文件自定义有效的状态列表
    :param db_name: 数据库名称
    :param config_path: 配置文件路径
    :return: 清洗报告
    """
    print(f"生成数据库 '{db_name}' 的数据清洗报告...")
    
    # 加载配置
    config = load_cleaning_config(config_path)
    invalid_status_rule = config.get('rules', {}).get('invalid_status', {})
    valid_statuses = invalid_status_rule.get('valid_statuses', ['active', 'missing_char', 'empty_content', 'suspicious'])
    
    # 获取数据管理器
    data_manager = get_data_manager(db_name)
    db_adapter = data_manager.db_adapter
    
    report = {
        'total': 0,
        'by_status': {},       
        'null_status': 0,
        'empty_status': 0,
        'other_invalid': 0,  # 其他无效状态
    }
    
    # 初始化 by_status
    for status in valid_statuses:
        report['by_status'][status] = 0

    try:
        # 动态构建 CASE WHEN 子句
        case_when_clauses = []
        for status in valid_statuses:
            case_when_clauses.append(f"COUNT(CASE WHEN data_status = '{status}' THEN 1 END) as {status}")
        case_when_str = ", ".join(case_when_clauses)
        
        query = f"""
            SELECT 
                COUNT(*) as total,
                {case_when_str},
                COUNT(CASE WHEN data_status IS NULL THEN 1 END) as null_status,
                COUNT(CASE WHEN data_status = '' THEN 1 END) as empty_status,
                COUNT(CASE WHEN data_status NOT IN ({','.join('?' * len(valid_statuses))}) AND data_status IS NOT NULL AND data_status != '' THEN 1 END) as other_invalid
            FROM poems
        """
        # 注意：SQLite 的 ? 占位符在字符串拼接中不能直接用于列名或表名，但对于值是安全的。
        # 上面的查询中，列名是硬编码的，值部分用占位符。
        rows = db_adapter.execute_query(query, tuple(valid_statuses))
        
        if rows:
            row = rows[0]
            report['total'] = row[0] or 0
            for i, status in enumerate(valid_statuses, start=1):  # start=1 because total is index 0
                report['by_status'][status] = row[i] or 0
            report['null_status'] = row[len(valid_statuses) + 1] or 0
            report['empty_status'] = row[len(valid_statuses) + 2] or 0
            report['other_invalid'] = row[len(valid_statuses) + 3] or 0  # 其他无效状态的数量
        
        return report
        
    except Exception as e:
        print(f"生成清洗报告时出错: {e}")
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗词数据清洗工具')
    parser.add_argument('--db-name', type=str, default='default', help='数据库名称（从配置文件中获取）')
    parser.add_argument('--clean', action='store_true', help='执行数据清洗')
    parser.add_argument('--reset', action='store_true', help='重置所有数据状态为active')
    parser.add_argument('--report', action='store_true', help='生成清洗报告')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式，不实际修改数据')
    parser.add_argument('--config', type=str, help='自定义配置文件路径 (默认: config/cleaning_rules.yaml)')
    
    args = parser.parse_args()
    
    # 检查参数
    actions = [args.clean, args.reset, args.report]
    if sum(actions) == 0:
        parser.print_help()
        sys.exit(1)
    elif sum(actions) > 1:
        print("错误：只能指定一个操作（--clean, --reset, --report）")
        sys.exit(1)
    
    config_path = args.config  # 传递配置文件路径
    
    # 执行相应的操作
    if args.clean:
        stats = clean_poems_data(args.db_name, args.dry_run, config_path)
        print("\n清洗统计:")
        print(f"  总诗词数: {stats['total']}")
        for rule_name, count in stats['by_rule'].items():
            print(f"  匹配规则 '{rule_name}': {count}")
        print(f"  已更新: {stats['updated']}")
        print(f"  错误: {stats['errors']}")
        
    elif args.reset:
        stats = reset_data_status(args.db_name, args.dry_run, config_path)
        print("\n重置统计:")
        print(f"  状态异常诗词: {stats['total']}")
        print(f"  已重置: {stats['reset']}")
        print(f"  错误: {stats['errors']}")
        
    elif args.report:
        report = get_cleaning_report(args.db_name, config_path)
        print("\n数据清洗报告:")
        print(f"  总诗词数: {report['total']}")
        for status, count in report['by_status'].items():
            print(f"  状态 '{status}': {count}")
        print(f"  状态为NULL: {report['null_status']}")
        print(f"  状态为空字符串: {report['empty_status']}")
        print(f"  其他无效状态: {report['other_invalid']}")  # 打印其他无效状态的数量

if __name__ == "__main__":
    main()