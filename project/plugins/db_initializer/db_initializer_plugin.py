"""数据库初始化插件"""

import logging
from typing import Dict, Any, Optional
from src.db_initializer.plugin_interface import DatabaseInitPlugin
from src.data.adapter import DatabaseAdapter
from src.data.separate_databases import SeparateDatabaseManager
from src.config.schema import PluginConfig

logger = logging.getLogger(__name__)

class SocialPoemAnalysisDBInitializer(DatabaseInitPlugin):
    """《交际诗分析》项目数据库初始化插件"""
    
    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[SeparateDatabaseManager] = None):
        super().__init__(config, separate_db_manager)
        self.name = "social_poem_analysis_db_init"
        self.description = "《交际诗分析》项目数据库初始化插件"
        
    def get_name(self) -> str:
        return self.name
        
    def get_description(self) -> str:
        return self.description
        
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库表结构"""
        try:
            # 获取数据库适配器
            db_adapter = self.separate_db_manager.get_db_adapter(db_name)
            
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
            
            logger.info(f"成功初始化《交际诗分析》项目数据库表结构，源数据路径: {self.source_dir}，数据库路径: {self.db_paths}")
            return {
                "status": "success",
                "message": "数据库初始化成功",
                "source_dir": self.source_dir,
                "db_paths": self.db_paths
            }
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }