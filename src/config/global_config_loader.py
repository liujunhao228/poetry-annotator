"""
全局配置加载器
"""

import configparser
import os
from typing import Dict, Any, List, Optional
from src.config.schema import GlobalConfig, GlobalLLMConfig, GlobalDatabaseConfig, GlobalDataPathConfig, GlobalPromptConfig, GlobalLoggingConfig, GlobalVisualizerConfig, GlobalModelConfigTemplate, GlobalCategoriesConfig, GlobalPluginConfig, GlobalValidationRuleSet, GlobalPreprocessingRuleSet, GlobalCleaningRuleSet


class GlobalConfigLoader:
    """全局配置加载器"""

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

    def load(self) -> GlobalConfig:
        """加载并返回全局配置对象"""
        global_config = GlobalConfig()
        
        # 加载LLM配置
        global_config.llm = self._load_llm_config()
        
        # 加载数据库配置
        global_config.database = self._load_database_config()
        
        # 加载数据路径配置
        global_config.data_path = self._load_data_path_config()
        
        # 加载提示词配置
        global_config.prompt = self._load_prompt_config()
        
        # 加载日志配置
        global_config.logging = self._load_logging_config()
        
        # 加载可视化配置
        global_config.visualizer = self._load_visualizer_config()
        
        # 加载情感分类配置
        global_config.categories = self._load_categories_config()
        
        # 加载插件配置
        global_config.plugins = self._load_plugin_config()
        
        # 加载模型模板配置
        global_config.model_template = self._load_model_template_config()
        
        # 加载校验规则配置
        global_config.validation = self._load_validation_rule_config()
        
        # 加载预处理规则配置
        global_config.preprocessing = self._load_preprocessing_rule_config()
        
        # 加载清洗规则配置
        global_config.cleaning = self._load_cleaning_rule_config()
        
        return global_config

    def save(self, global_config: GlobalConfig):
        """将全局配置保存到文件"""
        # 确保配置文件所在的目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # 创建新的ConfigParser对象
        config = configparser.ConfigParser()
        
        # 保存LLM配置
        self._save_llm_config(config, global_config.llm)
        
        # 保存数据库配置
        self._save_database_config(config, global_config.database)
        
        # 保存数据路径配置
        self._save_data_path_config(config, global_config.data_path)
        
        # 保存提示词配置
        self._save_prompt_config(config, global_config.prompt)
        
        # 保存日志配置
        self._save_logging_config(config, global_config.logging)
        
        # 保存可视化配置
        self._save_visualizer_config(config, global_config.visualizer)
        
        # 保存情感分类配置
        self._save_categories_config(config, global_config.categories)
        
        # 保存插件配置
        self._save_plugin_config(config, global_config.plugins)
        
        # 保存模型模板配置
        self._save_model_template_config(config, global_config.model_template)
        
        # 保存校验规则配置
        self._save_validation_rule_config(config, global_config.validation)
        
        # 保存预处理规则配置
        self._save_preprocessing_rule_config(config, global_config.preprocessing)
        
        # 保存清洗规则配置
        self._save_cleaning_rule_config(config, global_config.cleaning)
        
        # 写入文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            config.write(f)

    def _load_llm_config(self) -> GlobalLLMConfig:
        """加载LLM配置"""
        llm_config = GlobalLLMConfig()
        if self.config.has_section('LLM'):
            llm = self.config['LLM']
            llm_config.max_workers = llm.getint('max_workers', llm_config.max_workers)
            llm_config.max_model_pipelines = llm.getint('max_model_pipelines', llm_config.max_model_pipelines)
            llm_config.max_retries = llm.getint('max_retries', llm_config.max_retries)
            llm_config.retry_delay = llm.getint('retry_delay', llm_config.retry_delay)
            llm_config.breaker_fail_max = llm.getint('breaker_fail_max', llm_config.breaker_fail_max)
            llm_config.breaker_reset_timeout = llm.getint('breaker_reset_timeout', llm_config.breaker_reset_timeout)
            llm_config.save_full_response = llm.getboolean('save_full_response', llm_config.save_full_response)
        return llm_config

    def _save_llm_config(self, config: configparser.ConfigParser, llm_config: GlobalLLMConfig):
        """保存LLM配置"""
        config.add_section('LLM')
        config['LLM']['max_workers'] = str(llm_config.max_workers)
        config['LLM']['max_model_pipelines'] = str(llm_config.max_model_pipelines)
        config['LLM']['max_retries'] = str(llm_config.max_retries)
        config['LLM']['retry_delay'] = str(llm_config.retry_delay)
        config['LLM']['breaker_fail_max'] = str(llm_config.breaker_fail_max)
        config['LLM']['breaker_reset_timeout'] = str(llm_config.breaker_reset_timeout)
        config['LLM']['save_full_response'] = str(llm_config.save_full_response).lower()

    def _load_database_config(self) -> GlobalDatabaseConfig:
        """加载数据库配置"""
        db_config = GlobalDatabaseConfig()
        if self.config.has_section('Database'):
            db = self.config['Database']
            # 分离数据库配置模板
            separate_db_paths_str = db.get('separate_db_paths')
            if separate_db_paths_str:
                separate_db_paths = {}
                for item in separate_db_paths_str.split(','):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        separate_db_paths[key.strip()] = value.strip()
                db_config.separate_db_template = separate_db_paths
        return db_config

    def _save_database_config(self, config: configparser.ConfigParser, db_config: GlobalDatabaseConfig):
        """保存数据库配置"""
        config.add_section('Database')
        if db_config.separate_db_template:
            separate_db_paths_str = ','.join([f"{k}={v}" for k, v in db_config.separate_db_template.items()])
            config['Database']['separate_db_paths'] = separate_db_paths_str

    def _load_data_path_config(self) -> GlobalDataPathConfig:
        """加载数据路径配置"""
        data_path_config = GlobalDataPathConfig()
        if self.config.has_section('Data'):
            data = self.config['Data']
            # 数据路径配置通常在项目配置中指定，这里只保留默认配置
            pass
        return data_path_config

    def _save_data_path_config(self, config: configparser.ConfigParser, data_path_config: GlobalDataPathConfig):
        """保存数据路径配置"""
        config.add_section('Data')

    def _load_prompt_config(self) -> GlobalPromptConfig:
        """加载提示词配置"""
        prompt_config = GlobalPromptConfig()
        if self.config.has_section('Prompt'):
            prompt = self.config['Prompt']
            # 提示词配置通常在项目配置中指定，这里只保留默认配置
            pass
        return prompt_config

    def _save_prompt_config(self, config: configparser.ConfigParser, prompt_config: GlobalPromptConfig):
        """保存提示词配置"""
        config.add_section('Prompt')

    def _load_logging_config(self) -> GlobalLoggingConfig:
        """加载日志配置"""
        logging_config = GlobalLoggingConfig()
        if self.config.has_section('Logging'):
            log = self.config['Logging']
            logging_config.console_log_level = log.get('console_log_level', logging_config.console_log_level)
            logging_config.file_log_level = log.get('file_log_level', logging_config.file_log_level)
            logging_config.enable_file_log = log.getboolean('enable_file_log', logging_config.enable_file_log)
            logging_config.log_file = log.get('log_file', logging_config.log_file)
            logging_config.enable_console_log = log.getboolean('enable_console_log', logging_config.enable_console_log)
            logging_config.max_file_size = log.getint('max_file_size', logging_config.max_file_size)
            logging_config.backup_count = log.getint('backup_count', logging_config.backup_count)
            logging_config.quiet_third_party = log.getboolean('quiet_third_party', logging_config.quiet_third_party)
        return logging_config

    def _save_logging_config(self, config: configparser.ConfigParser, logging_config: GlobalLoggingConfig):
        """保存日志配置"""
        config.add_section('Logging')
        config['Logging']['console_log_level'] = logging_config.console_log_level
        config['Logging']['file_log_level'] = logging_config.file_log_level
        config['Logging']['enable_file_log'] = str(logging_config.enable_file_log).lower()
        config['Logging']['log_file'] = logging_config.log_file
        config['Logging']['enable_console_log'] = str(logging_config.enable_console_log).lower()
        config['Logging']['max_file_size'] = str(logging_config.max_file_size)
        config['Logging']['backup_count'] = str(logging_config.backup_count)
        config['Logging']['quiet_third_party'] = str(logging_config.quiet_third_party).lower()

    def _load_visualizer_config(self) -> GlobalVisualizerConfig:
        """加载可视化配置"""
        visualizer_config = GlobalVisualizerConfig()
        if self.config.has_section('Visualizer'):
            viz = self.config['Visualizer']
            visualizer_config.enable_custom_download = viz.getboolean('enable_custom_download', visualizer_config.enable_custom_download)
        return visualizer_config

    def _save_visualizer_config(self, config: configparser.ConfigParser, visualizer_config: GlobalVisualizerConfig):
        """保存可视化配置"""
        config.add_section('Visualizer')
        config['Visualizer']['enable_custom_download'] = str(visualizer_config.enable_custom_download).lower()

    def _load_categories_config(self) -> GlobalCategoriesConfig:
        """加载情感分类配置"""
        categories_config = GlobalCategoriesConfig()
        if self.config.has_section('Categories'):
            categories = self.config['Categories']
            categories_config.xml_path = categories.get('xml_path', categories_config.xml_path)
            categories_config.md_path = categories.get('md_path', categories_config.md_path)
        return categories_config

    def _save_categories_config(self, config: configparser.ConfigParser, categories_config: GlobalCategoriesConfig):
        """保存情感分类配置"""
        if not config.has_section('Categories'):
            config.add_section('Categories')
        config['Categories']['xml_path'] = categories_config.xml_path
        config['Categories']['md_path'] = categories_config.md_path

    def _load_plugin_config(self) -> GlobalPluginConfig:
        """加载插件配置"""
        plugin_config = GlobalPluginConfig()
        if self.config.has_section('Plugins'):
            plugins = self.config['Plugins']
            enabled_plugins_str = plugins.get('enabled_plugins', '')
            if enabled_plugins_str:
                plugin_config.enabled_plugins = [name.strip() for name in enabled_plugins_str.split(',') if name.strip()]
            
            plugin_paths_str = plugins.get('plugin_paths', '')
            if plugin_paths_str:
                plugin_config.plugin_paths = [path.strip() for path in plugin_paths_str.split(',') if path.strip()]
        return plugin_config

    def _save_plugin_config(self, config: configparser.ConfigParser, plugin_config: GlobalPluginConfig):
        """保存插件配置"""
        if not config.has_section('Plugins'):
            config.add_section('Plugins')
        config['Plugins']['enabled_plugins'] = ','.join(plugin_config.enabled_plugins)
        config['Plugins']['plugin_paths'] = ','.join(plugin_config.plugin_paths)

    def _load_model_template_config(self) -> GlobalModelConfigTemplate:
        """加载模型模板配置"""
        model_template_config = GlobalModelConfigTemplate()
        # 模型模板配置通常在具体的模型配置节中定义，这里只保留默认配置
        return model_template_config

    def _save_model_template_config(self, config: configparser.ConfigParser, model_template_config: GlobalModelConfigTemplate):
        """保存模型模板配置"""
        # 模型模板配置通常在具体的模型配置节中定义，这里不需要保存

    def _load_validation_rule_config(self) -> GlobalValidationRuleSet:
        """加载校验规则配置"""
        validation_config = GlobalValidationRuleSet()
        # 校验规则配置通常在规则文件中定义，这里只保留默认配置
        return validation_config

    def _save_validation_rule_config(self, config: configparser.ConfigParser, validation_config: GlobalValidationRuleSet):
        """保存校验规则配置"""
        # 校验规则配置通常在规则文件中定义，这里不需要保存

    def _load_preprocessing_rule_config(self) -> GlobalPreprocessingRuleSet:
        """加载预处理规则配置"""
        preprocessing_config = GlobalPreprocessingRuleSet()
        # 预处理规则配置通常在规则文件中定义，这里只保留默认配置
        return preprocessing_config

    def _save_preprocessing_rule_config(self, config: configparser.ConfigParser, preprocessing_config: GlobalPreprocessingRuleSet):
        """保存预处理规则配置"""
        # 预处理规则配置通常在规则文件中定义，这里不需要保存

    def _load_cleaning_rule_config(self) -> GlobalCleaningRuleSet:
        """加载清洗规则配置"""
        cleaning_config = GlobalCleaningRuleSet()
        # 清洗规则配置通常在规则文件中定义，这里只保留默认配置
        return cleaning_config

    def _save_cleaning_rule_config(self, config: configparser.ConfigParser, cleaning_config: GlobalCleaningRuleSet):
        """保存清洗规则配置"""
        # 清洗规则配置通常在规则文件中定义，这里不需要保存

    def _get_global_database_config(self) -> Dict[str, Any]:
        """获取全局数据库配置"""
        config = {}
        if self.config.has_section('Database'):
            db = self.config['Database']
            # 分离数据库配置模板
            separate_db_paths_str = db.get('separate_db_paths')
            if separate_db_paths_str:
                separate_db_paths = {}
                for item in separate_db_paths_str.split(','):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        separate_db_paths[key.strip()] = value.strip()
                config['separate_db_template'] = separate_db_paths
        return config

    def _get_global_data_config(self) -> Dict[str, str]:
        """获取全局数据路径配置"""
        config = {}
        if self.config.has_section('Data'):
            data = self.config['Data']
            config['source_dir'] = data.get('source_dir', 'data/source_json')
            config['output_dir'] = data.get('output_dir', 'data/output')
        return config

    def _get_global_prompt_config(self) -> Dict[str, str]:
        """获取全局提示词配置"""
        # 不再使用模板文件，返回空配置
        return {}

    def _get_global_model_config(self, model_name: str) -> Dict[str, Any]:
        """获取全局模型配置"""
        section_name = f"Model.{model_name}"
        if not self.config.has_section(section_name):
            return {}
        
        model_config = dict(self.config[section_name])
        # 转换特定字段的类型
        if 'request_delay' in model_config:
            model_config['request_delay'] = float(model_config['request_delay'])
        if 'temperature' in model_config:
            model_config['temperature'] = float(model_config['temperature'])
        if 'max_tokens' in model_config:
            model_config['max_tokens'] = int(model_config['max_tokens'])
        if 'timeout' in model_config:
            model_config['timeout'] = int(model_config['timeout'])
        if 'enable_thinking' in model_config:
            model_config['enable_thinking'] = model_config['enable_thinking'].lower() == 'true'
        if 'stream' in model_config:
            model_config['stream'] = model_config['stream'].lower() == 'true'
            
        return model_config

    def _get_all_global_model_configs(self) -> List[Dict[str, Any]]:
        """获取所有全局模型配置"""
        model_configs = []
        for section_name in self.config.sections():
            if section_name.startswith('Model.'):
                model_name = section_name[len('Model.'):]
                model_config = self._get_global_model_config(model_name)
                model_config['name'] = model_name
                model_configs.append(model_config)
        return model_configs