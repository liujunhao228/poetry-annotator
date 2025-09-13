"""
数据清洗插件实现
"""

import re
import sqlite3
from typing import Dict, Any, List
from src.data_cleaning.plugin import DataCleaningPlugin
from src.plugin_system.manager import get_plugin_manager
from src.data import get_data_manager
from src.config.schema import PluginConfig


class DefaultDataCleaningPlugin(DataCleaningPlugin):
    """默认数据清洗插件实现"""

    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        self.settings = plugin_config.settings
        
    def get_name(self) -> str:
        """获取插件名称"""
        return "default_data_cleaning"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "默认数据清洗插件，提供基础的数据清洗功能"
        
    def clean_data(self, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        清洗数据
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            清洗统计信息
        """
        print(f"开始清洗数据库 '{db_name}' 的诗词数据...")
        if dry_run:
            print("【试运行模式】不会实际修改数据")

        # 获取插件配置
        rules = self.settings.get("rules", {})
        global_settings = self.settings.get("global_settings", {})
        default_fields = global_settings.get('default_check_fields', ["title", "author", "full_text"])

        # 获取数据管理器
        data_manager = get_data_manager(db_name)
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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
            rows = cursor.execute(query).fetchall()
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
                        if self._contains_symbols_in_fields(poem_data, symbols, fields):
                            matched_rule = rule_name
                            break  # 高优先级，匹配后退出

                    elif rule_name == 'empty_content':
                        if self._is_empty_content(poem_data, rule_config):
                            matched_rule = rule_name
                            break  # 中优先级

                    elif rule_name == 'suspicious_symbols':
                        if self._contains_suspicious_symbols_in_brackets(poem_data, rule_config):
                            matched_rule = rule_name
                            break  # 低优先级

                if matched_rule:
                    ids_by_rule[matched_rule].append(poem_id)
                    stats['by_rule'][matched_rule] += 1
                elif rules.get('invalid_status', {}).get('enabled', False):
                    # 如果没有匹配任何规则，并且启用了 invalid_status 检查，则检查状态
                    valid_statuses = rules['invalid_status'].get('valid_statuses',
                                                                ['active', 'missing_char', 'empty_content',
                                                                 'suspicious'])
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
                        cursor.execute(update_query, params)
                        total_updated += cursor.rowcount
                        processed_ids.update(ids_to_update)
                        print(f"已将 {cursor.rowcount} 首诗词标记为 '{target_status}' 状态 (来自规则: {rule_name})")
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

    def reset_data_status(self, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        重置数据状态
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            重置统计信息
        """
        print(f"开始重置数据库 '{db_name}' 的诗词数据状态...")
        if dry_run:
            print("【试运行模式】不会实际修改数据")

        # 获取插件配置
        rules = self.settings.get("rules", {})
        invalid_status_rule = rules.get('invalid_status', {})
        reset_to_status = invalid_status_rule.get('reset_to_status', 'active')
        valid_statuses = invalid_status_rule.get('valid_statuses', ['active', 'missing_char', 'empty_content', 'suspicious'])

        # 获取数据管理器
        data_manager = get_data_manager(db_name)
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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
            rows = cursor.execute(count_query, tuple(valid_statuses)).fetchall()
            stats['total'] = rows[0][0] if rows else 0

            print(f"找到 {stats['total']} 首状态异常的诗词（包括空状态）")

            if stats['total'] > 0:
                if not dry_run:
                    update_query = "UPDATE poems SET data_status = ?"
                    try:
                        cursor.execute(update_query, (reset_to_status,))
                        stats['reset'] = cursor.rowcount
                        print(f"已将 {cursor.rowcount} 首诗词的状态重置为 '{reset_to_status}'")
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

    def generate_report(self, db_name: str = "default") -> Dict[str, Any]:
        """
        生成清洗报告
        
        Args:
            db_name: 数据库名称
            
        Returns:
            清洗报告
        """
        print(f"生成数据库 '{db_name}' 的清洗报告...")

        # 获取数据管理器
        data_manager = get_data_manager(db_name)
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        report = {
            "total_poems": 0,
            "by_status": {},
            "by_rule": {},
        }

        try:
            # 获取总诗词数
            total_query = "SELECT COUNT(*) FROM poems"
            total_rows = cursor.execute(total_query).fetchall()
            report["total_poems"] = total_rows[0][0] if total_rows else 0

            # 获取按状态分类的统计
            status_query = "SELECT data_status, COUNT(*) FROM poems GROUP BY data_status"
            status_rows = cursor.execute(status_query).fetchall()
            for row in status_rows:
                status = row[0] if row[0] is not None else "NULL"
                count = row[1]
                report["by_status"][status] = count

            # 获取按规则分类的统计（如果有相关数据）
            # 这里假设规则信息存储在插件配置中
            rules = self.settings.get("rules", {})
            for rule_name in rules.keys():
                report["by_rule"][rule_name] = 0

            print("清洗报告生成完成。")
            return report

        except Exception as e:
            print(f"生成清洗报告时发生错误: {e}")
            return report

    def _clean_punctuation(self, text: str, punctuation_to_clean: str) -> str:
        """ 清除文本中的指定标点符号
        :param text: 原始文本
        :param punctuation_to_clean: 要清除的标点符号字符串
        :return: 清除标点符号后的文本
        """
        cleaned = text
        for p in punctuation_to_clean:
            cleaned = cleaned.replace(p, '')
        return cleaned

    def _contains_symbols_in_fields(self, poem_data: dict, symbols: List[str], fields: List[str]) -> bool:
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

    def _is_empty_content(self, poem_data: dict, config_rule: dict) -> bool:
        """ 根据配置判断内容是否为空。

        :param poem_data: 包含诗词字段的字典
        :param config_rule: 配置文件中 empty_content 规则部分
        :return: 如果内容为空则返回 True，否则返回 False
        """
        fields_to_check = config_rule.get('fields', [])
        punctuation = config_rule.get('punctuation_to_clean', '')

        for field in fields_to_check:
            text = poem_data.get(field, "") or ""
            cleaned_text = self._clean_punctuation(text, punctuation)
            if cleaned_text.strip():
                return False  # 只要有一个字段不为空，就不算空内容
        return True  # 所有指定字段都为空内容

    def _contains_suspicious_symbols_in_brackets(self, poem_data: dict, config_rule: dict) -> bool:
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

    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作（实现预处理插件接口）
        
        Args:
            data: 输入数据
            **kwargs: 额外参数，包括：
                - db_name: 数据库名称（可选）
                - dry_run: 是否为试运行模式（可选）
                - action: 操作类型（'clean', 'reset', 'report'）
                
        Returns:
            处理后的数据（包含清洗统计信息）
        """
        db_name = kwargs.get('db_name', 'default')
        dry_run = kwargs.get('dry_run', False)
        action = kwargs.get('action', 'clean')
        
        if action == 'clean':
            result = self.clean_data(db_name, dry_run)
        elif action == 'reset':
            result = self.reset_data_status(db_name, dry_run)
        elif action == 'report':
            result = self.generate_report(db_name)
        else:
            raise ValueError(f"不支持的操作类型: {action}")
        
        # 将结果添加到数据中返回
        data['preprocessing_result'] = result
        return data