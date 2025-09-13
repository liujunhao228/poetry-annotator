"""
完全重构的数据管理器
仅作为插件的调度器和接口层，不包含任何核心业务逻辑
"""
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from src.config import get_config_manager
from .models import Poem, Author, Annotation
from .exceptions import DataError, DatabaseError
from src.component_system import get_component_system, ComponentType
from src.data.poem_processing import PoemClassificationCore


class DataManager:
    """完全重构的数据管理器，核心逻辑全部由插件承担"""
    
    def __init__(self, db_name: str = "default"):
        """初始化数据管理器"""
        # 获取配置管理器实例
        config_manager = get_config_manager()
        
        # 获取数据库配置
        db_config = config_manager.get_effective_database_config()
        
        # 处理分离数据库配置
        separate_db_paths = db_config.get('separate_db_paths', {})
        self.db_name = db_name
        
        # 从配置中获取数据库路径，优先使用分离数据库配置
        if separate_db_paths:
            if db_name in separate_db_paths:
                # 如果指定了特定的数据库名称，使用对应的配置
                self.db_path = separate_db_paths[db_name]
            elif 'raw_data' in separate_db_paths:
                # 默认使用原始数据数据库路径
                self.db_path = separate_db_paths['raw_data']
            else:
                # 如果没有找到合适的配置，使用默认路径
                self.db_path = f"data/{db_name}/raw_data.db"
        else:
            # 如果没有分离数据库配置，使用默认路径
            self.db_path = f"data/{db_name}/raw_data.db"
            
        # 获取数据源目录配置
        data_config = config_manager.get_effective_data_config()
        self.source_dir = data_config['source_dir']
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"数据管理器初始化 - 数据库: {self.db_path}, 数据源: {self.source_dir}")
        
        # 初始化组件系统
        project_root = Path(__file__).parent.parent.parent
        self.component_system = get_component_system(project_root)
        
        # 初始化分离数据库管理器 (提前初始化，以便插件可以使用)
        from .separate_databases import get_separate_db_manager
        self.separate_db_manager = get_separate_db_manager()
        
        # 为了保持向后兼容性，添加适配器属性
        self.db_adapter = self.separate_db_manager.raw_data_db
        
        # 为不同数据库设置ID前缀，确保全局唯一性
        self._set_id_prefix()

        # 直接导入并创建统一插件实例，避免循环依赖
        try:
            from project.plugins.social_poem_analysis_plugin import SocialPoemAnalysisPlugin
            from src.config.schema import PluginConfig
            plugin_config = PluginConfig(
                enabled=True,
                module="project.plugins.social_poem_analysis_plugin",
                class_name="SocialPoemAnalysisPlugin",
                settings={"type": "social_poem_analysis"}
            )
            # 传递 separate_db_manager 给插件
            self.social_poem_plugin = SocialPoemAnalysisPlugin(plugin_config, separate_db_manager=self.separate_db_manager)
            self.logger.info("DataManager: 成功创建统一插件实例")
        except Exception as e:
            self.logger.critical(f"DataManager: 创建统一插件实例失败: {e}", exc_info=True)
            # Do not re-raise here, allow DataManager to function without the plugin
            # This will cause subsequent calls to self.social_poem_plugin to fail if not handled
            self.social_poem_plugin = None # Explicitly set to None if creation fails
        
        # 检查数据库文件是否存在，如果不存在则初始化
        if not Path(self.db_path).exists():
            self.logger.info(f"数据库文件 {self.db_path} 不存在，正在初始化...")
            self._initialize_database_if_not_exists()
        
        # 初始化诗词分类核心处理器
        self.poem_classification_core = PoemClassificationCore(project_root=str(project_root))
    
    def _set_id_prefix(self):
        """为不同数据库设置ID前缀，确保全局唯一性"""
        # 定义数据库名称到前缀的映射
        db_prefixes = {
            "TangShi": 1000000,  # 唐诗ID前缀
            "SongCi": 2000000,   # 宋词ID前缀
            "YuanQu": 3000000,   # 元曲ID前缀
            "default": 0         # 默认数据库前缀
        }
        
        # 根据数据库名称设置前缀
        self.id_prefix = db_prefixes.get(self.db_name, 0)
        self.logger.info(f"数据库 {self.db_name} 的ID前缀设置为: {self.id_prefix}")
    
    def _initialize_database_if_not_exists(self):
        """如果数据库文件不存在则初始化"""
        try:
            # 确保数据库目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建一个空的数据库文件
            with open(self.db_path, 'w') as f:
                pass
                
            self.logger.info(f"已创建空数据库文件: {self.db_path}")
        except Exception as e:
            self.logger.error(f"创建数据库文件失败: {e}")
            raise DatabaseError(f"无法创建数据库文件 {self.db_path}: {e}")
    
    # 所有业务逻辑都直接委托给统一插件
    
    def get_poems_to_annotate(self, model_identifier: str, 
                             limit: Optional[int] = None, 
                             start_id: Optional[int] = None, 
                             end_id: Optional[int] = None,
                             force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词"""
        return self.social_poem_plugin.get_poems_to_annotate(
            model_identifier, limit, start_id, end_id, force_rerun
        )
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息"""
        return self.social_poem_plugin.get_poem_by_id(poem_id)
    
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息"""
        return self.social_poem_plugin.get_poems_by_ids(poem_ids)
    
    def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                        annotation_result: Optional[str] = None, 
                        error_message: Optional[str] = None) -> bool:
        """保存标注结果"""
        return self.social_poem_plugin.save_annotation(
            poem_id, model_identifier, status, annotation_result, error_message
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.social_poem_plugin.get_statistics()
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        return self.social_poem_plugin.get_annotation_statistics()
    
    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        return self.social_poem_plugin.get_all_authors()
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页"""
        return self.social_poem_plugin.search_poems(author, title, page, per_page)
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        """高效检查一组 poem_id 是否已被特定模型成功标注"""
        return self.social_poem_plugin.get_completed_poem_ids(poem_ids, model_identifier)
    
    # 数据加载和存储方法也直接委托给统一插件
    def load_data_from_json(self, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        return self.social_poem_plugin.load_data_from_json(self.source_dir, json_file)
    
    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据"""
        return self.social_poem_plugin.load_all_json_files(self.source_dir)
    
    def load_author_data(self, source_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载作者数据"""
        # 如果没有提供source_dir，则使用实例的source_dir属性
        if source_dir is None:
            source_dir = self.source_dir
        return self.social_poem_plugin.load_author_data(source_dir)

    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息"""
        if not self.social_poem_plugin:
            raise DataError("SocialPoemAnalysisPlugin 未成功加载，无法执行批量插入作者操作。")
        return self.social_poem_plugin.batch_insert_authors(authors_data)

    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None) -> int:
        """批量插入诗词到数据库"""
        if not self.social_poem_plugin:
            raise DataError("SocialPoemAnalysisPlugin 未成功加载，无法执行批量插入诗词操作。")
        return self.social_poem_plugin.batch_insert_poems(poems_data, start_id=start_id, id_prefix=self.id_prefix)

    def classify_data(self, db_name: str = "default", dry_run: bool = False):
        """
        对诗词数据进行分类
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            分类统计信息
        """
        return self.poem_classification_core.classify_poems_data(self, db_name, dry_run)

    def reset_data_classification(self, db_name: str = "default", dry_run: bool = False):
        """
        重置数据分类
        
        Args:
            db_name: 数据库名称
            dry_run: 是否为试运行模式
            
        Returns:
            重置统计信息
        """
        return self.poem_classification_core.reset_pre_classification(self, db_name, dry_run)

    def generate_classification_report(self, db_name: str = "default"):
        """
        生成分类报告
        
        Args:
            db_name: 数据库名称
            
        Returns:
            分类报告
        """
        return self.poem_classification_core.get_classification_report(self, db_name)

# 全局数据管理器实例
data_manager = None


def get_data_manager(db_name: str = "default"):
    """获取数据管理器实例，支持在运行时切换数据库"""
    global data_manager
    if data_manager is None or data_manager.db_name != db_name:
        data_manager = DataManager(db_name=db_name)
    return data_manager
