"""
为scripts/目录下的脚本提供简单、统一的数据访问API封装
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入数据管理器
try:
    from src.data import get_data_manager
except ImportError:
    print("错误: 无法导入数据管理器，请检查项目结构")
    sys.exit(1)


class SimpleDataAPI:
    """为脚本提供简单、统一的数据访问API"""
    
    def __init__(self):
        """初始化API实例"""
        self._data_managers = {}
    
    def get_data_manager(self, db_name: str = "default"):
        """
        获取数据管理器实例
        
        Args:
            db_name: 数据库名称
            
        Returns:
            DataManager实例
        """
        if db_name not in self._data_managers:
            self._data_managers[db_name] = get_data_manager(db_name)
        return self._data_managers[db_name]
    
    # --- 数据库操作方法 ---
    
    def load_data_from_json(self, json_file: str, db_name: str = "default") -> List[Dict[str, Any]]:
        """
        从JSON文件加载数据
        
        Args:
            json_file: JSON文件名
            db_name: 数据库名称
            
        Returns:
            加载的数据列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.load_data_from_json(json_file)
    
    def load_all_json_files(self, db_name: str = "default") -> List[Dict[str, Any]]:
        """
        加载所有JSON文件的数据
        
        Args:
            db_name: 数据库名称
            
        Returns:
            所有加载的数据列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.load_all_json_files()
    
    def load_author_data(self, db_name: str = "default") -> List[Dict[str, Any]]:
        """
        加载作者数据
        
        Args:
            db_name: 数据库名称
            
        Returns:
            加载的作者数据列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.load_author_data()
    
    def initialize_database_from_json(self, clear_existing: bool = False, db_name: str = "default") -> Dict[str, int]:
        """
        从JSON文件初始化数据库
        
        Args:
            clear_existing: 是否清空现有数据
            db_name: 数据库名称
            
        Returns:
            初始化统计信息
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.initialize_database_from_json(clear_existing)
    
    def get_poems_to_annotate(self, model_identifier: str, 
                              limit: Optional[int] = None, 
                              start_id: Optional[int] = None, 
                              end_id: Optional[int] = None,
                              force_rerun: bool = False,
                              db_name: str = "default") -> List[Any]:
        """
        获取指定模型待标注的诗词
        
        Args:
            model_identifier: 模型标识符
            limit: 限制数量
            start_id: 起始ID
            end_id: 结束ID
            force_rerun: 是否强制重跑
            db_name: 数据库名称
            
        Returns:
            待标注的诗词列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_poems_to_annotate(model_identifier, limit, start_id, end_id, force_rerun)
    
    def get_poem_by_id(self, poem_id: int, db_name: str = "default") -> Optional[Any]:
        """
        根据ID获取单首诗词信息
        
        Args:
            poem_id: 诗词ID
            db_name: 数据库名称
            
        Returns:
            诗词对象或None
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_poem_by_id(poem_id)
    
    def get_poems_by_ids(self, poem_ids: List[int], db_name: str = "default") -> List[Any]:
        """
        根据ID列表获取诗词信息
        
        Args:
            poem_ids: 诗词ID列表
            db_name: 数据库名称
            
        Returns:
            诗词对象列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_poems_by_ids(poem_ids)
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None, 
                        error_message: Optional[str] = None,
                        db_name: str = "default") -> bool:
        """
        保存标注结果
        
        Args:
            poem_id: 诗词ID
            model_identifier: 模型标识符
            status: 状态
            annotation_result: 标注结果
            error_message: 错误信息
            db_name: 数据库名称
            
        Returns:
            保存是否成功
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.save_annotation(poem_id, model_identifier, status, annotation_result, error_message)
    
    def get_statistics(self, db_name: str = "default") -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Args:
            db_name: 数据库名称
            
        Returns:
            统计信息字典
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_statistics()
    
    def export_results(self, output_format: str = 'jsonl', 
                       output_file: Optional[str] = None,
                       model_filter: Optional[str] = None,
                       db_name: str = "default") -> str:
        """
        导出标注结果
        
        Args:
            output_format: 输出格式
            output_file: 输出文件路径
            model_filter: 模型过滤器
            db_name: 数据库名称
            
        Returns:
            输出文件路径
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.export_results(output_format, output_file, model_filter)
    
    def get_annotation_statistics(self, db_name: str = "default") -> Dict[str, Any]:
        """
        获取标注统计信息
        
        Args:
            db_name: 数据库名称
            
        Returns:
            标注统计信息字典
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_annotation_statistics()
    
    def get_all_authors(self, db_name: str = "default") -> List[Any]:
        """
        获取所有作者信息
        
        Args:
            db_name: 数据库名称
            
        Returns:
            作者对象列表
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_all_authors()
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10, db_name: str = "default") -> Dict[str, Any]:
        """
        根据作者和标题搜索诗词，并支持分页
        
        Args:
            author: 作者
            title: 标题
            page: 页码
            per_page: 每页数量
            db_name: 数据库名称
            
        Returns:
            搜索结果字典
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.search_poems(author, title, page, per_page)
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str, db_name: str = "default") -> set[int]:
        """
        高效检查一组 poem_id 是否已被特定模型成功标注。
        
        Args:
            poem_ids: 需要检查的诗词ID列表。
            model_identifier: 要检查的模型的标识符。
            db_name: 数据库名称。
            
        Returns:
            一个包含在这批ID中且已成功标注的 poem_id 的集合。
        """
        data_manager = self.get_data_manager(db_name)
        return data_manager.get_completed_poem_ids(poem_ids, model_identifier)


# 全局API实例
simple_data_api = SimpleDataAPI()