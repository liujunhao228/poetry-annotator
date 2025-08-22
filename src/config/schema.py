"""
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
    system_prompt_instruction_template: str = "config/system_prompt_instruction.txt"
    system_prompt_example_template: str = "config/system_prompt_example.txt"
    user_prompt_template: str = "config/user_prompt_template.txt"
    # 可以添加更多通用字段...

# --- 全局规则配置 (Global Rule Configuration) ---

@dataclass
class GlobalValidationRuleSet:
    """全局校验规则集"""
    # 定义多个校验规则集的名称
    available_rulesets: List[str] = field(default_factory=lambda: ["default_emotion_annotation"])
    # 当前激活的规则集名称
    active_ruleset: str = "default_emotion_annotation"

@dataclass
class GlobalPreprocessingRuleSet:
    """全局预处理分类规则集"""
    # 定义多个预处理规则集的名称
    available_rulesets: List[str] = field(default_factory=lambda: ["social_emotion"])
    # 当前激活的规则集名称
    active_ruleset: str = "social_emotion"

@dataclass
class GlobalCleaningRuleSet:
    """全局清洗规则"""
    # 定义多个清洗规则集的名称 (如果未来支持多种)
    available_rulesets: List[str] = field(default_factory=lambda: ["default"])
    # 当前激活的规则集名称
    active_ruleset: str = "default"

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
    # 或者直接指定数据库路径 (可选，优先级高于config_name)
    db_paths: Optional[Dict[str, str]] = None  # e.g., {"TangShi": "data/TangShi.db"}
    db_path: Optional[str] = None  # 旧的单数据库模式，用于向后兼容
    # 分离数据库路径配置（可选，优先级高于全局配置中的模板）
    separate_db_paths: Optional[Dict[str, str]] = None  # e.g., {"raw_data": "data/raw_data.db"}
    # 分离数据库路径配置（可选，优先级高于全局配置中的模板）
    separate_db_paths: Optional[Dict[str, str]] = None  # e.g., {"raw_data": "data/raw_data.db"}

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
    # 或者直接指定提示词模板路径 (可选，优先级高于config_name)
    template_path: Optional[str] = None
    system_prompt_instruction_template: Optional[str] = None
    system_prompt_example_template: Optional[str] = None
    user_prompt_template: Optional[str] = None

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
class ProjectValidationConfig:
    """项目校验规则配置"""
    # 指定要使用的校验规则集名称（来自GlobalValidationRuleSet.available_rulesets）
    ruleset_name: str = "default_emotion_annotation"

@dataclass
class ProjectPreprocessingConfig:
    """项目预处理分类规则配置"""
    # 指定要使用的预处理规则集名称（来自GlobalPreprocessingRuleSet.available_rulesets）
    ruleset_name: str = "social_emotion"

@dataclass
class ProjectCleaningConfig:
    """项目清洗规则配置"""
    # 指定要使用的清洗规则集名称（来自GlobalCleaningRuleSet.available_rulesets）
    ruleset_name: str = "default"

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
    validation: GlobalValidationRuleSet = field(default_factory=GlobalValidationRuleSet)
    preprocessing: GlobalPreprocessingRuleSet = field(default_factory=GlobalPreprocessingRuleSet)
    cleaning: GlobalCleaningRuleSet = field(default_factory=GlobalCleaningRuleSet)

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
    validation: ProjectValidationConfig = field(default_factory=ProjectValidationConfig)
    preprocessing: ProjectPreprocessingConfig = field(default_factory=ProjectPreprocessingConfig)
    cleaning: ProjectCleaningConfig = field(default_factory=ProjectCleaningConfig)