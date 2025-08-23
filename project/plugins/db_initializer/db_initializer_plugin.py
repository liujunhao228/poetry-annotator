"""数据库初始化插件"""

import logging
from typing import Dict, Any, Optional
from src.data.db_initializer_interface import DatabaseInitializerPlugin
from src.data.db_adapter import DatabaseAdapter

logger = logging.getLogger(__name__)

class SocialPoemAnalysisDBInitializer(DatabaseInitializerPlugin):
    """《交际诗分析》项目数据库初始化插件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = "social_poem_analysis_db_init"
        self.description = "《交际诗分析》项目数据库初始化插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def initialize(self, db_adapter: DatabaseAdapter) -> bool:
        """初始化数据库表结构"""
        try:
            # 创建项目特定的表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS social_analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poem_id INTEGER NOT NULL,
                sentence_id TEXT NOT NULL,
                relationship_action TEXT,
                emotional_strategy TEXT,
                communication_scene TEXT,
                risk_level TEXT,
                rationale TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (poem_id) REFERENCES poems (id)
            );
            """
            db_adapter.execute_script(create_table_sql)
            
            logger.info("成功初始化《交际诗分析》项目数据库表结构")
            return True
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return False