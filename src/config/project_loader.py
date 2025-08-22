"""
项目配置加载器，负责从项目配置文件加载配置到对应的 schema 对象中。
"""

import configparser
import os
from typing import Dict, Any, Optional

from src.config.schema import (
    ProjectConfig, ProjectLLMConfig, ProjectDatabaseConfig, ProjectDataPathConfig,
    ProjectPromptConfig, ProjectLoggingConfig, ProjectVisualizerConfig,
    ProjectModelConfig, ProjectValidationConfig, ProjectPreprocessingConfig,
    ProjectCleaningConfig
)


class ProjectConfigLoader:
    """项目配置加载器"""

    def __init__(self, project_config_path: str):
        self.project_config_path = project_config_path

    def load(self) -> ProjectConfig:
        """加载项目配置文件"""
        if not os.path.exists(self.project_config_path):
            print(f"警告: 项目配置文件不存在: {self.project_config_path}。将使用默认配置。")
            return ProjectConfig()

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.project_config_path, encoding='utf-8')

        project_config = ProjectConfig()

        # 项目LLM配置（暂无特殊字段）
        project_config.llm = ProjectLLMConfig()

        # 项目数据库配置
        if config.has_section('Database'):
            db_config = ProjectDatabaseConfig()
            # 尝试获取新的多数据库配置
            db_paths_str = config.get('Database', 'db_paths', fallback=None)
            if db_paths_str:
                # 解析 "name1=path1,name2=path2" 格式
                db_paths = {}
                for item in db_paths_str.split(','):
                    if '=' in item:
                        name, path = item.split('=', 1)
                        db_paths[name.strip()] = path.strip()
                db_config.db_paths = db_paths

            # 回退到旧的单数据库配置
            if not db_config.db_paths:
                db_path = config.get('Database', 'db_path', fallback=None)
                if db_path:
                    db_config.db_path = db_path

            # 获取分离数据库配置
            separate_db_paths_str = config.get('Database', 'separate_db_paths', fallback=None)
            if separate_db_paths_str:
                # 解析 "name1=path1,name2=path2" 格式
                separate_db_paths = {}
                for item in separate_db_paths_str.split(','):
                    if '=' in item:
                        name, path = item.split('=', 1)
                        separate_db_paths[name.strip()] = path.strip()
                db_config.separate_db_paths = separate_db_paths

            # 获取配置名称
            config_name = config.get('Database', 'config_name', fallback='default')
            db_config.config_name = config_name
            project_config.database = db_config

        # 项目数据路径配置
        if config.has_section('Data'):
            data_config = ProjectDataPathConfig()
            data_config.source_dir = config.get('Data', 'source_dir', fallback=None)
            data_config.output_dir = config.get('Data', 'output_dir', fallback=None)
            data_config.config_name = config.get('Data', 'config_name', fallback='default')
            project_config.data_path = data_config

        # 项目提示词配置
        if config.has_section('Prompt'):
            prompt_config = ProjectPromptConfig()
            prompt_config.template_path = config.get('Prompt', 'template_path', fallback=None)
            prompt_config.system_prompt_instruction_template = config.get(
                'Prompt', 'system_prompt_instruction_template', fallback=None)
            prompt_config.system_prompt_example_template = config.get(
                'Prompt', 'system_prompt_example_template', fallback=None)
            prompt_config.user_prompt_template = config.get(
                'Prompt', 'user_prompt_template', fallback=None)
            prompt_config.config_name = config.get('Prompt', 'config_name', fallback='default')
            project_config.prompt = prompt_config

        # 项目日志配置（暂无特殊字段）
        project_config.logging = ProjectLoggingConfig()

        # 项目可视化配置（暂无特殊字段）
        project_config.visualizer = ProjectVisualizerConfig()

        # 项目模型配置
        if config.has_section('Model'):
            model_names_str = config.get('Model', 'model_names', fallback='')
            model_names = [name.strip() for name in model_names_str.split(',') if name.strip()]
            project_config.model = ProjectModelConfig(model_names=model_names)

        # 项目校验规则配置
        if config.has_section('Validation'):
            ruleset_name = config.get('Validation', 'ruleset_name',
                                      fallback="default_emotion_annotation")  # 默认值应该从全局配置获取
            project_config.validation = ProjectValidationConfig(ruleset_name=ruleset_name)

        # 项目预处理规则配置
        if config.has_section('Preprocessing'):
            ruleset_name = config.get('Preprocessing', 'ruleset_name',
                                      fallback="social_emotion")  # 默认值应该从全局配置获取
            project_config.preprocessing = ProjectPreprocessingConfig(ruleset_name=ruleset_name)

        # 项目清洗规则配置
        if config.has_section('Cleaning'):
            ruleset_name = config.get('Cleaning', 'ruleset_name',
                                      fallback="default")  # 默认值应该从全局配置获取
            project_config.cleaning = ProjectCleaningConfig(ruleset_name=ruleset_name)

        return project_config

    def save(self, project_config: ProjectConfig):
        """将当前项目配置写入文件"""
        if not self.project_config_path:
            raise ValueError("未指定项目配置文件路径")

        config = configparser.ConfigParser(interpolation=None)

        # 数据库配置
        config.add_section('Database')
        db = project_config.database
        if db.db_paths:
            db_paths_str = ','.join(f"{k}={v}" for k, v in db.db_paths.items())
            config.set('Database', 'db_paths', db_paths_str)
        elif db.db_path:
            config.set('Database', 'db_path', db.db_path)
        config.set('Database', 'config_name', db.config_name)
        
        # 保存分离数据库配置
        if db.separate_db_paths:
            separate_db_paths_str = ','.join(f"{k}={v}" for k, v in db.separate_db_paths.items())
            config.set('Database', 'separate_db_paths', separate_db_paths_str)

        # 数据路径配置
        config.add_section('Data')
        data = project_config.data_path
        if data.source_dir:
            config.set('Data', 'source_dir', data.source_dir)
        if data.output_dir:
            config.set('Data', 'output_dir', data.output_dir)
        config.set('Data', 'config_name', data.config_name)

        # 提示词配置
        config.add_section('Prompt')
        prompt = project_config.prompt
        if prompt.template_path:
            config.set('Prompt', 'template_path', prompt.template_path)
        if prompt.system_prompt_instruction_template:
            config.set('Prompt', 'system_prompt_instruction_template',
                       prompt.system_prompt_instruction_template)
        if prompt.system_prompt_example_template:
            config.set('Prompt', 'system_prompt_example_template',
                       prompt.system_prompt_example_template)
        if prompt.user_prompt_template:
            config.set('Prompt', 'user_prompt_template', prompt.user_prompt_template)
        config.set('Prompt', 'config_name', prompt.config_name)

        # 模型配置
        config.add_section('Model')
        model = project_config.model
        config.set('Model', 'model_names', ','.join(model.model_names))

        # 校验规则配置
        config.add_section('Validation')
        validation = project_config.validation
        config.set('Validation', 'ruleset_name', validation.ruleset_name)

        # 预处理规则配置
        config.add_section('Preprocessing')
        preprocessing = project_config.preprocessing
        config.set('Preprocessing', 'ruleset_name', preprocessing.ruleset_name)

        # 清洗规则配置
        config.add_section('Cleaning')
        cleaning = project_config.cleaning
        config.set('Cleaning', 'ruleset_name', cleaning.ruleset_name)

        # 保存到文件
        with open(self.project_config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)