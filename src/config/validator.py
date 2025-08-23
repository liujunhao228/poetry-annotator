"""
配置验证器，用于验证配置的完整性。
"""

import os
import configparser
from typing import Dict, Any, List, Optional


class ConfigValidator:
    """配置验证器"""

    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path

    def validate_config(self, project_config_path: Optional[str] = None) -> bool:
        """
        验证配置的完整性
        
        Args:
            project_config_path: 项目配置文件路径（可选）
            
        Returns:
            配置是否有效
        """
        # 验证全局配置
        if not self._validate_global_config():
            return False
        
        # 如果提供了项目配置路径，验证项目配置
        if project_config_path and not self._validate_project_config(project_config_path):
            return False
        
        return True

    def _validate_global_config(self) -> bool:
        """验证全局配置"""
        if not os.path.exists(self.global_config_path):
            print(f"错误: 全局配置文件不存在: {self.global_config_path}")
            return False
        
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(self.global_config_path, encoding='utf-8')
        except Exception as e:
            print(f"错误: 读取全局配置文件失败: {e}")
            return False
        
        # 验证必需的节
        required_sections = ['LLM', 'Database', 'Data', 'Prompt', 'Logging', 'Visualizer']
        for section in required_sections:
            if not config.has_section(section):
                print(f"错误: 全局配置文件缺少必需的节: [{section}]")
                return False
        
        # 验证必需的字段
        # LLM节
        llm = config['LLM']
        required_llm_fields = ['max_workers', 'max_model_pipelines', 'max_retries', 'retry_delay', 
                              'breaker_fail_max', 'breaker_reset_timeout', 'save_full_response']
        for field in required_llm_fields:
            if not llm.get(field):
                print(f"错误: 全局配置文件LLM节缺少必需的字段: {field}")
                return False
        
        # Database节
        # Database节没有必需字段
        
        # Data节
        data = config['Data']
        required_data_fields = ['source_dir', 'output_dir']
        for field in required_data_fields:
            if not data.get(field):
                print(f"错误: 全局配置文件Data节缺少必需的字段: {field}")
                return False
        
        # Prompt节
        # 不再需要模板文件路径
        pass
        
        # Logging节
        log = config['Logging']
        required_log_fields = ['console_log_level', 'file_log_level', 'enable_file_log', 
                              'enable_console_log', 'max_file_size', 'backup_count', 'quiet_third_party']
        for field in required_log_fields:
            if not log.get(field):
                print(f"错误: 全局配置文件Logging节缺少必需的字段: {field}")
                return False
        
        # Visualizer节
        viz = config['Visualizer']
        required_viz_fields = ['enable_custom_download']
        for field in required_viz_fields:
            if not viz.get(field):
                print(f"错误: 全局配置文件Visualizer节缺少必需的字段: {field}")
                return False
        
        return True

    def _validate_project_config(self, project_config_path: str) -> bool:
        """验证项目配置"""
        if not os.path.exists(project_config_path):
            print(f"错误: 项目配置文件不存在: {project_config_path}")
            return False
        
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(project_config_path, encoding='utf-8')
        except Exception as e:
            print(f"错误: 读取项目配置文件失败: {e}")
            return False
        
        # 验证必需的节
        required_sections = ['Database', 'Data', 'Prompt', 'Model', 'Validation', 'Preprocessing', 'Cleaning']
        for section in required_sections:
            if not config.has_section(section):
                print(f"错误: 项目配置文件缺少必需的节: [{section}]")
                return False
        
        # 验证必需的字段
        # Database节
        db = config['Database']
        if not (db.get('config_name') or db.get('db_paths') or db.get('db_path')):
            print("错误: 项目配置文件Database节必须指定config_name、db_paths或db_path之一")
            return False
        
        # Data节
        data = config['Data']
        if not (data.get('config_name') or (data.get('source_dir') and data.get('output_dir'))):
            print("错误: 项目配置文件Data节必须指定config_name或source_dir和output_dir")
            return False
        
        # Prompt节
        # 不再需要模板文件路径
        pass
        
        # Model节
        model = config['Model']
        if not model.get('model_names'):
            print("错误: 项目配置文件Model节缺少必需的字段: model_names")
            return False
        
        # Validation节
        validation = config['Validation']
        if not validation.get('ruleset_name'):
            print("错误: 项目配置文件Validation节缺少必需的字段: ruleset_name")
            return False
        
        # Preprocessing节
        preprocessing = config['Preprocessing']
        if not preprocessing.get('ruleset_name'):
            print("错误: 项目配置文件Preprocessing节缺少必需的字段: ruleset_name")
            return False
        
        # Cleaning节
        cleaning = config['Cleaning']
        if not cleaning.get('ruleset_name'):
            print("错误: 项目配置文件Cleaning节缺少必需的字段: ruleset_name")
            return False
        
        return True