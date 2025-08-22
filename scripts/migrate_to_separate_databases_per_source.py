#!/usr/bin/env python3
"""
数据迁移脚本
将现有数据库中的数据按来源迁移到新的分离数据库结构中
每个数据源（如唐诗、宋词）都有独立的原始数据、标注数据和情感分类数据库
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
# 获取项目根目录 (当前脚本的父目录的父目录)
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import sqlite3
from src.data.adapter import get_database_adapter


def migrate_data():
    """迁移数据到按来源分离的数据库结构"""
    print("开始按来源迁移数据...")
    
    # 定义数据源和对应的数据库路径
    data_sources = {
        'TangShi': {
            'source_db': 'data/TangShi.db',
            'target_databases': {
                'raw_data': 'data/TangShi/raw_data.db',
                'annotation': 'data/TangShi/annotation.db',
                'emotion': 'data/TangShi/emotion.db'
            }
        },
        'SongCi': {
            'source_db': 'data/SongCi.db',
            'target_databases': {
                'raw_data': 'data/SongCi/raw_data.db',
                'annotation': 'data/SongCi/annotation.db',
                'emotion': 'data/SongCi/emotion.db'
            }
        }
    }
    
    # 为每个数据源执行迁移
    for source_name, source_config in data_sources.items():
        print(f"\n开始迁移 {source_name} 数据...")
        migrate_source_data(source_name, source_config)
    
    print("\n所有数据迁移完成!")


def migrate_source_data(source_name, source_config):
    """迁移单个数据源的数据到独立的分离数据库"""
    source_db_path = source_config['source_db']
    target_databases = source_config['target_databases']
    
    print(f"  从数据库迁移数据:")
    print(f"    源数据库: {source_db_path}")
    print(f"    目标原始数据数据库: {target_databases['raw_data']}")
    print(f"    目标标注数据数据库: {target_databases['annotation']}")
    print(f"    目标情感分类数据库: {target_databases['emotion']}")
    
    # 确保目标数据库的目录存在
    for db_path in target_databases.values():
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 连接源数据库
    source_db = get_database_adapter('sqlite', source_db_path)
    
    # 初始化目标数据库
    raw_data_db = get_database_adapter('sqlite', target_databases['raw_data'])
    annotation_db = get_database_adapter('sqlite', target_databases['annotation'])
    emotion_db = get_database_adapter('sqlite', target_databases['emotion'])
    
    # 初始化各目标数据库的表结构
    raw_data_db.init_raw_data_database()
    annotation_db.init_annotation_database()
    emotion_db.init_emotion_database()
    
    # 迁移原始数据（诗词和作者）
    print("  开始迁移原始数据...")
    migrate_raw_data(source_db, raw_data_db)
    
    # 迁移标注数据
    print("  开始迁移标注数据...")
    migrate_annotation_data(source_db, annotation_db)
    
    # 迁移情感分类数据
    print("  开始迁移情感分类数据...")
    migrate_emotion_data(source_db, emotion_db)


def migrate_raw_data(source_db, target_db):
    """迁移原始数据（诗词和作者）"""
    # 迁移作者数据
    print("    迁移作者数据...")
    
    authors = source_db.execute_query("SELECT name, description, short_description, created_at FROM authors")
    if authors:
        # 清空目标表
        target_db.execute_update("DELETE FROM authors")
        
        # 批量插入作者数据
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO authors (name, description, short_description, created_at)
            VALUES (?, ?, ?, ?)
        ''', authors)
        target_conn.commit()
        
        print(f"      迁移了 {len(authors)} 位作者")
    
    # 迁移诗词数据
    print("    迁移诗词数据...")
    
    poems = source_db.execute_query("SELECT id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at FROM poems")
    if poems:
        # 清空目标表
        target_db.execute_update("DELETE FROM poems")
        
        # 批量插入诗词数据
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO poems (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', poems)
        target_conn.commit()
        
        print(f"      迁移了 {len(poems)} 首诗词")


def migrate_annotation_data(source_db, target_db):
    """迁移标注数据"""
    print("    迁移标注数据...")
    
    # 迁移标注结果
    annotations = source_db.execute_query("SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at FROM annotations")
    if annotations:
        # 清空目标表
        target_db.execute_update("DELETE FROM annotations")
        
        # 批量插入标注结果
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO annotations (id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', annotations)
        target_conn.commit()
        
        print(f"      迁移了 {len(annotations)} 条标注结果")
    
    # 迁移句子标注数据
    sentence_annotations = source_db.execute_query("SELECT id, annotation_id, poem_id, sentence_uid, sentence_text FROM sentence_annotations")
    if sentence_annotations:
        # 清空目标表
        target_db.execute_update("DELETE FROM sentence_annotations")
        
        # 批量插入句子标注数据
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO sentence_annotations (id, annotation_id, poem_id, sentence_uid, sentence_text)
            VALUES (?, ?, ?, ?, ?)
        ''', sentence_annotations)
        target_conn.commit()
        
        print(f"      迁移了 {len(sentence_annotations)} 条句子标注")
    
    # 迁移句子情感链接数据
    sentence_emotion_links = source_db.execute_query("SELECT sentence_annotation_id, emotion_id, is_primary FROM sentence_emotion_links")
    if sentence_emotion_links:
        # 清空目标表
        target_db.execute_update("DELETE FROM sentence_emotion_links")
        
        # 批量插入句子情感链接数据
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary)
            VALUES (?, ?, ?)
        ''', sentence_emotion_links)
        target_conn.commit()
        
        print(f"      迁移了 {len(sentence_emotion_links)} 条句子情感链接")


def migrate_emotion_data(source_db, target_db):
    """迁移情感分类数据"""
    print("    迁移情感分类数据...")
    
    # 迁移情感分类
    emotions = source_db.execute_query("SELECT id, name_zh, name_en, parent_id, level FROM emotion_categories")
    if emotions:
        # 清空目标表
        target_db.execute_update("DELETE FROM emotion_categories")
        
        # 批量插入情感分类数据
        target_conn = target_db.connect()
        target_cursor = target_conn.cursor()
        target_cursor.executemany('''
            INSERT OR REPLACE INTO emotion_categories (id, name_zh, name_en, parent_id, level)
            VALUES (?, ?, ?, ?, ?)
        ''', emotions)
        target_conn.commit()
        
        print(f"      迁移了 {len(emotions)} 个情感分类")


if __name__ == "__main__":
    migrate_data()