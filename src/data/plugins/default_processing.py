"""
默认数据处理插件实现
"""
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.data.plugin_interfaces.core import DataProcessingPlugin


class DefaultProcessingPlugin(DataProcessingPlugin):
    """默认数据处理插件实现"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_name(self) -> str:
        return "default_processing"
    
    def get_description(self) -> str:
        return "默认数据处理插件实现"
    
    def load_data_from_json(self, source_dir: str, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        file_path = Path(source_dir) / json_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {file_path}")
        
        self.logger.debug(f"加载JSON文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.logger.debug(f"JSON文件 {json_file} 加载完成，包含 {len(data)} 条记录")
        return data
    
    def load_all_json_files(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据"""
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"数据源目录不存在: {source_path}")
        
        all_data = []
        
        # 查找所有 poet.*.*.json 和 ci.*.*.json 文件
        poet_files = list(source_path.glob('poet.*.*.json'))
        ci_files = list(source_path.glob('ci.*.*.json'))
        json_files = poet_files + ci_files
        json_files.sort()  # 确保按文件名排序
        
        self.logger.info(f"找到 {len(json_files)} 个JSON文件 ({len(poet_files)} 个poet文件, {len(ci_files)} 个ci文件)")
        
        for json_file in json_files:
            try:
                self.logger.debug(f"处理文件: {json_file.name}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
                self.logger.debug(f"文件 {json_file.name} 处理完成，包含 {len(data)} 条记录")
            except Exception as e:
                self.logger.error(f"处理文件 {json_file.name} 时出错: {e}")
        
        self.logger.info(f"所有JSON文件加载完成，总计 {len(all_data)} 条记录")
        return all_data
    
    def load_author_data(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载作者数据"""
        source_path = Path(source_dir)
        if not source_path.exists():
            self.logger.warning(f"数据源目录不存在: {source_path}")
            return []

        all_authors = []
        # 查找所有 authors.*.json 和 author.*.json 文件
        authors_files = list(source_path.glob('authors.*.json'))
        author_files = list(source_path.glob('author.*.json'))
        author_files = sorted(authors_files + author_files)

        if not author_files:
            self.logger.warning("在数据源目录中未找到作者文件。")
            return []

        self.logger.info(f"找到 {len(author_files)} 个作者文件: {[f.name for f in author_files]}")

        for author_file in author_files:
            try:
                with open(author_file, 'r', encoding='utf-8') as f:
                    authors = json.load(f)
                all_authors.extend(authors)
                self.logger.info(f"从 {author_file.name} 加载了 {len(authors)} 位作者信息。")
            except Exception as e:
                self.logger.error(f"加载作者文件 {author_file.name} 时出错: {e}")
        
        self.logger.info(f"所有作者文件加载完成，总计加载了 {len(all_authors)} 位作者信息。")
        return all_authors