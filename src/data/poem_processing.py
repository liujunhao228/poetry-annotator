"""
诗词分类核心处理器
"""

import json
import logging
import sqlite3
from typing import Dict, Any, List
from pathlib import Path

from src.plugin_system.manager import get_plugin_manager
from src.plugin_system.plugin_types import PluginType
from src.plugin_system.interfaces import PreprocessingPlugin # Import the generic PreprocessingPlugin

# 配置日志
logger = logging.getLogger(__name__)


class PoemClassificationCore:
    """诗词分类核心处理器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.plugin_manager = get_plugin_manager()
        
        # 获取所有已注册的预处理插件，并筛选出具有分类功能的插件
        self.classification_plugins: List[PreprocessingPlugin] = []
        for plugin in self.plugin_manager.get_plugins_by_type(PluginType.PREPROCESSING):
            # 动态检查插件是否具有 classify_poem 和 get_supported_categories 方法
            if hasattr(plugin, 'classify_poem') and callable(getattr(plugin, 'classify_poem')) and \
               hasattr(plugin, 'get_supported_categories') and callable(getattr(plugin, 'get_supported_categories')):
                self.classification_plugins.append(plugin)
        
        logger.info(f"找到 {len(self.classification_plugins)} 个诗词分类插件")
    
    def classify_poems_data(self, data_manager: Any, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        使用插件对诗词数据进行分类
        
        :param data_manager: 数据管理器实例
        :param db_name: 数据库名称
        :param dry_run: 是否为试运行（不实际修改数据）
        :return: 分类统计信息
        """
        logger.info(f"开始使用插件对数据库 '{db_name}' 的诗词数据进行分类...")
        if dry_run:
            logger.info("【试运行模式】不会实际修改数据")
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 统计信息
        stats = {
            "total_poems_scanned": 0,
            "classified_this_run": 0,
            "updated_in_db": 0,
            "errors": 0,
            "skipped_unchanged": 0,
            "classification_distribution": {},
        }

        # 初始化按分类统计
        all_categories = set()
        for plugin in self.classification_plugins:
            try:
                # 调用插件的 get_supported_categories 方法
                categories = plugin.get_supported_categories()
                all_categories.update(categories)
            except Exception as e:
                logger.warning(f"插件 {plugin.get_name()} 获取支持分类时出错: {e}")
                
        for category in all_categories:
            stats["classification_distribution"][category] = 0

        try:
            # 获取所有诗词记录
            query = "SELECT id, title, full_text, pre_classification FROM poems"
            rows = cursor.execute(query).fetchall()
            stats["total_poems_scanned"] = len(rows)

            logger.info(f"总共找到 {stats['total_poems_scanned']} 首诗词待处理。")

            # 存储待更新的诗词信息
            poems_to_update: Dict[int, List[str]] = {}

            # 遍历所有诗词进行分类
            for row in rows:
                poem_id = row[0]
                current_title = row[1] or ""
                current_full_text = row[2] or ""
                existing_classification_json = row[3]

                poem_data = {
                    "id": poem_id,
                    "title": current_title,
                    "full_text": current_full_text,
                }

                # 收集所有插件的分类结果
                all_categories_for_poem: set = set()
                for plugin in self.classification_plugins:
                    try:
                        # 调用插件的 classify_poem 方法
                        categories = plugin.classify_poem(poem_data)
                        all_categories_for_poem.update(categories)
                    except Exception as e:
                        logger.error(f"插件 {plugin.get_name()} 分类诗词 {poem_id} 时出错: {e}")
                        stats["errors"] += 1

                # 将分类列表排序，以确保 JSON 字符串的一致性
                new_classification_list = sorted(list(all_categories_for_poem))

                # 将分类列表转换为 JSON 字符串或None
                if new_classification_list:
                    new_classification_json = json.dumps(
                        new_classification_list, ensure_ascii=False
                    )
                else:
                    new_classification_json = None

                # 比较新分类与现有分类，判断是否需要更新
                parsed_existing_categories = []
                if existing_classification_json:
                    try:
                        parsed_existing = json.loads(existing_classification_json)
                        if isinstance(parsed_existing, list):
                            parsed_existing_categories = sorted(parsed_existing)
                    except json.JSONDecodeError:
                        parsed_existing_categories = []

                existing_classification_json_effective = (
                    json.dumps(parsed_existing_categories, ensure_ascii=False)
                    if parsed_existing_categories
                    else None
                )

                # 如果新分类与数据库中现有分类不同，则标记为待更新
                if (
                    new_classification_json
                    != existing_classification_json_effective
                ):
                    poems_to_update[poem_id] = new_classification_list
                    stats["classified_this_run"] += 1
                else:
                    stats["skipped_unchanged"] += 1

                # 更新分类分布统计
                for cat in new_classification_list:
                    stats["classification_distribution"][cat] += 1

            logger.info(
                f"\n已为 {len(poems_to_update)} 首诗词确定分类 (共扫描 {stats['total_poems_scanned']} 首)。"
            )
            logger.info(
                f"因分类结果未改变而跳过更新的诗词有：{stats['skipped_unchanged']} 首。"
            )

            # 如果不是试运行模式，则执行数据库更新
            if not dry_run:
                if poems_to_update:
                    try:
                        update_count = 0
                        for poem_id, categories_list in poems_to_update.items():
                            categories_json = (
                                json.dumps(categories_list, ensure_ascii=False)
                                if categories_list
                                else None
                            )

                            update_query = """
                                UPDATE poems 
                                SET pre_classification = ?
                                WHERE id = ?
                            """
                            cursor.execute(update_query, (categories_json, poem_id))
                            update_count += 1

                        conn.commit()
                        stats["updated_in_db"] = update_count
                        logger.info(
                            f"成功更新了数据库中 {stats['updated_in_db']} 首诗词的分类信息。"
                        )
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"数据库更新时出错: {e}")
                        stats["errors"] += len(poems_to_update)
                else:
                    logger.info("没有诗词需要更新分类。")
            else:
                stats["updated_in_db"] = len(poems_to_update)
                logger.info(
                    f"试运行模式：将有 {stats['updated_in_db']} 首诗词被更新。"
                )

            logger.info("诗词分类完成。")
            return stats

        except Exception as e:
            logger.error(f"诗词分类过程中发生意外错误: {e}")
            stats["errors"] = stats["total_poems_scanned"]
            return stats
    
    def reset_pre_classification(self, data_manager: Any, db_name: str = "default", dry_run: bool = False) -> Dict[str, Any]:
        """
        重置所有诗词的预分类字段
        
        :param data_manager: 数据管理器实例
        :param db_name: 数据库名称
        :param dry_run: 是否为试运行（不实际修改数据）
        :return: 重置统计信息
        """
        logger.info(f"开始重置数据库 '{db_name}' 的诗词预分类...")
        if dry_run:
            logger.info("【试运行模式】不会实际修改数据")
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        stats = {
            "total_with_classification": 0,
            "reset_count": 0,
            "errors": 0,
        }

        try:
            # 统计当前分类字段非 NULL 或非空字符串的诗词数量
            count_query = """
                SELECT COUNT(*) FROM poems 
                WHERE pre_classification IS NOT NULL AND pre_classification != ''
            """
            rows = cursor.execute(count_query).fetchall()
            stats["total_with_classification"] = (
                rows[0][0] if rows and rows[0] else 0
            )

            logger.info(
                f"找到 {stats['total_with_classification']} 首具有现有预分类数据的诗词。"
            )

            if stats["total_with_classification"] > 0:
                if not dry_run:
                    # 将所有预分类字段设置为 NULL
                    update_query = """
                        UPDATE poems SET pre_classification = NULL
                    """

                    try:
                        cursor.execute(update_query)
                        stats["reset_count"] = cursor.rowcount
                        logger.info(
                            f"已将 {stats['reset_count']} 首诗词的预分类重置为 NULL。"
                        )
                    except Exception as e:
                        logger.error(f"重置诗词预分类时出错: {e}")
                        stats["errors"] = stats["total_with_classification"]
                else:
                    stats["reset_count"] = stats["total_with_classification"]
                    logger.info(
                        f"试运行模式：将重置 {stats['reset_count']} 首诗词的预分类。"
                    )
            else:
                logger.info(
                    "没有诗词具有现有预分类数据需要重置。"
                )

            logger.info("预分类重置完成。")
            return stats

        except Exception as e:
            logger.error(f"重置预分类过程中发生意外错误: {e}")
            stats["errors"] = stats["total_with_classification"]
            return stats
    
    def get_classification_report(self, data_manager: Any, db_name: str = "default") -> Dict[str, Any]:
        """
        生成分类报告
        
        :param data_manager: 数据管理器实例
        :param db_name: 数据库名称
        :return: 分类报告
        """
        logger.info(f"生成数据库 '{db_name}' 的分类报告...")
        
        # 获取数据库路径
        db_configs = data_manager.separate_db_manager.db_configs if hasattr(data_manager, 'separate_db_manager') else {}
        raw_data_db_path = db_configs.get('raw_data', f"data/{db_name}/raw_data.db")
        
        # 获取数据库连接
        conn = sqlite3.connect(raw_data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        report = {
            "total_poems": 0,
            "effectively_classified": 0,
            "unclassified_null": 0,
            "unclassified_empty_string": 0,
            "unclassified_empty_or_invalid_json": 0,
            "by_individual_category": {},
            "multiple_categories_poems": 0,
        }

        try:
            # 首先，从数据库获取整体统计信息
            summary_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN pre_classification IS NULL THEN 1 END) as null_count,
                    COUNT(CASE WHEN pre_classification = '' THEN 1 END) as empty_string_count
                FROM poems
            """
            summary_rows = cursor.execute(summary_query).fetchall()
            if summary_rows and summary_rows[0]:
                report["total_poems"] = summary_rows[0][0]
                report["unclassified_null"] = summary_rows[0][1]
                report["unclassified_empty_string"] = summary_rows[0][2]

            # 获取所有非 NULL 和非空字符串的分类数据
            classification_data_query = """
                SELECT pre_classification
                FROM poems
                WHERE pre_classification IS NOT NULL AND pre_classification != ''
            """
            classified_rows = cursor.execute(classification_data_query).fetchall()

            for row in classified_rows:
                classification_json_str = row[0]

                # 根据解析的 JSON 进行分类和计数
                try:
                    categories = json.loads(classification_json_str)
                    if isinstance(categories, list) and categories:
                        report["effectively_classified"] += 1
                        if len(categories) > 1:
                            report["multiple_categories_poems"] += 1

                        for category in categories:
                            if isinstance(category, str):
                                report["by_individual_category"][category] = (
                                    report["by_individual_category"].get(category, 0) + 1
                                )
                            else:
                                report["unclassified_empty_or_invalid_json"] += 1
                                break
                    else:
                        report["unclassified_empty_or_invalid_json"] += 1
                except json.JSONDecodeError:
                    report["unclassified_empty_or_invalid_json"] += 1
                except Exception as e:
                    logger.warning(f"警告: 处理分类 '{classification_json_str}' 时出错: {e}")
                    report["unclassified_empty_or_invalid_json"] += 1

            # 确保所有插件支持的类别都在报告中显示
            all_defined_categories = set()
            for plugin in self.classification_plugins:
                try:
                    # 调用插件的 get_supported_categories 方法
                    categories = plugin.get_supported_categories()
                    all_defined_categories.update(categories)
                except Exception as e:
                    logger.warning(f"插件 {plugin.get_name()} 获取支持分类时出错: {e}")

            for category in sorted(list(all_defined_categories)):
                report["by_individual_category"].setdefault(category, 0)

            # 对分类统计结果按数量降序排序
            report["by_individual_category"] = dict(
                sorted(
                    report["by_individual_category"].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )

            logger.info("分类报告生成完成。")
            return report

        except Exception as e:
            logger.error(f"生成分类报告时发生意外错误: {e}")
            return report
