"""
清洗报告生成器，负责生成清洗报告。
"""

from typing import Dict, Any
from src.data import get_data_manager


class CleaningReportGenerator:
    """
    清洗报告生成器，负责生成清洗报告。
    """

    def __init__(self, rule_manager):
        """
        初始化清洗报告生成器。

        Args:
            rule_manager: 清洗规则管理器实例。
        """
        self.rule_manager = rule_manager

    def get_cleaning_report(self, db_name: str = "default") -> dict:
        """
        获取数据清洗报告
        支持通过配置文件自定义有效的状态列表
        :param db_name: 数据库名称
        :return: 清洗报告
        """
        print(f"生成数据库 '{db_name}' 的数据清洗报告...")

        # 加载配置
        rules = self.rule_manager.get_rules()
        invalid_status_rule = rules.get('invalid_status', {})
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
            rows = cursor.execute(query, tuple(valid_statuses)).fetchall()

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