import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigManager:
    """配置管理器，负责加载和管理配置文件"""
    
    def __init__(self, config_path: str = "config/config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        self.config.read(self.config_path, encoding='utf-8')
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM相关配置"""
        return {
            'max_workers': self.config.getint('LLM', 'max_workers'),
            'max_retries': self.config.getint('LLM', 'max_retries'),
            'retry_delay': self.config.getint('LLM', 'retry_delay')
        }
    
    def get_model_config(self, config_name: str) -> Dict[str, Any]:
        """
        获取指定模型配置别名的详细配置

        Args:
            config_name: 模型配置的别名 (例如 'gpt-4o')

        Returns:
            包含该模型所有配置项的字典
        """
        section_name = f"Model.{config_name}"
        if not self.config.has_section(section_name):
            raise ValueError(f"未在配置文件中找到模型配置节: [{section_name}]")
        
        return dict(self.config.items(section_name))

    def list_model_configs(self) -> List[str]:
        """
        列出所有已定义的模型配置别名

        Returns:
            一个包含所有模型别名的列表
        """
        prefix = "Model."
        configs = []
        for section in self.config.sections():
            if section.startswith(prefix):
                configs.append(section[len(prefix):])
        return sorted(configs)
        
    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        return {
            'db_path': self.config.get('Database', 'db_path')
        }
    
    def get_data_config(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return {
            'source_dir': self.config.get('Data', 'source_dir'),
            'output_dir': self.config.get('Data', 'output_dir')
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            'log_level': self.config.get('Logging', 'log_level', fallback='INFO'),
            'enable_file_log': self.config.getboolean('Logging', 'enable_file_log', fallback=True),
            'log_file': self.config.get('Logging', 'log_file', fallback=None),
            'enable_console_log': self.config.getboolean('Logging', 'enable_console_log', fallback=True),
            'max_file_size': self.config.getint('Logging', 'max_file_size', fallback=10),
            'backup_count': self.config.getint('Logging', 'backup_count', fallback=5),
            'quiet_third_party': self.config.getboolean('Logging', 'quiet_third_party', fallback=True)
        }
    
    
    def get_categories_config(self) -> Dict[str, str]:
        """获取情感分类配置"""
        return {
            'xml_path': self.config.get('Categories', 'xml_path'),
            'md_path': self.config.get('Categories', 'md_path', fallback='config/中国古典诗词情感分类体系.md')
        }
    
    def get_prompt_config(self) -> Dict[str, str]:
        """获取提示词配置"""
        return {
            'template_path': self.config.get('Prompt', 'template_path'),
            'system_prompt_template': self.config.get('Prompt', 'system_prompt_template', fallback='config/system_prompt_template.txt'),
            'user_prompt_template': self.config.get('Prompt', 'user_prompt_template', fallback='config/user_prompt_template.txt')
        }
    
    def get_model_prompt_config(self, model_name: str) -> Dict[str, str]:
        """
        获取指定模型的提示词模板配置
        
        Args:
            model_name: 模型配置别名
            
        Returns:
            包含模型特定提示词模板配置的字典
        """
        # 获取全局默认配置
        global_config = self.get_prompt_config()
        
        # 获取模型特定配置
        model_config = self.get_model_config(model_name)
        
        # 合并配置，模型特定配置优先
        prompt_config = {
            'template_path': model_config.get('template_path', global_config['template_path']),
            'system_prompt_template': model_config.get('system_prompt_template', global_config['system_prompt_template']),
            'user_prompt_template': model_config.get('user_prompt_template', global_config['user_prompt_template'])
        }
        
        return prompt_config
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        all_configs = {
            'llm': self.get_llm_config(),
            'database': self.get_database_config(),
            'data': self.get_data_config(),
            'categories': self.get_categories_config(),
            'prompt': self.get_prompt_config(),
            'models': {}
        }
        for name in self.list_model_configs():
            all_configs['models'][name] = self.get_model_config(name)
        return all_configs
    
    def validate_config(self) -> bool:
        """验证配置的完整性"""
        try:
            # 检查必要的配置节
            required_sections = ['LLM', 'Database', 'Data', 'Categories', 'Prompt']
            for section in required_sections:
                if not self.config.has_section(section):
                    print(f"警告: 缺少配置节 [{section}]")
                    return False
            
            # 检查LLM配置
            llm_config = self.get_llm_config()

            # 检查数据库配置
            db_config = self.get_database_config()
            if not db_config['db_path']:
                print("错误: 未设置数据库路径")
                return False
            
            # 检查数据路径配置
            data_config = self.get_data_config()
            if not data_config['source_dir'] or not data_config['output_dir']:
                print("错误: 未设置数据路径")
                return False
            
            return True
            
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

# 全局配置实例
config_manager = ConfigManager() 