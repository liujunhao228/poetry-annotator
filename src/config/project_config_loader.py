"""
项目配置加载器
"""

import configparser
import os
from typing import Dict, Any, Optional
from src.config.schema import ProjectConfig, ProjectLLMConfig, ProjectDatabaseConfig, ProjectDataPathConfig, ProjectPromptConfig, ProjectLoggingConfig, ProjectVisualizerConfig,ProjectModelConfig


class ProjectConfigLoader:
    """项目配置加载器"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            # 如果配置文件不存在，创建一个空的ConfigParser对象
            return configparser.ConfigParser()
        
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.config_file, encoding='utf-8')
        return config

    def load(self) -> ProjectConfig:
        """加载并返回项目配置对象"""
        project_config = ProjectConfig()
        
        # 加载LLM配置
        project_config.llm = self._load_llm_config()
        
        # 加载数据库配置
        project_config.database = self._load_database_config()
        
        # 加载数据路径配置
        project_config.data_path = self._load_data_path_config()
        
        # 加载提示词配置
        project_config.prompt = self._load_prompt_config()
        
        # 加载日志配置
        project_config.logging = self._load_logging_config()
        
        # 加载可视化配置
        project_config.visualizer = self._load_visualizer_config()
        
        # 加载模型配置
        project_config.model = self._load_model_config()
        
        return project_config

    def save(self, project_config: ProjectConfig):
        """将项目配置保存到文件"""
        # 确保配置文件所在的目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # 创建新的ConfigParser对象
        config = configparser.ConfigParser()
        
        # 保存LLM配置
        self._save_llm_config(config, project_config.llm)
        
        # 保存数据库配置
        self._save_database_config(config, project_config.database)
        
        # 保存数据路径配置
        self._save_data_path_config(config, project_config.data_path)
        
        # 保存提示词配置
        self._save_prompt_config(config, project_config.prompt)
        
        # 保存日志配置
        self._save_logging_config(config, project_config.logging)
        
        # 保存可视化配置
        self._save_visualizer_config(config, project_config.visualizer)
        
        # 保存模型配置
        self._save_model_config(config, project_config.model)
        
        # 写入文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            config.write(f)

    def _load_llm_config(self) -> ProjectLLMConfig:
        """加载LLM配置"""
        llm_config = ProjectLLMConfig()
        # 项目配置中暂无特殊LLM配置
        return llm_config

    def _save_llm_config(self, config: configparser.ConfigParser, llm_config: ProjectLLMConfig):
        """保存LLM配置"""
        # 项目配置中暂无特殊LLM配置

    def _load_database_config(self) -> ProjectDatabaseConfig:
        """加载数据库配置"""
        db_config = ProjectDatabaseConfig()
        if self.config.has_section('Database'):
            db = self.config['Database']
            db_config.config_name = db.get('config_name', db_config.config_name)
            
        return db_config

    def _save_database_config(self, config: configparser.ConfigParser, db_config: ProjectDatabaseConfig):
        """保存数据库配置"""
        config.add_section('Database')
        config['Database']['config_name'] = db_config.config_name
        

    def _load_data_path_config(self) -> ProjectDataPathConfig:
        """加载数据路径配置"""
        data_path_config = ProjectDataPathConfig()
        if self.config.has_section('Data'):
            data = self.config['Data']
            data_path_config.config_name = data.get('config_name', data_path_config.config_name)
            data_path_config.source_dir = data.get('source_dir', data_path_config.source_dir)
            data_path_config.output_dir = data.get('output_dir', data_path_config.output_dir)
        return data_path_config

    def _save_data_path_config(self, config: configparser.ConfigParser, data_path_config: ProjectDataPathConfig):
        """保存数据路径配置"""
        config.add_section('Data')
        config['Data']['config_name'] = data_path_config.config_name
        if data_path_config.source_dir:
            config['Data']['source_dir'] = data_path_config.source_dir
        if data_path_config.output_dir:
            config['Data']['output_dir'] = data_path_config.output_dir

    def _load_prompt_config(self) -> ProjectPromptConfig:
        """加载提示词配置"""
        prompt_config = ProjectPromptConfig()
        if self.config.has_section('Prompt'):
            prompt = self.config['Prompt']
            prompt_config.config_name = prompt.get('config_name', prompt_config.config_name)
        return prompt_config

    def _save_prompt_config(self, config: configparser.ConfigParser, prompt_config: ProjectPromptConfig):
        """保存提示词配置"""
        config.add_section('Prompt')
        config['Prompt']['config_name'] = prompt_config.config_name

    def _load_logging_config(self) -> ProjectLoggingConfig:
        """加载日志配置"""
        logging_config = ProjectLoggingConfig()
        # 项目配置中暂无特殊日志配置
        return logging_config

    def _save_logging_config(self, config: configparser.ConfigParser, logging_config: ProjectLoggingConfig):
        """保存日志配置"""
        # 项目配置中暂无特殊日志配置

    def _load_visualizer_config(self) -> ProjectVisualizerConfig:
        """加载可视化配置"""
        visualizer_config = ProjectVisualizerConfig()
        # 项目配置中暂无特殊可视化配置
        return visualizer_config

    def _save_visualizer_config(self, config: configparser.ConfigParser, visualizer_config: ProjectVisualizerConfig):
        """保存可视化配置"""
        # 项目配置中暂无特殊可视化配置

    def _load_model_config(self) -> ProjectModelConfig:
        """加载模型配置"""
        model_config = ProjectModelConfig()
        if self.config.has_section('Model'):
            model = self.config['Model']
            model_names_str = model.get('model_names', '')
            if model_names_str:
                model_config.model_names = [name.strip() for name in model_names_str.split(',') if name.strip()]
        return model_config

    def _save_model_config(self, config: configparser.ConfigParser, model_config: ProjectModelConfig):
        """保存模型配置"""
        config.add_section('Model')
        config['Model']['model_names'] = ','.join(model_config.model_names)
