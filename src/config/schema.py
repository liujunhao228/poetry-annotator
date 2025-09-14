""""
配置项模式定义模块。

此模块定义了项目中使用的所有配置项的模式，包括：
- 全局配置（Global Configuration）
- 项目配置（Project Configuration）
- 各种子配置（如数据库、数据路径、模型、日志等）

该模块旨在为配置管理器提供清晰的结构和类型定义。
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path

# --- 全局通用配置 (Global Common Configuration) ---

@dataclass
class GlobalLLMConfig:
    """全局LLM配置"""
    max_workers: int = 1
    max_model_pipelines: int = 1
    max_retries: int = 3
    retry_delay: int = 5
    breaker_fail_max: int = 3
    breaker_reset_timeout: int = 60
    save_full_response: bool = False

@dataclass
class GlobalDatabaseConfig:
    """全局数据库配置 (定义可用数据库配置)"""
    # 注意：这里只定义可用配置的模式/名称，实际路径在项目配置中指定
    available_configs: List[str] = field(default_factory=lambda: ["default"])
    # 分离数据库配置模板
    separate_db_template: Optional[Dict[str, str]] = None
    
@dataclass
class GlobalDataPathConfig:
    """全局数据路径配置 (定义可用数据路径配置)"""
    # 注意：这里只定义可用配置的模式/名称，实际路径在项目配置中指定
    available_configs: List[str] = field(default_factory=lambda: ["default"])

@dataclass
class GlobalPromptConfig:
    """全局提示词配置 (定义可用提示词配置)"""
    # 注意：这里只定义可用配置的模式/名称，实际路径在项目配置中指定
    available_configs: List[str] = field(default_factory=lambda: ["default"])

@dataclass
class GlobalLoggingConfig:
    """全局日志系统配置"""
    console_log_level: str = "INFO"
    file_log_level: str = "DEBUG"
    enable_file_log: bool = True
    log_file: str = ""
    enable_console_log: bool = True
    max_file_size: int = 10  # MB
    backup_count: int = 5
    quiet_third_party: bool = True

@dataclass
class GlobalVisualizerConfig:
    """全局数据可视化配置"""
    enable_custom_download: bool = False

@dataclass
class GlobalCategoriesConfig:
    """全局情感分类配置"""
    xml_path: str = ""
    md_path: str = ""


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    path: str = ""
    module: str = ""
    class_name: str = ""
    # 插件特定配置项将通过字典方式访问
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    path: str = ""
    module: str = ""
    class_name: str = ""
    # 插件特定配置项将通过字典方式访问
    settings: Dict[str, Any] = field(default_factory=dict)




@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    path: str = ""
    module: str = ""
    class_name: str = ""
    # 插件特定配置项将通过字典方式访问
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GlobalModelConfigTemplate:
    """全局模型配置模板 (定义可用模型配置的通用字段)"""
    provider: str = ""
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""
    request_delay: float = 1.0
    temperature: float = 1.0
    max_tokens: int = 1000
    timeout: int = 30
    # 可以添加更多通用字段...

# --- 项目级别配置 (Project Level Configuration) ---

@dataclass
class ProjectLLMConfig:
    """项目LLM配置"""
    # 项目可以覆盖全局LLM配置的某些字段，或添加项目特定的字段
    pass  # 当前版本暂无特殊项目级LLM配置

@dataclass
class ProjectDatabaseConfig:
    """项目数据库配置"""
    # 指定要使用的数据库配置名称（来自GlobalDatabaseConfig.available_configs）
    config_name: str = "default"

@dataclass
class ProjectDataPathConfig:
    """项目数据路径配置"""
    # 指定要使用的数据路径配置名称（来自GlobalDataPathConfig.available_configs）
    config_name: str = "default"
    # 或者直接指定数据路径 (可选，优先级高于config_name)
    source_dir: Optional[str] = None
    output_dir: Optional[str] = None

@dataclass
class ProjectPromptConfig:
    """项目提示词配置"""
    # 指定要使用的提示词配置名称（来自GlobalPromptConfig.available_configs）
    config_name: str = "default"

@dataclass
class ProjectLoggingConfig:
    """项目日志配置"""
    # 项目可以覆盖全局日志配置的某些字段，或添加项目特定的字段
    pass  # 当前版本暂无特殊项目级日志配置

@dataclass
class ProjectVisualizerConfig:
    """项目可视化配置"""
    # 项目可以覆盖全局可视化配置的某些字段，或添加项目特定的字段
    pass  # 当前版本暂无特殊项目级可视化配置

@dataclass
class ProjectModelConfig:
    """项目模型配置"""
    # 指定要使用的模型配置名称列表（来自配置文件中定义的Model.<name>节）
    model_names: List[str] = field(default_factory=lambda: ["qwen-max"])

@dataclass
class ProjectPluginsConfig:
    """项目插件配置"""
    enabled_plugins: List[str] = field(default_factory=list)
    plugin_paths: List[str] = field(default_factory=list)

# --- 主配置类 ---

@dataclass
class GlobalConfig:
    """全局配置"""
    llm: GlobalLLMConfig = field(default_factory=GlobalLLMConfig)
    database: GlobalDatabaseConfig = field(default_factory=GlobalDatabaseConfig)
    data_path: GlobalDataPathConfig = field(default_factory=GlobalDataPathConfig)
    prompt: GlobalPromptConfig = field(default_factory=GlobalPromptConfig)
    logging: GlobalLoggingConfig = field(default_factory=GlobalLoggingConfig)
    visualizer: GlobalVisualizerConfig = field(default_factory=GlobalVisualizerConfig)
    # 新增 Categories 配置
    categories: GlobalCategoriesConfig = field(default_factory=GlobalCategoriesConfig)
    model_template: GlobalModelConfigTemplate = field(default_factory=GlobalModelConfigTemplate)

@dataclass
class ProjectConfig:
    """项目配置"""
    llm: ProjectLLMConfig = field(default_factory=ProjectLLMConfig)
    database: ProjectDatabaseConfig = field(default_factory=ProjectDatabaseConfig)
    data_path: ProjectDataPathConfig = field(default_factory=ProjectDataPathConfig)
    prompt: ProjectPromptConfig = field(default_factory=ProjectPromptConfig)
    logging: ProjectLoggingConfig = field(default_factory=ProjectLoggingConfig)
    visualizer: ProjectVisualizerConfig = field(default_factory=ProjectVisualizerConfig)
    model: ProjectModelConfig = field(default_factory=ProjectModelConfig)
    plugins: ProjectPluginsConfig = field(default_factory=ProjectPluginsConfig)
