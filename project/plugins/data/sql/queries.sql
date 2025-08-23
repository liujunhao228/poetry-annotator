-- 查询所有诗词
SELECT id, title, author, paragraphs, full_text, created_at 
FROM poems;

-- 查询所有标注
SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at 
FROM annotations;

-- 查询标注数据并联接诗词信息
SELECT
    a.id AS annotation_id, a.model_identifier, a.status, a.created_at AS annotation_created_at,
    p.id AS poem_id, p.title AS title, p.author, p.created_at AS poem_created_at
FROM annotations a
JOIN poems p ON a.poem_id = p.id;

-- 获取每个作者的诗词数量
SELECT author, COUNT(id) AS poem_count 
FROM poems 
GROUP BY author 
ORDER BY poem_count DESC;

-- 获取每个模型的标注状态统计
SELECT model_identifier, status, COUNT(id) AS count 
FROM annotations 
GROUP BY model_identifier, status 
ORDER BY model_identifier, status;

