# 数据库结构说明

数据库使用 SQLite，主要包含以下几个表，用于存储诗词原文、情感标注结果、作者信息和情感分类体系。

## 1. `poems` 表 (诗词原文)

存储诗词的基本信息。为兼容唐诗（有标题）和宋词（有词牌名），统一使用 `title` 字段。

- `id` (INTEGER, PRIMARY KEY): 诗词唯一标识符。
- `title` (TEXT): 诗词标题（对于宋词，此字段存储其词牌名）。
- `author` (TEXT): 作者姓名。
- `paragraphs` (TEXT): 诗词正文（分行存储，JSON字符串）。
- `full_text` (TEXT): 诗词全文（纯文本，包含标题、作者和正文）。
- `author_desc` (TEXT): （可选）作者的简要描述。
- `created_at` (TEXT): 记录创建时间（ISO8601格式）。
- `updated_at` (TEXT): 记录最后更新时间（ISO 8601格式）。

## 2. `annotations` 表 (诗词整体标注记录)

存储每次对一首诗进行情感标注的结果。

- `id` (INTEGER, PRIMARY KEY): 标注记录唯一标识符。
- `poem_id` (INTEGER, FOREIGN KEY): 关联到 `poems` 表的 `id` 字段，表示被标注的诗词。
- `model_identifier` (TEXT, NOT NULL): 执行标注的模型或方法的唯一标识符（例如 `qwen_plus_20241225`）。
- `status` (TEXT, NOT NULL, CHECK IN `('completed', 'failed')`): 标注任务的状态。
- `annotation_result` (TEXT): 完整的标注结果 JSON 字符串（包含句子级标注详情）。
- `error_message` (TEXT): 如果 `status`为 `failed`，则存储错误信息。
- `created_at` (TEXT): 标注记录创建时间。
- `updated_at` (TEXT): 标注记录更新时间。

## 3. `authors` 表 (作者信息)

存储作者的详细信息。

- `name` (TEXT, PRIMARY KEY): 作者姓名。
- `description` (TEXT): 作者的详细介绍。
- `short_description` (TEXT): 作者的简短介绍。
- `created_at` (TEXT): 记录创建时间。

## 4. `emotion_categories` 表 (情感分类体系)

存储预定义的情感分类及其层级关系。

- `id` (TEXT, PRIMARY KEY): 情感类别唯一标识符（例如 `E1`）。
- `name_zh` (TEXT, NOT NULL): 情感类别的中文名称。
- `name_en` (TEXT): 情感类别的英文名称（可选）。
- `parent_id` (TEXT, FOREIGN KEY): 指向父类别的 `id`，用于构建树状结构。根节点的 `parent_id` 为 `NULL`。
- `level` (INTEGER, NOT NULL): 类别的层级（例如，1 为顶层类别，2 为二级子类）。

## 5. `sentence_annotations` 表 (句子级标注记录)

存储诗词中每个句子的标注信息。

- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): 句子标注记录的唯一标识符。
- `annotation_id` (INTEGER, FOREIGN KEY): 关联到 `annotations` 表的 `id` 字段，表示这次句子标注属于哪一次整体标注。
- `poem_id` (INTEGER, FOREIGN KEY): 关联到 `poems` 表的 `id` 字段，表示该句子属于哪首诗。
- `sentence_uid` (TEXT, NOT NULL): 句子的唯一标识符（通常由诗ID和句子序号组合而成，如 `poem_123_sent_1`）。
- `sentence_text` (TEXT): 句子的原始文本内容。

## 6. `sentence_emotion_links` 表 (句子-情感关联)

存储句子与其关联的情感标签之间的多对多关系，并区分主次情感。

- `sentence_annotation_id` (INTEGER, FOREIGN KEY, PART OF PRIMARY KEY): 关联到 `sentence_annotations` 表的 `id` 字段，表示哪个句子。
- `emotion_id` (TEXT, FOREIGN KEY, PART OF PRIMARY KEY): 关联到 `emotion_categories` 表的 `id` 字段，表示关联了哪种情感。
- `is_primary` (BOOLEAN, NOT NULL): 标记该情感是否为该句子的主要情感（`1` 为是，`0` 为否）。

## 数据库索引 (Indexes)

为了提高查询效率，数据库还创建了以下索引：

- `idx_poem_author` on `poems(author)`: 加速按作者查询诗词。
- `idx_annotation_poem_model` on `annotations(poem_id, model_identifier)`: 加速按诗ID和模型查询标注。
- `uidx_poem_model` on `annotations(poem_id, model_identifier)`: 确保每首诗对每个模型只有一个标注记录。
- `idx_annotation_status` on `annotations(status)`: 加速按标注状态查询。
- `idx_annotation_created_at` on `annotations(created_at)`: 加速按标注创建时间查询。
- `idx_poem_created_at` on `poems(created_at)`: 加速按诗词创建时间查询。
- `idx_emotion_parent_id` on `emotion_categories(parent_id)`: 加速查询情感类别的子类。
- `uidx_sentence_ref` on `sentence_annotations(annotation_id, sentence_uid)`: 确保每次标注中句子UID的唯一性。
- `idx_link_emotion_id` on `sentence_emotion_links(emotion_id)`: 加速按情感ID查询句子。