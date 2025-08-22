import sqlite3
import json
import xml.etree.ElementTree as ET
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加数据可视化模块到Python路径
visualizer_path = Path(__file__).parent.parent
if str(visualizer_path) not in sys.path:
    sys.path.insert(0, str(visualizer_path))

# 初始化日志系统，指定日志文件路径为主项目下的logs目录
try:
    from src.logging_config import get_logger, setup_default_logging
    # 确保主项目的logs目录存在
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    # 设置日志配置，使用主项目的logs目录
    setup_default_logging(log_file=None)  # 使用None让系统自动生成日志文件名
    logger = get_logger(__name__)
except ImportError:
    # 如果无法导入主项目的日志配置，则使用默认配置
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# 现在可以安全地导入本地模块
from data_visualizer.db_manager import DBManager
from data_visualizer.utils import db_connect
from data_visualizer.config import DB_PATHS, project_root

# 从主项目配置管理器获取情感分类XML文件路径
try:
    from src.config import config_manager
    categories_config = config_manager.get_categories_config()
    XML_PATH = categories_config.get('xml_path', os.path.join(str(project_root), 'config', 'emotion_categories.xml'))
    # 如果是相对路径，则相对于项目根目录解析
    if not os.path.isabs(XML_PATH):
        XML_PATH = os.path.join(str(project_root), XML_PATH)
except Exception as e:
    logger.warning(f"无法从主项目配置管理器获取情感分类XML路径: {e}。使用默认路径。")
    XML_PATH = os.path.join(str(project_root), 'config', 'emotion_categories.xml')


def parse_emotion_categories(xml_path: str) -> List[Tuple[str, str, str, str, int]]:
    """解析 emotion_categories.xml 文件。"""
    if not os.path.exists(xml_path):
        logger.error(f"情感分类文件未找到: {xml_path}")
        return []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    categories_data = []
    for primary_cat in root.findall('PrimaryCategory'):
        p_id = primary_cat.get('id')
        p_name_zh = primary_cat.get('name_zh')
        p_name_en = primary_cat.get('name_en')
        categories_data.append((p_id, p_name_zh, p_name_en, None, 1))
        for secondary_cat in primary_cat.findall('SecondaryCategory'):
            s_id = secondary_cat.get('id')
            s_name_zh = secondary_cat.get('name_zh')
            s_name_en = secondary_cat.get('name_en')
            if any(cat[0] == s_id for cat in categories_data):
                logger.warning(f"发现重复的二级分类ID: {s_id}。将跳过此条目。")
                continue
            categories_data.append((s_id, s_name_zh, s_name_en, p_id, 2))
    logger.info(f"从XML文件中成功解析 {len(categories_data)} 条情感分类。")
    return categories_data


def populate_emotion_categories(conn: sqlite3.Connection, categories_data: List[Tuple[str, str, str, str, int]]):
    """填充 emotion_categories 表，确保数据是最新的。"""
    cursor = conn.cursor()
    try:
        # 清空现有数据并重新插入，确保数据是最新的
        cursor.execute("DELETE FROM emotion_categories")
        cursor.executemany(
            "INSERT INTO emotion_categories (id, name_zh, name_en, parent_id, level) VALUES (?, ?, ?, ?, ?)",
            categories_data
        )
        conn.commit()
        logger.info(f"成功更新 emotion_categories 表，共插入 {len(categories_data)} 条数据。")
    except sqlite3.Error as e:
        logger.error(f"更新 emotion_categories 表失败: {e}")
        conn.rollback()
        raise


def migrate_annotations(conn: sqlite3.Connection):
    """迁移旧的标注数据到新表结构，确保数据完整性。"""
    cursor = conn.cursor()
    
    # 检查是否有需要迁移的数据
    cursor.execute(
        "SELECT COUNT(*) FROM annotations WHERE status = 'completed' AND annotation_result IS NOT NULL"
    )
    pending_migrations = cursor.fetchone()[0]
    
    if pending_migrations == 0:
        logger.info("没有需要迁移的标注数据。")
        return
    
    # 检查是否已经迁移过数据
    cursor.execute("SELECT COUNT(*) FROM sentence_annotations")
    already_migrated = cursor.fetchone()[0]
    
    if already_migrated > 0:
        logger.info("sentence_annotations 表已包含数据，为了确保数据一致性，将重新执行迁移。")
        # 清空现有的迁移数据
        cursor.execute("DELETE FROM sentence_emotion_links")
        cursor.execute("DELETE FROM sentence_annotations")
        conn.commit()
    
    logger.info("开始迁移历史标注数据...")
    cursor.execute(
        "SELECT id, poem_id, annotation_result FROM annotations WHERE status = 'completed' AND annotation_result IS NOT NULL"
    )
    annotations_to_migrate = cursor.fetchall()
    
    migration_count = 0
    try:
        for ann_id, poem_id, ann_result_json in annotations_to_migrate:
            if not ann_result_json:
                continue
            try:
                sentences = json.loads(ann_result_json)
                for sentence in sentences:
                    cursor.execute(
                        "INSERT INTO sentence_annotations (annotation_id, poem_id, sentence_uid, sentence_text) VALUES (?, ?, ?, ?)",
                        (ann_id, poem_id, sentence.get('sentence_id'), sentence.get('sentence_text'))
                    )
                    sentence_ann_id = cursor.lastrowid
                    if primary_emotion := sentence.get('primary_emotion'):
                        cursor.execute(
                            "INSERT INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary) VALUES (?, ?, ?)",
                            (sentence_ann_id, primary_emotion, 1)
                        )
                    if secondary_emotions := sentence.get('secondary_emotions', []):
                        for sec_emotion in secondary_emotions:
                            cursor.execute(
                                "INSERT INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary) VALUES (?, ?, ?)",
                                (sentence_ann_id, sec_emotion, 0)
                            )
                    migration_count += 1
            except json.JSONDecodeError:
                logger.warning(f"无法解析 annotation_id={ann_id} 的JSON数据，跳过。")
        conn.commit()
        logger.info(f"成功迁移 {len(annotations_to_migrate)} 条标注记录，共处理 {migration_count} 条句子情感数据。")
    except sqlite3.Error as e:
        logger.error(f"迁移过程中发生数据库错误: {e}")
        conn.rollback()
        raise


def setup_for_db(db_key: str, db_path: str, categories_data: List[Tuple[str, str, str, str, int]]) -> bool:
    """为指定的数据库执行完整的设置和迁移过程。"""
    logger.info(f"--- 开始为数据库 '{db_key}' 进行设置与数据迁移 ---")
    
    # 确保使用绝对路径，避免相对路径问题
    abs_db_path = os.path.abspath(db_path) if not os.path.isabs(db_path) else db_path
    
    # 确保数据库目录存在（使用绝对路径）
    os.makedirs(os.path.dirname(abs_db_path), exist_ok=True)
    
    # 步骤 1: 确保数据库和所有表结构已创建
    logger.info(f"正在初始化/验证数据库架构: {abs_db_path}...")
    try:
        # 直接初始化数据库表结构，确保每次都是最新的
        initialize_database_schema(abs_db_path)
    except Exception as e:
        logger.error(f"初始化数据库 '{db_key}' 失败: {e}", exc_info=True)
        return False

    if not categories_data:
        logger.error("无法继续，因为情感分类数据为空。")
        return False

    conn = None
    try:
        conn = db_connect(abs_db_path)
        # 步骤 2 & 3: 填充数据和迁移
        populate_emotion_categories(conn, categories_data)
        migrate_annotations(conn)
        logger.info(f"--- 数据库 '{db_key}' 设置与数据迁移完成 ---")
        return True
    except Exception as e:
        logger.error(f"为 '{db_key}' 执行设置时发生未知错误: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()


def initialize_database_schema(db_path: str):
    """初始化数据库表和索引，确保表结构是最新的。"""
    logger.info(f"检查/初始化数据库架构于 {db_path}...")
    
    # 使用主项目的数据库适配器来初始化表结构
        try:
            from src.data import get_database_adapter
            db_adapter = get_database_adapter('sqlite', self.db_path)
            db_adapter.init_database()
            logger.info("数据库架构检查/初始化完成。")
        except Exception as e:
            logger.error(f"数据库初始化错误: {e}")
            raise


def setup_all_databases(db_paths: Dict[str, str]) -> Dict[str, bool]:
    """为所有配置的数据库执行设置和迁移过程。"""
    # 解析情感分类数据（只需要解析一次）
    categories_data = parse_emotion_categories(XML_PATH)
    
    # 存储每个数据库的设置结果
    results = {}
    
    # 为每个数据库执行设置
    for db_key, db_path in db_paths.items():
        try:
            results[db_key] = setup_for_db(db_key, db_path, categories_data)
        except Exception as e:
            logger.error(f"为数据库 '{db_key}' 设置时发生未预期的错误: {e}", exc_info=True)
            results[db_key] = False
            
    return results


def main():
    """主执行函数，支持通过命令行参数选择数据库。"""
    parser = argparse.ArgumentParser(description="数据库设置与数据迁移工具。")
    parser.add_argument(
        "--db",
        type=str,
        choices=list(DB_PATHS.keys()),
        help=f"指定要设置的单个数据库。可选: {', '.join(DB_PATHS.keys())}。如果未提供，则设置所有数据库。"
    )
    args = parser.parse_args()

    if args.db:
        # 如果用户指定了一个数据库
        db_path = DB_PATHS.get(args.db)
        if not db_path:
            logger.error(f"数据库键 '{args.db}' 未在 config.py 中定义。")
            return
            
        categories_data = parse_emotion_categories(XML_PATH)
        success = setup_for_db(args.db, db_path, categories_data)
        if success:
            logger.info(f"数据库 '{args.db}' 设置完成。")
        else:
            logger.error(f"数据库 '{args.db}' 设置失败。")
    else:
        # 如果用户未指定，则处理所有已定义的数据库
        logger.info("未指定特定数据库，将为 config.py 中定义的所有数据库执行设置...")
        results = setup_all_databases(DB_PATHS)
        
        # 输出结果摘要
        successful = [db for db, success in results.items() if success]
        failed = [db for db, success in results.items() if not success]
        
        logger.info("=== 设置结果摘要 ===")
        logger.info(f"成功: {', '.join(successful) if successful else '无'}")
        if failed:
            logger.error(f"失败: {', '.join(failed)}")
        else:
            logger.info("所有数据库设置完成。")


if __name__ == '__main__':
    main()
