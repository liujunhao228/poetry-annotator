"""
核心配置管理器，负责协调全局和项目配置的加载、管理和获取。
"""

import os
from typing import Dict, Any, Optional, List

from src.config.schema import GlobalConfig, ProjectConfig, PluginConfig, ProjectPluginsConfig
from src.config.global_config_loader import GlobalConfigLoader
from src.config.project_config_loader import ProjectConfigLoader
from src.config.project_manager import ProjectConfigManager
from src.config.model_manager import ModelManager
from src.config.validator import ConfigValidator
from src.config.plugin_loader import ProjectPluginConfigLoader


# 全局配置实例
_config_manager_instance: Optional['ConfigManager'] = None


def get_config_manager(global_config_path: Optional[str] = None,
                       project_config_path: Optional[str] = None) -> 'ConfigManager':
    """获取全局配置管理器实例"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(global_config_path, project_config_path)
    return _config_manager_instance


class ConfigManager:
    """增强型配置管理器"""

    def __init__(self, global_config_path: Optional[str] = None,
                 project_config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            global_config_path: 全局配置文件路径 (可选)
            project_config_path: 项目配置文件路径（可选）
                               如果未提供，则使用默认项目配置文件 (project/project.ini)
        """
        # 确定配置文件路径
        if global_config_path is None:
            self.global_config_path = "config/global/config.ini"
        else:
            self.global_config_path = global_config_path
            
        if project_config_path is None:
            # 如果没有显式指定项目配置文件，则使用默认项目配置文件
            self.project_config_path = "project/project.ini"
        else:
            self.project_config_path = project_config_path

        # 初始化配置对象
        self.global_config = GlobalConfig()
        self.project_config = ProjectConfig() if self.project_config_path else None

        # 初始化加载器和管理器
        self.global_loader = GlobalConfigLoader(self.global_config_path)
        self.project_loader = ProjectConfigLoader(self.project_config_path) if self.project_config_path else None
        self.project_plugin_loader = ProjectPluginConfigLoader("project/plugins.ini") if self.project_config_path else None
        self.model_manager = ModelManager(self.global_config_path)
        self.validator = ConfigValidator(self.global_config_path)
        self.project_manager = ProjectConfigManager()

        # 加载配置
        self._load_global_config()
        if self.project_config:
            self._load_project_config()

    def _load_global_config(self):
        """加载全局配置文件"""
        self.global_config = self.global_loader.load()

    def _load_project_config(self):
        """加载项目配置文件（如果指定了项目配置文件）"""
        if self.project_loader:
            self.project_config = self.project_loader.load()
            # Load plugin configurations and merge into project_config
            if self.project_plugin_loader:
                self.project_config.plugins = self.project_plugin_loader.load_project_plugin_config()

    def save_global_config(self):
        """将当前全局配置写入文件"""
        self.global_loader.save(self.global_config)

    def save_project_config(self):
        """将当前项目配置写入文件"""
        if self.project_loader and self.project_config:
            # Save plugin configurations first
            if self.project_plugin_loader:
                self.project_plugin_loader.save_project_plugin_config(self.project_config.plugins)
            self.project_loader.save(self.project_config)

    # --- 配置获取方法 ---

    def get_effective_database_config(self) -> Dict[str, Any]:
        """获取生效的数据库配置，支持主数据库和分离数据库"""
        if not self.project_config:
            # 只有全局配置
            return self.global_loader._get_global_database_config()

        # 优先使用项目配置
        project_db = self.project_config.database
        # 检查项目配置中是否有任何数据库相关设置
        config = {}
        
        # 处理主数据库路径配置
        if project_db.db_paths:
            config['db_paths'] = project_db.db_paths
        elif project_db.db_path:
            config['db_path'] = project_db.db_path
            
        # 处理分离数据库配置
        separate_db_config = self._get_effective_separate_database_config()
        if separate_db_config:
            config['separate_db_paths'] = separate_db_config
            
        return config

    def _get_effective_separate_database_config(self) -> Optional[Dict[str, str]]:
        """获取生效的分离数据库配置"""
        # 首先检查项目配置中是否有分离数据库配置
        if self.project_config and hasattr(self.project_config.database, 'separate_db_paths'):
            separate_db_paths = getattr(self.project_config.database, 'separate_db_paths', None)
            if separate_db_paths:
                return separate_db_paths

        # 如果项目配置中没有，则使用全局配置中的模板
        if self.global_config.database.separate_db_template:
            return self.global_config.database.separate_db_template

        return None

    def _get_global_database_config_by_name(self, config_name: str) -> Dict[str, Any]:
        """根据配置名称获取全局数据库配置"""
        # 这个实现与_get_global_database_config类似，但更明确地表明是按名称查找
        return self.global_loader._get_global_database_config()

    def get_effective_data_config(self) -> Dict[str, str]:
        """获取生效的数据路径配置"""
        if not self.project_config:
            # 只有全局配置
            return self.global_loader._get_global_data_config()

        # 优先使用项目配置
        project_data = self.project_config.data_path
        if project_data.source_dir and project_data.output_dir:
            # 项目配置中直接指定了路径
            return {
                'source_dir': project_data.source_dir,
                'output_dir': project_data.output_dir
            }
        else:
            # 使用项目配置中指定的配置名称，在全局配置中查找
            config_name = project_data.config_name
            return self._get_global_data_config_by_name(config_name)

    def _get_global_data_config_by_name(self, config_name: str) -> Dict[str, str]:
        """根据配置名称获取全局数据路径配置"""
        # 与_get_global_data_config类似
        return self.global_loader._get_global_data_config()

    def get_effective_prompt_config(self) -> Dict[str, str]:
        """获取生效的提示词配置"""
        # 不再使用模板文件，返回空配置
        return {}

    def _get_global_prompt_config_by_name(self, config_name: str) -> Dict[str, str]:
        """根据配置名称获取全局提示词配置"""
        # 与_get_global_prompt_config类似
        return self.global_loader._get_global_prompt_config()

    def get_effective_logging_config(self) -> Dict[str, Any]:
        """获取生效的日志配置"""
        # 日志配置通常不区分项目级和全局级，直接使用全局配置
        log = self.global_config.logging
        return {
            'console_log_level': log.console_log_level,
            'file_log_level': log.file_log_level,
            'enable_file_log': log.enable_file_log,
            'log_file': log.log_file,
            'enable_console_log': log.enable_console_log,
            'max_file_size': log.max_file_size,
            'backup_count': log.backup_count,
            'quiet_third_party': log.quiet_third_party,
        }

    def get_effective_visualizer_config(self) -> Dict[str, Any]:
        """获取生效的可视化配置"""
        # 可视化配置通常不区分项目级和全局级，直接使用全局配置
        viz = self.global_config.visualizer
        return {
            'enable_custom_download': viz.enable_custom_download
        }

    def get_effective_model_configs(self) -> List[Dict[str, Any]]:
        """获取生效的模型配置列表"""
        if not self.project_config:
            # 只有全局配置，返回所有模型配置
            return self.model_manager._get_all_global_model_configs()

        # 使用项目配置中指定的模型名称列表
        model_names = self.project_config.model.model_names
        return self.model_manager.get_effective_model_configs(model_names)


    def get_project_plugins_config(self) -> ProjectPluginsConfig:
        """获取项目插件配置"""
        return self.project_config.plugins


    def get_plugin_config(self, plugin_name: str) -> PluginConfig:
        """获取特定插件配置"""
        return self.project_config.plugins.plugins.get(plugin_name, PluginConfig())

    # --- 其他方法保持不变或稍作修改 ---

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM相关配置"""
        llm = self.global_config.llm
        return {
            'max_workers': llm.max_workers,
            'max_model_pipelines': llm.max_model_pipelines,
            'max_retries': llm.max_retries,
            'retry_delay': llm.retry_delay,
            'breaker_fail_max': llm.breaker_fail_max,
            'breaker_reset_timeout': llm.breaker_reset_timeout,
            'save_full_response': llm.save_full_response
        }

    def get_categories_config(self) -> Dict[str, str]:
        """获取情感分类配置（保持向后兼容）"""
        if not os.path.exists(self.global_config_path):
            return {}

        # 使用configparser直接读取配置文件
        import configparser
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')
        
        if not config.has_section('Categories'):
            return {}

        return {
            'xml_path': config.get('Categories', 'xml_path', fallback=None),
            'md_path': config.get('Categories', 'md_path',
                                  fallback='config/中国古典诗词情感分类体系.md')
        }

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置（用于调试和展示）"""
        all_configs = {
            'global': {
                'llm': self.get_llm_config(),
                'database': self.global_loader._get_global_database_config(),
                'data': self.global_loader._get_global_data_config(),
                'prompt': self.global_loader._get_global_prompt_config(),
                'logging': self.get_effective_logging_config(),
                'visualizer': self.get_effective_visualizer_config(),
                'models': self.model_manager._get_all_global_model_configs()
            },
            'project_management': {
                'active_project': self.get_active_project_config(),
                'available_projects': self.get_available_project_configs()
            }
        }

        if self.project_config:
            all_configs['project'] = {
                'database': self.get_effective_database_config(),
                'data': self.get_effective_data_config(),
                'prompt': self.get_effective_prompt_config(),
                'models': self.get_effective_model_configs()
            }

        return all_configs

    def validate_config(self) -> bool:
        """验证配置的完整性"""
        return self.validator.validate_config(self.project_config_path)
        
    def switch_project_config(self, project_name: str) -> bool:
        """
        切换到指定的项目配置
        
        Args:
            project_name: 要切换到的项目配置文件名（例如："tangshi/project.ini"）
            
        Returns:
            bool: 切换是否成功
        """
        # 验证项目配置文件是否存在
        project_config_path = f"config/projects/{project_name}"
        if not os.path.exists(project_config_path):
            print(f"错误: 项目配置文件不存在: {project_config_path}")
            return False
            
        # 更新active_project.json
        try:
            # 更新激活的项目
            self.project_manager.set_active_project(project_name)
            
            # 重新加载配置
            self.project_config_path = project_config_path
            self.project_config = ProjectConfig()
            self._load_project_config()
            
            print(f"成功切换到项目配置: {project_name}")
            return True
            
        except Exception as e:
            print(f"切换项目配置失败: {e}")
            return False

    def get_available_project_configs(self) -> List[str]:
        """
        获取所有可用的项目配置文件列表
        
        Returns:
            List[str]: 可用的项目配置文件名列表
        """
        return self.project_manager.get_available_projects()
        
    def get_active_project_config(self) -> str:
        """
        获取当前激活的项目配置文件名
        
        Returns:
            str: 当前激活的项目配置文件名
        """
        return self.project_manager.get_active_project()

# 全局配置实例
config_manager = ConfigManager()
