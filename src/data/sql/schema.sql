-- 创建原始数据表
CREATE TABLE poems (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    paragraphs TEXT,
    full_text TEXT,
    author_desc TEXT,
    data_status TEXT DEFAULT 'active',
    pre_classification TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE authors (
    name TEXT PRIMARY KEY,
    description TEXT,
    short_description TEXT,
    created_at TEXT
);

-- 创建索引
CREATE INDEX idx_poem_author ON poems(author);
CREATE INDEX idx_poem_created_at ON poems(created_at);

-- 创建标注数据表
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY,
    poem_id INTEGER,
    model_identifier TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('completed', 'failed')),
    annotation_result TEXT,
    error_message TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE sentence_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annotation_id INTEGER NOT NULL,
    poem_id INTEGER NOT NULL,
    sentence_uid TEXT NOT NULL,
    sentence_text TEXT
);

CREATE TABLE sentence_emotion_links (
    sentence_annotation_id INTEGER NOT NULL,
    emotion_id TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL,
    PRIMARY KEY (sentence_annotation_id, emotion_id)
);

CREATE TABLE sentence_strategy_links (
    sentence_annotation_id INTEGER NOT NULL,
    strategy_id TEXT NOT NULL,
    strategy_type TEXT NOT NULL, -- relationship_action, emotional_strategy, communication_scene, risk_level
    is_primary BOOLEAN NOT NULL,
    PRIMARY KEY (sentence_annotation_id, strategy_id, strategy_type)
);

-- 创建索引
CREATE INDEX idx_annotation_poem_model ON annotations(poem_id, model_identifier);
CREATE UNIQUE INDEX uidx_poem_model ON annotations(poem_id, model_identifier);
CREATE INDEX idx_annotation_status ON annotations(status);
CREATE INDEX idx_annotation_created_at ON annotations(created_at);
CREATE UNIQUE INDEX uidx_sentence_ref ON sentence_annotations(annotation_id, sentence_uid);
CREATE INDEX idx_link_emotion_id ON sentence_emotion_links(emotion_id);
CREATE INDEX idx_link_strategy_id ON sentence_strategy_links(strategy_id);
CREATE INDEX idx_link_strategy_type ON sentence_strategy_links(strategy_type);

-- 创建策略分类表
CREATE TABLE strategy_categories (
    id TEXT PRIMARY KEY,
    name_zh TEXT NOT NULL,
    name_en TEXT,
    category_type TEXT NOT NULL, -- relationship_action, emotional_strategy, communication_scene, risk_level
    parent_id TEXT,
    level INTEGER NOT NULL
);

-- 创建索引
CREATE INDEX idx_strategy_parent_id ON strategy_categories(parent_id);
CREATE INDEX idx_strategy_category_type ON strategy_categories(category_type);