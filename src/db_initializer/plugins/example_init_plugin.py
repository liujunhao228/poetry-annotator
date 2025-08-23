"""
示例数据库初始化插件
"""

from typing import Dict, Any
from src.db_initializer.plugin_interface import DatabaseInitPlugin


class ExampleInitPlugin(DatabaseInitPlugin):
    """示例数据库初始化插件"""
    
    def get_name(self) -> str:
        return "example"
    
    def get_description(self) -> str:
        return "示例数据库初始化插件"
    
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库"""
        # 在这里可以执行插件特定的数据库初始化逻辑
        # 例如创建插件需要的表结构等
        
        # 示例：在标注数据库中创建一个示例表
        if self.separate_db_manager:
            try:
                # 创建示例表
                conn = self.separate_db_manager.annotation_db.connect()
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_example (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.close()
                
                return {
                    "status": "success",
                    "message": f"示例插件表在数据库 {db_name} 中创建成功"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"创建示例插件表时出错: {e}"
                }
        else:
            return {
                "status": "error",
                "message": "未提供分离数据库管理器"
            }
    
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法"""
        # 在这里可以执行初始化完成后的操作
        print(f"示例插件: 数据库 {db_name} 初始化完成，结果: {result}")