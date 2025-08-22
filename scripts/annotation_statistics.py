#!/usr/bin/env python3
"""
诗词情感标注统计脚本
用于统计指定数据库的标注情况
"""

import sys
import os
from pathlib import Path
import sqlite3
import argparse
import pandas as pd

# 添加项目根目录到Python路径，确保能正确导入src下的模块
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入配置管理器
try:
    from src.config import config_manager
except ImportError:
    print("错误: 无法导入配置管理器，请检查项目结构")
    sys.exit(1)

def get_db_path(db_name: str) -> str:
    """根据数据库名称获取数据库路径"""
    db_config = config_manager.get_database_config()
    
    # 处理新的多数据库配置
    if 'db_paths' in db_config:
        db_paths = db_config['db_paths']
        if db_name in db_paths:
            db_path = db_paths[db_name]
            # 如果是相对路径，则相对于项目根目录解析
            if not os.path.isabs(db_path):
                db_path = os.path.join(str(project_root), db_path)
            return db_path
        else:
            raise ValueError(f"数据库 '{db_name}' 未在配置中定义。")
    # 回退到旧的单数据库配置
    elif 'db_path' in db_config:
        db_path = db_config['db_path']
        if not os.path.isabs(db_path):
            db_path = os.path.join(str(project_root), db_path)
        return db_path
    else:
        raise ValueError("配置文件中未找到数据库路径配置。")

def connect_database(db_path: str) -> sqlite3.Connection:
    """连接到SQLite数据库"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

def execute_query(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list:
    """执行查询并返回结果"""
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()

def get_unique_annotation_stats(conn: sqlite3.Connection) -> dict:
    """获取去重的标注统计信息"""
    stats = {}
    
    # 查询去重后的已标注诗词数
    query_poems = """
        SELECT COUNT(DISTINCT sa.poem_id) AS unique_annotated_poems
        FROM sentence_annotations sa
        JOIN annotations a ON sa.annotation_id = a.id
        WHERE a.status = 'completed'
    """
    result = execute_query(conn, query_poems)
    stats['unique_annotated_poems'] = result[0]['unique_annotated_poems'] if result else 0
    
    # 查询去重后的已标注分句数
    query_sentences = """
        SELECT COUNT(DISTINCT sa.poem_id || '-' || sa.sentence_uid) AS unique_annotated_sentences
        FROM sentence_annotations sa
        JOIN annotations a ON sa.annotation_id = a.id
        WHERE a.status = 'completed'
    """
    result = execute_query(conn, query_sentences)
    stats['unique_annotated_sentences'] = result[0]['unique_annotated_sentences'] if result else 0
    
    return stats

def get_model_annotation_stats(conn: sqlite3.Connection) -> list:
    """获取各模型的标注统计信息"""
    stats = []
    
    # 按模型统计标注诗词数
    query_poems = """
        SELECT 
            a.model_identifier, 
            COUNT(DISTINCT sa.poem_id) AS annotated_poems_by_model
        FROM sentence_annotations sa
        JOIN annotations a ON sa.annotation_id = a.id
        WHERE a.status = 'completed'
        GROUP BY a.model_identifier
    """
    result_poems = execute_query(conn, query_poems)
    poems_by_model = {row['model_identifier']: row['annotated_poems_by_model'] for row in result_poems}
    
    # 按模型统计标注分句数
    query_sentences = """
        SELECT 
            a.model_identifier, 
            COUNT(sa.id) AS annotated_sentences_by_model
        FROM sentence_annotations sa
        JOIN annotations a ON sa.annotation_id = a.id
        WHERE a.status = 'completed'
        GROUP BY a.model_identifier
    """
    result_sentences = execute_query(conn, query_sentences)
    sentences_by_model = {row['model_identifier']: row['annotated_sentences_by_model'] for row in result_sentences}
    
    # 合并结果
    all_models = set(poems_by_model.keys()) | set(sentences_by_model.keys())
    for model in all_models:
        stats.append({
            'model_identifier': model,
            'annotated_poems': poems_by_model.get(model, 0),
            'annotated_sentences': sentences_by_model.get(model, 0)
        })
    
    return stats

def get_unduplicated_annotation_stats(conn: sqlite3.Connection) -> dict:
    """获取不去重的标注统计信息"""
    stats = {}
    
    # 不去重的已标注总诗词数
    query_poems = """
        SELECT COUNT(DISTINCT sa.poem_id) AS total_annotated_poems_unduplicated
        FROM annotations a
        JOIN sentence_annotations sa ON a.id = sa.annotation_id
        WHERE a.status = 'completed'
    """
    result = execute_query(conn, query_poems)
    stats['total_annotated_poems_unduplicated'] = result[0]['total_annotated_poems_unduplicated'] if result else 0
    
    # 不去重的已标注总分句数
    query_sentences = """
        SELECT COUNT(sa.id) AS total_annotated_sentences_unduplicated
        FROM sentence_annotations sa
        JOIN annotations a ON sa.annotation_id = a.id
        WHERE a.status = 'completed'
    """
    result = execute_query(conn, query_sentences)
    stats['total_annotated_sentences_unduplicated'] = result[0]['total_annotated_sentences_unduplicated'] if result else 0
    
    return stats

def format_statistics(unique_stats: dict, model_stats: list, unduplicated_stats: dict) -> pd.DataFrame:
    """将统计信息格式化为DataFrame"""
    data = []
    
    # 添加去重统计
    data.append({
        'statistic_type': 'unique_total_poems',
        'model_identifier': 'ALL',
        'value': unique_stats['unique_annotated_poems'],
        'description': '去重后的已标注总诗词数'
    })
    
    data.append({
        'statistic_type': 'unique_total_sentences',
        'model_identifier': 'ALL',
        'value': unique_stats['unique_annotated_sentences'],
        'description': '去重后的已标注总分句数'
    })
    
    # 添加各模型统计
    for stat in model_stats:
        data.append({
            'statistic_type': 'model_poems',
            'model_identifier': stat['model_identifier'],
            'value': stat['annotated_poems'],
            'description': f"模型 {stat['model_identifier']} 标注的诗词数"
        })
        
        data.append({
            'statistic_type': 'model_sentences',
            'model_identifier': stat['model_identifier'],
            'value': stat['annotated_sentences'],
            'description': f"模型 {stat['model_identifier']} 标注的分句数"
        })
    
    # 添加不去重统计
    data.append({
        'statistic_type': 'unduplicated_total_poems',
        'model_identifier': 'ALL',
        'value': unduplicated_stats['total_annotated_poems_unduplicated'],
        'description': '不去重的已标注总诗词数'
    })
    
    data.append({
        'statistic_type': 'unduplicated_total_sentences',
        'model_identifier': 'ALL',
        'value': unduplicated_stats['total_annotated_sentences_unduplicated'],
        'description': '不去重的已标注总分句数'
    })
    
    return pd.DataFrame(data)

def main():
    parser = argparse.ArgumentParser(description="诗词情感标注统计脚本")
    parser.add_argument(
        "--db",
        type=str,
        required=True,
        help="指定数据库名称"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径 (CSV格式)，如果不指定则只在控制台输出"
    )
    
    args = parser.parse_args()
    
    try:
        # 获取数据库路径
        db_path = get_db_path(args.db)
        print(f"正在连接数据库: {db_path}")
        
        # 连接数据库
        conn = connect_database(db_path)
        
        # 获取统计数据
        print("正在获取去重标注统计信息...")
        unique_stats = get_unique_annotation_stats(conn)
        
        print("正在获取各模型标注统计信息...")
        model_stats = get_model_annotation_stats(conn)
        
        print("正在获取不去重标注统计信息...")
        unduplicated_stats = get_unduplicated_annotation_stats(conn)
        
        # 关闭数据库连接
        conn.close()
        
        # 格式化统计数据
        df = format_statistics(unique_stats, model_stats, unduplicated_stats)
        
        # 输出结果
        print("\n=== 标注统计结果 ===")
        print(df.to_string(index=False))
        
        # 如果指定了输出文件，则保存到CSV
        if args.output:
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"\n统计结果已保存到: {args.output}")
            
    except Exception as e:
        print(f"执行统计时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()