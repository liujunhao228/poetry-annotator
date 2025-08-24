"""
规则加载器，用于加载和管理校验、预处理和清洗规则。
"""

import os
import yaml
from typing import Dict, Any, List, Optional


class RulesLoader:
    """规则加载器"""

    def __init__(self):
        pass

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
        global_validation_file = "config/global/global_validation_rules.yaml"
        if os.path.exists(global_validation_file):
            with open(global_validation_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的校验规则
        if project_name:
            project_validation_files = [
                f"config/project/{project_name}/project_validation_rules.yaml",
                f"config/project/{project_name}/custom_validation_rules.yaml"
            ]
            for file_path in project_validation_files:
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
        global_preprocessing_file = "config/global/global_preprocessing_rules.yaml"
        if os.path.exists(global_preprocessing_file):
            with open(global_preprocessing_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的预处理规则
        if project_name:
            project_preprocessing_files = [
                f"config/project/{project_name}/project_preprocessing_rules.yaml"
            ]
            for file_path in project_preprocessing_files:
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
        global_cleaning_file = "config/global/global_cleaning_rules.yaml"
        if os.path.exists(global_cleaning_file):
            with open(global_cleaning_file, 'r', encoding='utf-8') as f:
                rules.update(yaml.safe_load(f) or {})
        
        # 如果提供了项目名称，加载项目特定的清洗规则
        if project_name:
            project_cleaning_files = [
                f"config/project/{project_name}/project_cleaning_rules.yaml"
            ]
            for file_path in project_cleaning_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rules.update(yaml.safe_load(f) or {})
        
        return rules

    def get_validation_rules_files(self) -> List[str]:
        """获取校验规则文件列表"""
        return [
            "config/global/global_validation_rules.yaml",
            "config/project/project_validation_rules.yaml"
        ]

    def get_preprocessing_rules_files(self) -> List[str]:
        """获取预处理规则文件列表"""
        return [
            "config/global/global_preprocessing_rules.yaml",
            "config/project/project_preprocessing_rules.yaml"
        ]

    def get_cleaning_rules_files(self) -> List[str]:
        """获取清洗规则文件列表"""
        return [
            "config/global/global_cleaning_rules.yaml",
            "config/project/project_cleaning_rules.yaml"
        ]