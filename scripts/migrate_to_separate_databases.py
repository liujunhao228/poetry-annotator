#!/usr/bin/env python3
"""
数据迁移脚本
将现有数据库中的数据迁移到新的分离数据库结构中
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
from src.data.separate_databases import get_separate_db_manager
from src.data.adapter import get_database_adapter


def migrate_data():
    """迁移数据到新的分离数据库结构"""
    print("开始数据迁移...")
    
    # 初始化分离数据库管理器
    separate_db_manager = get_separate_db_manager()
    
    # 初始化各数据库
    separate_db_manager.initialize_all_databases()
    
    # 获取现有的数据库路径
    db_configs = separate_db_manager.db_configs
    tangshi_db_path = db_configs.get('TangShi', 'data/TangShi.db')
    songci_db_path = db_configs.get('SongCi', 'data/SongCi.db')
    
    print(f"从数据库迁移数据:")
    print(f"  唐诗数据库: {tangshi_db_path}")
    print(f"  宋词数据库: {songci_db_path}")
    print(f"  原始数据数据库: {separate_db_manager.db_configs['raw_data']}")
    print(f"  标注数据数据库: {separate_db_manager.db_configs['annotation']}")
    print(f"  情感分类数据库: {separate_db_manager.db_configs['emotion']}")
    
    # 连接数据库
    tangshi_db = get_database_adapter('sqlite', tangshi_db_path)
    songci_db = get_database_adapter('sqlite', songci_db_path)
    
    # 迁移原始数据（诗词和作者）
    print("\\n开始迁移原始数据...")
    migrate_raw_data(tangshi_db, songci_db, separate_db_manager.raw_data_db)
    
    # 迁移标注数据
    print("\\n开始迁移标注数据...")
    migrate_annotation_data(tangshi_db, songci_db, separate_db_manager.annotation_db)
    
    # 迁移情感分类数据
    print("\\n开始迁移情感分类数据...")
    migrate_emotion_data(tangshi_db, separate_db_manager.emotion_db)
    
    print("\\n数据迁移完成!")


def migrate_raw_data(source_db1, source_db2, target_db):
    """迁移原始数据（诗词和作者）"""
    # 迁移作者数据
    print("迁移作者数据...")
    
    # 从第一个数据库迁移作者
    authors1 = source_db1.execute_query("SELECT name, description, short_description, created_at FROM authors")
    if authors1:
        target_db.execute_update("DELETE FROM authors")  # 清空目标表
        for author in authors1:
            target_db.execute_update('''
                INSERT OR REPLACE INTO authors (name, description, short_description, created_at)
                VALUES (?, ?, ?, ?)
            ''', author)
        print(f"    从第一个数据库迁移了 {len(authors1)} 位作者")
    
    # 从第二个数据库迁移作者（避免重复）
    authors2 = source_db2.execute_query("SELECT name, description, short_description, created_at FROM authors")
    if authors2:
        existing_authors = set(row[0] for row in target_db.execute_query("SELECT name FROM authors"))
        new_authors = [author for author in authors2 if author[0] not in existing_authors]
        for author in new_authors:
            target_db.execute_update('''
                INSERT OR REPLACE INTO authors (name, description, short_description, created_at)
                VALUES (?, ?, ?, ?)
            ''', author)
        print(f"    从第二个数据库迁移了 {len(new_authors)} 位新作者")
    
    # 迁移诗词数据
    print("  迁移诗词数据...")
    
    # 从第一个数据库迁移诗词
    poems1 = source_db1.execute_query("SELECT id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at FROM poems")
    if poems1:
        target_db.execute_update("DELETE FROM poems")  # 清空目标表
        for poem in poems1:
            target_db.execute_update('''
                INSERT OR REPLACE INTO poems (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', poem)
        print(f"    从第一个数据库迁移了 {len(poems1)} 首诗词")
    
    # 从第二个数据库迁移诗词（避免ID冲突）
    poems2 = source_db2.execute_query("SELECT id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at FROM poems")
    if poems2:
        # 获取目标数据库中最大的ID，确保新ID不冲突
        max_id_result = target_db.execute_query("SELECT MAX(id) FROM poems")
        max_id = max_id_result[0][0] if max_id_result and max_id_result[0][0] else 0
        
        for poem in poems2:
            # 更新ID以避免冲突
            new_id = poem[0] + max_id
            new_poem = (new_id, *poem[1:])
            target_db.execute_update('''
                INSERT OR REPLACE INTO poems (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', new_poem)
        print(f"    从第二个数据库迁移了 {len(poems2)} 首诗词")


def migrate_annotation_data(source_db1, source_db2, target_db):
    """迁移标注数据"""
    print("  迁移标注数据...")
    
    # 迁移标注结果
    annotations1 = source_db1.execute_query("SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at FROM annotations")
    if annotations1:
        target_db.execute_update("DELETE FROM annotations")  # 清空目标表
        for annotation in annotations1:
            target_db.execute_update('''
                INSERT OR REPLACE INTO annotations (id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', annotation)
        print(f"    从第一个数据库迁移了 {len(annotations1)} 条标注结果")
    
    # 从第二个数据库迁移标注结果
    annotations2 = source_db2.execute_query("SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at FROM annotations")
    if annotations2:
        # 获取目标数据库中最大的ID，确保新ID不冲突
        max_id_result = target_db.execute_query("SELECT MAX(id) FROM annotations")
        max_id = max_id_result[0][0] if max_id_result and max_id_result[0][0] else 0
        
        # 获取目标数据库中最大的poem_id，确保引用的诗词ID不冲突
        max_poem_id_result = target_db.execute_query("SELECT MAX(poem_id) FROM annotations")
        max_poem_id = max_poem_id_result[0][0] if max_poem_id_result and max_poem_id_result[0][0] else 0
        
        for annotation in annotations2:
            # 更新ID以避免冲突
            new_id = annotation[0] + max_id
            # 更新poem_id以匹配新的诗词ID
            new_poem_id = annotation[1] + max_poem_id
            new_annotation = (new_id, new_poem_id, *annotation[2:])
            target_db.execute_update('''
                INSERT OR REPLACE INTO annotations (id, poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', new_annotation)
        print(f"    从第二个数据库迁移了 {len(annotations2)} 条标注结果")
    
    # 迁移句子标注数据
    sentence_annotations1 = source_db1.execute_query("SELECT id, annotation_id, poem_id, sentence_uid, sentence_text FROM sentence_annotations")
    if sentence_annotations1:
        target_db.execute_update("DELETE FROM sentence_annotations")  # 清空目标表
        for sentence_annotation in sentence_annotations1:
            target_db.execute_update('''
                INSERT OR REPLACE INTO sentence_annotations (id, annotation_id, poem_id, sentence_uid, sentence_text)
                VALUES (?, ?, ?, ?, ?)
            ''', sentence_annotation)
        print(f"    从第一个数据库迁移了 {len(sentence_annotations1)} 条句子标注")
    
    # 从第二个数据库迁移句子标注数据
    sentence_annotations2 = source_db2.execute_query("SELECT id, annotation_id, poem_id, sentence_uid, sentence_text FROM sentence_annotations")
    if sentence_annotations2:
        # 获取目标数据库中最大的ID，确保新ID不冲突
        max_id_result = target_db.execute_query("SELECT MAX(id) FROM sentence_annotations")
        max_id = max_id_result[0][0] if max_id_result and max_id_result[0][0] else 0
        
        # 获取目标数据库中最大的annotation_id，确保引用的标注ID不冲突
        max_annotation_id_result = target_db.execute_query("SELECT MAX(annotation_id) FROM sentence_annotations")
        max_annotation_id = max_annotation_id_result[0][0] if max_annotation_id_result and max_annotation_id_result[0][0] else 0
        
        # 获取目标数据库中最大的poem_id，确保引用的诗词ID不冲突
        max_poem_id_result = target_db.execute_query("SELECT MAX(poem_id) FROM sentence_annotations")
        max_poem_id = max_poem_id_result[0][0] if max_poem_id_result and max_poem_id_result[0][0] else 0
        
        for sentence_annotation in sentence_annotations2:
            # 更新ID以避免冲突
            new_id = sentence_annotation[0] + max_id
            # 更新annotation_id以匹配新的标注ID
            new_annotation_id = sentence_annotation[1] + max_annotation_id
            # 更新poem_id以匹配新的诗词ID
            new_poem_id = sentence_annotation[2] + max_poem_id
            new_sentence_annotation = (new_id, new_annotation_id, new_poem_id, sentence_annotation[3], sentence_annotation[4])
            target_db.execute_update('''
                INSERT OR REPLACE INTO sentence_annotations (id, annotation_id, poem_id, sentence_uid, sentence_text)
                VALUES (?, ?, ?, ?, ?)
            ''', new_sentence_annotation)
        print(f"    从第二个数据库迁移了 {len(sentence_annotations2)} 条句子标注")
    
    # 迁移句子情感链接数据
    sentence_emotion_links1 = source_db1.execute_query("SELECT sentence_annotation_id, emotion_id, is_primary FROM sentence_emotion_links")
    if sentence_emotion_links1:
        target_db.execute_update("DELETE FROM sentence_emotion_links")  # 清空目标表
        for sentence_emotion_link in sentence_emotion_links1:
            target_db.execute_update('''
                INSERT OR REPLACE INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary)
                VALUES (?, ?, ?)
            ''', sentence_emotion_link)
        print(f"    从第一个数据库迁移了 {len(sentence_emotion_links1)} 条句子情感链接")
    
    # 从第二个数据库迁移句子情感链接数据
    sentence_emotion_links2 = source_db2.execute_query("SELECT sentence_annotation_id, emotion_id, is_primary FROM sentence_emotion_links")
    if sentence_emotion_links2:
        # 获取目标数据库中最大的sentence_annotation_id，确保引用的句子标注ID不冲突
        max_sentence_annotation_id_result = target_db.execute_query("SELECT MAX(sentence_annotation_id) FROM sentence_emotion_links")
        max_sentence_annotation_id = max_sentence_annotation_id_result[0][0] if max_sentence_annotation_id_result and max_sentence_annotation_id_result[0][0] else 0
        
        for sentence_emotion_link in sentence_emotion_links2:
            # 更新sentence_annotation_id以匹配新的句子标注ID
            new_sentence_annotation_id = sentence_emotion_link[0] + max_sentence_annotation_id
            new_sentence_emotion_link = (new_sentence_annotation_id, sentence_emotion_link[1], sentence_emotion_link[2])
            target_db.execute_update('''
                INSERT OR REPLACE INTO sentence_emotion_links (sentence_annotation_id, emotion_id, is_primary)
                VALUES (?, ?, ?)
            ''', new_sentence_emotion_link)
        print(f"    从第二个数据库迁移了 {len(sentence_emotion_links2)} 条句子情感链接")


def migrate_emotion_data(source_db, target_db):
    """迁移情感分类数据"""
    print("  迁移情感分类数据...")
    
    # 迁移情感分类
    emotions = source_db.execute_query("SELECT id, name_zh, name_en, parent_id, level FROM emotion_categories")
    if emotions:
        target_db.execute_update("DELETE FROM emotion_categories")  # 清空目标表
        for emotion in emotions:
            target_db.execute_update('''
                INSERT OR REPLACE INTO emotion_categories (id, name_zh, name_en, parent_id, level)
                VALUES (?, ?, ?, ?, ?)
            ''', emotion)
        print(f"    迁移了 {len(emotions)} 个情感分类")


if __name__ == "__main__":
    migrate_data()