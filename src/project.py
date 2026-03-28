"""
Project 类 - 项目上下文管理器

Project class - project context manager
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.config_manager import ConfigManager
from src.logging_config import setup_default_logging, get_logger
from src.data_manager import DataManager
from src.llm_factory import LLMFactory
from src.projects import get_project_type, list_project_types

logger = get_logger(__name__)


class Project:
    """
    Project 类作为项目上下文，负责加载和管理特定项目的所有配置、数据和处理逻辑。
    每个 Project 实例代表一个独立的标注项目，确保资源强绑定和隔离。
    
    新架构：
    - 通用组件（LLMFactory, DataManager）从主程序加载
    - 项目特定组件（Annotator）从项目注册表加载
    - 项目类型通过 project_type.txt 指定
    """
    
    def __init__(self, project_name: str, project_root_dir: Path, global_config_path: Path):
        self.name = project_name
        self.root_path = project_root_dir / project_name
        self.global_config_path = global_config_path
        self.project_config_file_path = self.root_path / "config.ini"
        self.project_type_file_path = self.root_path / "project_type.txt"
        
        # 验证项目目录是否存在
        if not self.root_path.is_dir():
            raise ValueError(f"项目目录 '{self.root_path}' 不存在。")
        
        # 读取项目类型
        self.project_type = self._load_project_type()
        
        # 获取项目类型的组件类
        try:
            self._project_components = get_project_type(self.project_type)
            logger.info(f"项目 '{self.name}' 使用项目类型：{self.project_type}")
        except ValueError as e:
            logger.warning(f"加载项目类型失败：{e}")
            self._project_components = None
        
        # 懒加载的组件实例
        self._config_manager: Optional[ConfigManager] = None
        self._data_manager_instances: Dict[str, DataManager] = {}
        self._llm_factory: Optional[LLMFactory] = None
        self._annotator_instances: Dict[str, Any] = {}
        
        logger.info(f"项目 '{self.name}' 上下文已初始化，根路径：{self.root_path}, 项目类型：{self.project_type}")
    
    def _load_project_type(self) -> str:
        """
        加载项目类型
        
        从 project_type.txt 文件读取项目类型
        如果文件不存在，默认使用 'social_analysis'
        """
        if self.project_type_file_path.exists():
            project_type = self.project_type_file_path.read_text(encoding='utf-8').strip()
            logger.debug(f"从 {self.project_type_file_path} 加载项目类型：{project_type}")
            return project_type
        else:
            # 默认使用社会分析项目
            logger.debug(f"项目类型文件不存在，使用默认类型：social_analysis")
            return "social_analysis"
    
    @property
    def config_manager(self) -> ConfigManager:
        """获取 ConfigManager 实例"""
        if self._config_manager is None:
            logger.debug(f"为项目 '{self.name}' 懒加载 ConfigManager")
            
            # 检测配置模式
            project_config_exists = self.project_config_file_path.exists()
            legacy_project_extra = self.root_path / "project_config.ini"
            legacy_mode = False
            
            if not project_config_exists:
                if legacy_project_extra.exists():
                    logger.warning(
                        f"项目 '{self.name}' 使用旧版配置结构（三文件模式）。"
                        f"建议迁移到简化结构。"
                    )
                    legacy_mode = True
                    self.project_config_file_path = self.root_path / "config.ini"
                else:
                    raise FileNotFoundError(
                        f"项目配置文件不存在：{self.project_config_file_path}\n"
                        f"请创建项目配置文件或运行迁移工具。"
                    )
            
            if legacy_mode:
                self._config_manager = ConfigManager(
                    config_paths=[
                        str(self.global_config_path),
                        str(self.project_config_file_path),
                        str(legacy_project_extra)
                    ],
                    legacy_mode=True
                )
            else:
                self._config_manager = ConfigManager(
                    config_paths=[str(self.project_config_file_path)]
                )
        
        return self._config_manager
    
    @property
    def llm_factory(self) -> LLMFactory:
        """获取 LLMFactory 实例（从主程序加载）"""
        if self._llm_factory is None:
            logger.debug(f"为项目 '{self.name}' 懒加载 LLMFactory")
            self._llm_factory = LLMFactory(self.config_manager)
        return self._llm_factory
    
    def get_data_manager(self, db_name: str = "default") -> DataManager:
        """
        获取 DataManager 实例（从主程序加载）
        
        Args:
            db_name: 数据库别名
        """
        if db_name not in self._data_manager_instances:
            db_config = self.config_manager.get_database_config()
            
            db_path_str: Optional[str] = None
            if 'db_paths' in db_config and db_config['db_paths']:
                db_paths = db_config['db_paths']
                if db_name == "default":
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
            
            logger.debug(f"为项目 '{self.name}' 获取 DataManager，数据库路径：{full_db_path}, 数据库别名：{db_name}")
            
            data_config = self.config_manager.get_data_config()
            source_dir = self.root_path / data_config.get('source_dir', 'data')
            output_dir = self.root_path / data_config.get('output_dir', 'output')
            
            self._data_manager_instances[db_name] = DataManager(
                db_path=str(full_db_path),
                source_dir=str(source_dir),
                output_dir=str(output_dir),
                db_name_alias=db_name
            )
        
        return self._data_manager_instances[db_name]
    
    def get_annotator(self, config_name: str) -> Any:
        """
        获取项目专属的 Annotator 实例
        
        从项目注册表加载项目类型的 Annotator 类
        
        Args:
            config_name: 模型配置别名
        """
        if config_name not in self._annotator_instances:
            logger.debug(f"为项目 '{self.name}' 和模型 '{config_name}' 懒加载 Annotator")
            
            if self._project_components is None:
                raise RuntimeError(f"项目类型 '{self.project_type}' 未正确加载")
            
            AnnotatorClass = self._project_components.get("annotator")
            if AnnotatorClass is None:
                raise RuntimeError(f"项目类型 '{self.project_type}' 未定义 annotator 组件")
            
            self._annotator_instances[config_name] = AnnotatorClass(
                config_name=config_name,
                project_context=self
            )
        
        return self._annotator_instances[config_name]
    
    def get_project_logging_config(self) -> Dict[str, Any]:
        """获取项目专属的日志配置"""
        log_config = self.config_manager.get_logging_config()
        log_file_path = self.root_path / log_config.get('log_file', 'logs/project_annotator.log')
        log_config['log_file'] = str(log_file_path)
        return log_config
    
    def setup_project_logging(self):
        """设置项目专属的日志"""
        log_config = self.get_project_logging_config()
        log_file_path = Path(log_config['log_file'])
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        setup_default_logging(
            console_level=log_config['console_log_level'],
            enable_file_log=log_config['enable_file_log'],
            log_file=log_config['log_file'],
            file_level=log_config['file_log_level'],
            global_config_path=self.global_config_path
        )
        logger = get_logger(__name__)
        logger.info(f"项目 '{self.name}' 日志已配置，日志文件：{log_config['log_file']}")
    
    def ensure_project_dirs(self):
        """确保项目所需的数据和日志目录存在"""
        data_dir = self.root_path / "data"
        logs_dir = self.root_path / "logs"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"项目 '{self.name}' 的数据目录 '{data_dir}' 和日志目录 '{logs_dir}' 已确认存在。")
