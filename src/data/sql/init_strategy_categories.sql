-- 初始化策略分类数据
-- 关系动作 (Relationship Action)
INSERT INTO strategy_categories (id, name_zh, name_en, category_type, parent_id, level) VALUES
('RA01', '情感充值', 'Emotional Recharge', 'relationship_action', NULL, 1),
('RA02', '资源请求', 'Resource Request', 'relationship_action', NULL, 1),
('RA03', '身份认证', 'Identity Verification', 'relationship_action', NULL, 1),
('RA04', '危机公关', 'Crisis Management', 'relationship_action', NULL, 1),
('RA05', '价值展示', 'Value Display', 'relationship_action', NULL, 1),
('RA06', '权力应答', 'Power Response', 'relationship_action', NULL, 1),
('RA07', '加密传讯', 'Encrypted Communication', 'relationship_action', NULL, 1),
('RA08', '情绪爆破', 'Emotional Explosion', 'relationship_action', NULL, 1),

-- 情感策略 (Emotional Strategy)
('ES01', '暴雨式', 'Torrential', 'emotional_strategy', NULL, 1),
('ES02', '针灸式', 'Acupuncture', 'emotional_strategy', NULL, 1),
('ES03', '迷雾式', 'Foggy', 'emotional_strategy', NULL, 1),
('ES04', '糖衣式', 'Sugar-coated', 'emotional_strategy', NULL, 1),

-- 传播场景 (Communication Scene)
('SC01', '密室私语', 'Private Whisper', 'communication_scene', NULL, 1),
('SC02', '沙龙展演', 'Salon Performance', 'communication_scene', NULL, 1),
('SC03', '广场广播', 'Public Broadcast', 'communication_scene', NULL, 1),
('SC04', '权力剧场', 'Power Theater', 'communication_scene', NULL, 1),

-- 风险等级 (Risk Score)
('RS01', '安全牌', 'Safe Card', 'risk_level', NULL, 1),
('RS02', '杠杆牌', 'Leverage Card', 'risk_level', NULL, 1),
('RS03', '炸弹牌', 'Bomb Card', 'risk_level', NULL, 1);