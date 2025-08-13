import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigManager:
    """配置管理器，负责加载、管理和保存配置文件"""
    
    def __init__(self, config_path: str = "config/config.ini"):
        # 确保目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        self.config_path = config_path
        self.config = configparser.ConfigParser(interpolation=None) # interpolation=None 防止 % 被解析
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            # 如果文件不存在，可以考虑创建一个默认的
            print(f"警告: 配置文件不存在: {self.config_path}。将使用一个空的配置。")
            self.config.read_string('') # 初始化一个空的ConfigParser
        else:
            self.config.read(self.config_path, encoding='utf-8')

    def save_config(self):
        """将当前配置写入文件"""
        with open(self.config_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def update_setting(self, section: str, option: str, value: Any):
        """
        更新一个配置项。如果节不存在，则创建它。
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def add_model_section(self, model_name: str, template: Optional[Dict[str, Any]] = None):
        """
        添加一个新的模型配置节。
        可以基于一个模板字典来创建。
        """
        section_name = f"Model.{model_name}"
        if self.config.has_section(section_name):
            raise ValueError(f"模型配置节 '{section_name}' 已存在。")
        self.config.add_section(section_name)
        if template:
            for key, value in template.items():
                self.config.set(section_name, key, str(value))
        else: # Add some default empty values
            defaults = {
                'provider': '', 'model_name': '', 'api_key': '', 'base_url': '',
                'temperature': '0.3', 'max_tokens': '1000', 'timeout': '30',
                'system_prompt_instruction_template': 'config/system_prompt_instruction.txt',
                'system_prompt_example_template': 'config/system_prompt_example.txt',
                'user_prompt_template': 'config/user_prompt_template.txt'
            }
            for key, value in defaults.items():
                 self.config.set(section_name, key, str(value))

    def remove_model_section(self, model_name: str):
        """删除一个模型配置节。"""
        section_name = f"Model.{model_name}"
        if not self.config.has_section(section_name):
            raise ValueError(f"未找到模型配置节: '{section_name}'")
        self.config.remove_section(section_name)

    def get_raw_items(self, section: str) -> List[tuple[str, str]]:
        """获取指定节下的所有原始键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM相关配置"""
        return {
            'max_workers': self.config.getint('LLM', 'max_workers'),
            'max_model_pipelines': self.config.getint('LLM', 'max_model_pipelines'),
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
        列出所有已定义的模型配置别名，顺序与配置文件中的顺序一致。

        Returns:
            一个包含所有模型别名的列表
        """
        prefix = "Model."
        configs = []
        for section in self.config.sections():
            if section.startswith(prefix):
                configs.append(section[len(prefix):])
        return configs
        
    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        # 尝试获取新的多数据库配置
        db_paths_str = self.config.get('Database', 'db_paths', fallback=None)
        if db_paths_str:
            # 解析 "name1=path1,name2=path2" 格式
            db_paths = {}
            for item in db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    db_paths[name.strip()] = path.strip()
            return {'db_paths': db_paths}
        
        # 回退到旧的单数据库配置
        db_path = self.config.get('Database', 'db_path', fallback=None)
        if db_path:
            return {'db_path': db_path}
        
        # 如果都没有配置，则返回空字典
        return {}
    
    def get_data_config(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return {
            'source_dir': self.config.get('Data', 'source_dir'),
            'output_dir': self.config.get('Data', 'output_dir')
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """[重构] 获取日志配置，支持分离的日志级别"""
        return {
            'console_log_level': self.config.get('Logging', 'console_log_level', fallback='INFO'),
            'file_log_level': self.config.get('Logging', 'file_log_level', fallback='DEBUG'),
            'enable_file_log': self.config.getboolean('Logging', 'enable_file_log', fallback=True),
            'log_file': self.config.get('Logging', 'log_file', fallback='logs/poetry_annotator.log'),
            'enable_console_log': self.config.getboolean('Logging', 'enable_console_log', fallback=True),
            'max_file_size': self.config.getint('Logging', 'max_file_size', fallback=10),
            'backup_count': self.config.getint('Logging', 'backup_count', fallback=5),
            'quiet_third_party': self.config.getboolean('Logging', 'quiet_third_party', fallback=True),
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
            'system_prompt_instruction_template': self.config.get('Prompt', 'system_prompt_instruction_template', fallback='config/system_prompt_instruction.txt'),
            'system_prompt_example_template': self.config.get('Prompt', 'system_prompt_example_template', fallback='config/system_prompt_example.txt'),
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
            'system_prompt_instruction_template': model_config.get('system_prompt_instruction_template', global_config['system_prompt_instruction_template']),
            'system_prompt_example_template': model_config.get('system_prompt_example_template', global_config['system_prompt_example_template']),
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

            # 检查数据库配置 - 支持新旧两种模式
            db_config = self.get_database_config()
            if not db_config:
                print("错误: 未设置数据库路径 (db_path 或 db_paths)")
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
try:
    # 假设config.ini在项目根目录下的config文件夹
    root_dir = os.path.dirname(os.path.abspath(__file__))
    # 如果src/config_manager.py，则根目录是 os.path.dirname(root_dir)
    if os.path.basename(root_dir) == 'src':
        root_dir = os.path.dirname(root_dir)
    config_path = os.path.join(root_dir, 'config', 'config.ini')
    config_manager = ConfigManager(config_path)
except Exception as e:
    # Fallback for unexpected structures
    print(f"无法定位config.ini, 尝试默认路径 'config/config.ini'. Error: {e}")
    config_manager = ConfigManager()
