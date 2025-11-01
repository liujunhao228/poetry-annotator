import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type

# 导入需要管理的组件类
# 注意：这里我们导入的是类，而不是全局实例
# 使用 absolute import，因为 project.py 可能作为顶层模块运行
relative_import_failed = False
try:
    # 当作为包运行时（推荐方式）
    from .config_manager import ConfigManager
    from .logging_config import setup_default_logging, get_logger
    from .data_manager import DataManager as BaseDataManager
    from .label_parser import LabelParser as BaseLabelParser
    from .llm_factory import LLMFactory as BaseLLMFactory
    from .annotator import Annotator as BaseAnnotator
except ImportError as e:
    relative_import_failed = True
    print(f"Project模块相对导入失败: {e}")

# 如果相对导入失败，则尝试绝对导入
if relative_import_failed:
    # 当直接运行时（兼容开发环境）
    # 确保 src 目录在 sys.path 中，以便绝对导入可以找到 src 下的模块
    import sys
    import os
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"已将 {src_dir} 添加到 sys.path")
        
    from config_manager import ConfigManager
    from logging_config import setup_default_logging, get_logger
    from data_manager import DataManager as BaseDataManager
    from label_parser import LabelParser as BaseLabelParser
    from llm_factory import LLMFactory as BaseLLMFactory
    from annotator import Annotator as BaseAnnotator


logger = get_logger(__name__)

class Project:
    """
    Project 类作为项目上下文，负责加载和管理特定项目的所有配置、数据和处理逻辑。
    每个 Project 实例代表一个独立的标注项目，确保资源强绑定和隔离。
    """
    def __init__(self, project_name: str, project_root_dir: Path):
        self.name = project_name
        self.root_path = project_root_dir / project_name
        self.config_path = self.root_path / "config.ini"
        self.project_src_path = self.root_path / "src" # 项目专属的 src 目录

        # 验证项目目录和配置文件是否存在
        if not self.root_path.is_dir():
            raise ValueError(f"项目目录 '{self.root_path}' 不存在。")
        if not self.config_path.is_file():
            raise ValueError(f"项目 '{project_name}' 的配置文件 '{self.config_path}' 不存在。")
        if not self.project_src_path.is_dir():
            raise ValueError(f"项目 '{project_name}' 的专属 src 目录 '{self.project_src_path}' 不存在。")

        # 将项目专属的 src 目录添加到 Python 模块搜索路径
        # 确保它在标准 src 目录之前被搜索，以优先加载项目专属模块
        if str(self.project_src_path) not in sys.path:
            sys.path.insert(0, str(self.project_src_path))
            logger.debug(f"已将项目专属 src 目录 '{self.project_src_path}' 添加到 sys.path")

        # 懒加载的组件实例
        self._config_manager: Optional[ConfigManager] = None
        self._data_manager_instances: Dict[str, BaseDataManager] = {} # 存储不同数据库名称的DataManager实例
        self._label_parser: Optional[BaseLabelParser] = None
        self._llm_factory: Optional[BaseLLMFactory] = None
        self._annotator_instances: Dict[str, BaseAnnotator] = {} # 存储不同模型配置的Annotator实例

        logger.info(f"项目 '{self.name}' 上下文已初始化，根路径: {self.root_path}")

    def _load_project_component(self, module_name: str, class_name: str) -> Type[Any]:
        """
        动态加载项目专属的组件类。
        确保从项目专属的 src 目录加载，且不允许回退到默认实现。
        """
        module_path = self.project_src_path / f"{module_name}.py"
        if not module_path.is_file():
            raise FileNotFoundError(f"项目 '{self.name}' 的专属模块 '{module_path}' 不存在。")

        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None:
            raise ImportError(f"无法为模块 '{module_name}' 创建模块规范。")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module # 将模块添加到 sys.modules
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"加载项目 '{self.name}' 的模块 '{module_name}' 失败: {e}") from e

        component_class = getattr(module, class_name, None)
        if component_class is None:
            raise AttributeError(f"模块 '{module_name}' 中未找到类 '{class_name}'。")
        
        logger.debug(f"成功从项目 '{self.name}' 专属 src 目录加载组件: {class_name} (来自 {module_path})")
        return component_class

    @property
    def config_manager(self) -> ConfigManager:
        """获取项目专属的 ConfigManager 实例"""
        if self._config_manager is None:
            logger.debug(f"为项目 '{self.name}' 懒加载 ConfigManager，路径: {self.config_path}")
            self._config_manager = ConfigManager(config_path=str(self.config_path))
        return self._config_manager

    @property
    def label_parser(self) -> BaseLabelParser:
        """获取项目专属的 LabelParser 实例"""
        if self._label_parser is None:
            logger.debug(f"为项目 '{self.name}' 懒加载 LabelParser")
            LabelParserClass = self._load_project_component("label_parser", "LabelParser")
            categories_config = self.config_manager.get_categories_config()
            xml_path = self.root_path / categories_config.get('xml_path', 'categories.xml')
            md_path = self.root_path / categories_config.get('md_path', 'classification_schema.md')
            self._label_parser = LabelParserClass(xml_path=str(xml_path), md_path=str(md_path))
        return self._label_parser

    @property
    def llm_factory(self) -> BaseLLMFactory:
        """获取项目专属的 LLMFactory 实例"""
        if self._llm_factory is None:
            logger.debug(f"为项目 '{self.name}' 懒加载 LLMFactory")
            LLMFactoryClass = self._load_project_component("llm_factory", "LLMFactory")
            self._llm_factory = LLMFactoryClass(self.config_manager)
        return self._llm_factory

    def get_data_manager(self, db_name: str = "default") -> BaseDataManager:
        """
        获取项目专属的 DataManager 实例。
        DataManager 可能需要根据不同的数据库名称进行实例化，因此不作为单一属性。
        """
        if db_name not in self._data_manager_instances:
            # DataManager 的实例化逻辑需要根据 config_manager 获取 db_path
            # 并且 db_path 应该是相对于项目根目录的
            db_config = self.config_manager.get_database_config()
            
            db_path_str: Optional[str] = None
            if 'db_paths' in db_config and db_config['db_paths']:
                db_paths = db_config['db_paths']
                if db_name == "default":
                    # 默认使用第一个数据库
                    db_path_str = next(iter(db_paths.values()))
                else:
                    if db_name not in db_paths:
                        raise ValueError(f"数据库 '{db_name}' 未在项目 '{self.name}' 的配置中定义。")
                    db_path_str = db_paths[db_name]
            elif 'db_path' in db_config and db_config['db_path']:
                db_path_str = db_config['db_path']
            else:
                raise ValueError(f"项目 '{self.name}' 的配置文件中未找到数据库路径配置。")
            
            full_db_path = self.root_path / db_path_str
            
            # DataManager 内部会处理数据库的初始化，这里只负责传递路径
            logger.debug(f"为项目 '{self.name}' 获取 DataManager，数据库路径: {full_db_path}, 数据库别名: {db_name}")
            
            # DataManager 还需要知道其数据源目录和输出目录，也应是项目专属的
            data_config = self.config_manager.get_data_config()
            source_dir = self.root_path / data_config.get('source_dir', 'data') # 默认 'data' 目录
            output_dir = self.root_path / data_config.get('output_dir', 'output') # 默认 'output' 目录

            DataManagerClass = self._load_project_component("data_manager", "DataManager")
            self._data_manager_instances[db_name] = DataManagerClass(
                db_path=str(full_db_path), 
                source_dir=str(source_dir), 
                output_dir=str(output_dir),
                db_name_alias=db_name # 传递db_name_alias用于DataManager内部的ID前缀设置
            )
        return self._data_manager_instances[db_name]

    def get_annotator(self, config_name: str) -> BaseAnnotator:
        """获取项目专属的 Annotator 实例"""
        if config_name not in self._annotator_instances:
            logger.debug(f"为项目 '{self.name}' 和模型 '{config_name}' 懒加载 Annotator")
            AnnotatorClass = self._load_project_component("annotator", "Annotator")
            self._annotator_instances[config_name] = AnnotatorClass(
                config_name=config_name,
                project_context=self # 传递 Project 实例作为上下文
            )
        return self._annotator_instances[config_name]

    def get_project_logging_config(self) -> Dict[str, Any]:
        """获取项目专属的日志配置"""
        log_config = self.config_manager.get_logging_config()
        # 确保日志文件路径是相对于项目根目录的
        log_file_path = self.root_path / log_config.get('log_file', 'logs/project_annotator.log')
        log_config['log_file'] = str(log_file_path)
        return log_config

    def setup_project_logging(self):
        """设置项目专属的日志"""
        log_config = self.get_project_logging_config()
        # Ensure the directory for the log file exists
        log_file_path = Path(log_config['log_file'])
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        setup_default_logging(
            console_level=log_config['console_log_level'],
            enable_file_log=log_config['enable_file_log'],
            log_file=log_config['log_file'],
            file_level=log_config['file_log_level'] # Pass file_level explicitly
        )
        logger = get_logger(__name__)  # Re-get logger after setting up logging
        logger.info(f"项目 '{self.name}' 日志已配置，日志文件: {log_config['log_file']}")
