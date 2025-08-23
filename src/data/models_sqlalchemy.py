"""
SQLAlchemy数据库模型定义
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


Base = declarative_base()


class Poem(Base):
    """诗词数据模型"""
    __tablename__ = 'poems'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    paragraphs = Column(Text)
    full_text = Column(Text)
    author_desc = Column(Text)
    data_status = Column(String, default='active')
    pre_classification = Column(String)
    created_at = Column(String)
    updated_at = Column(String)


class Author(Base):
    """作者数据模型"""
    __tablename__ = 'authors'
    
    name = Column(String, primary_key=True)
    description = Column(Text)
    short_description = Column(Text)
    created_at = Column(String)


class Annotation(Base):
    """标注数据模型"""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    poem_id = Column(Integer)
    model_identifier = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'completed' or 'failed'
    annotation_result = Column(Text)
    error_message = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)


class SentenceAnnotation(Base):
    """句子标注模型"""
    __tablename__ = 'sentence_annotations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    annotation_id = Column(Integer, nullable=False)
    poem_id = Column(Integer, nullable=False)
    sentence_uid = Column(String, nullable=False)
    sentence_text = Column(Text)


class SentenceEmotionLink(Base):
    """句子情感链接模型"""
    __tablename__ = 'sentence_emotion_links'
    
    sentence_annotation_id = Column(Integer, primary_key=True)
    emotion_id = Column(String, primary_key=True)
    is_primary = Column(Boolean, nullable=False)


class SentenceStrategyLink(Base):
    """句子策略链接模型"""
    __tablename__ = 'sentence_strategy_links'
    
    sentence_annotation_id = Column(Integer, primary_key=True)
    strategy_id = Column(String, primary_key=True)
    strategy_type = Column(String, primary_key=True)  # relationship_action, emotional_strategy, communication_scene, risk_level
    is_primary = Column(Boolean, nullable=False)


class EmotionCategory(Base):
    """情感分类模型"""
    __tablename__ = 'emotion_categories'
    
    id = Column(String, primary_key=True)
    name_zh = Column(String, nullable=False)
    name_en = Column(String)
    parent_id = Column(String)
    level = Column(Integer, nullable=False)


class StrategyCategory(Base):
    """策略分类模型"""
    __tablename__ = 'strategy_categories'
    
    id = Column(String, primary_key=True)
    name_zh = Column(String, nullable=False)
    name_en = Column(String)
    category_type = Column(String, nullable=False)  # relationship_action, emotional_strategy, communication_scene, risk_level
    parent_id = Column(String)
    level = Column(Integer, nullable=False)


# 数据库会话工厂
engine = None
SessionLocal = None


def init_db(db_path: str):
    """初始化数据库"""
    global engine, SessionLocal
    engine = create_engine(f'sqlite:///{db_path}')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()