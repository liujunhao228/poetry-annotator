"""
规则加载器，用于加载和管理校验、预处理和清洗规则。
"""

import os
import yaml
from typing import Dict, Any, List, Optional


class RulesLoader:
    """规则加载器"""

    def __init__(self, config_metadata: Dict[str, Any]):
        self.config_metadata = config_metadata

    def load_validation_rules(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载校验规则
        
        Args:
            project_name: 项目名称，如果提供则加载项目特定的规则
            
        Returns:
            校验规则字典
        """
        rules = {}
        
        # 加载全局校验规则
        global_validation_file = self.config_metadata.get('validation_rules', {}).get('global_file')
        if global_validation_file and os.path.exists(global_validation_file):
            with open(global_validation_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的校验规则
        if project_name:
            project_validation_files = self.config_metadata.get('validation_rules', {}).get('project_files', [])
            for file_pattern in project_validation_files:
                file_path = file_pattern.format(project_name=project_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rules.update(yaml.safe_load(f) or {})
        
        return rules

    def load_preprocessing_rules(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载预处理规则
        
        Args:
            project_name: 项目名称，如果提供则加载项目特定的规则
            
        Returns:
            预处理规则字典
        """
        rules = {}
        
        # 加载全局预处理规则
        global_preprocessing_file = self.config_metadata.get('preprocessing_rules', {}).get('global_file')
        if global_preprocessing_file and os.path.exists(global_preprocessing_file):
            with open(global_preprocessing_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的预处理规则
        if project_name:
            project_preprocessing_files = self.config_metadata.get('preprocessing_rules', {}).get('project_files', [])
            for file_pattern in project_preprocessing_files:
                file_path = file_pattern.format(project_name=project_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rules.update(yaml.safe_load(f) or {})
        
        return rules

    def load_cleaning_rules(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载清洗规则
        
        Args:
            project_name: 项目名称，如果提供则加载项目特定的规则
            
        Returns:
            清洗规则字典
        """
        rules = {}
        
        # 加载全局清洗规则
        global_cleaning_file = self.config_metadata.get('cleaning_rules', {}).get('global_file')
        if global_cleaning_file and os.path.exists(global_cleaning_file):
            with open(global_cleaning_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的清洗规则
        if project_name:
            project_cleaning_files = self.config_metadata.get('cleaning_rules', {}).get('project_files', [])
            for file_pattern in project_cleaning_files:
                file_path = file_pattern.format(project_name=project_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rules.update(yaml.safe_load(f) or {})
        
        return rules