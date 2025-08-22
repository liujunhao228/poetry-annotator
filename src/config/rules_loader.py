"""
规则配置处理器，处理校验、预处理、清洗等规则文件的加载（支持数组定义多个文件）。
"""

from typing import List, Dict, Any


class RulesLoader:
    """规则配置处理器"""
    
    def __init__(self, config_metadata: Dict[str, Any]):
        self.config_metadata = config_metadata

    def _get_validation_rules_files(self) -> List[str]:
        """获取校验规则文件列表（支持数组定义多个文件）"""
        # 首先从配置元数据获取文件路径
        validation_rules_config = self.config_metadata.get("validation_rules", {})
        
        # 获取全局规则文件
        global_file = validation_rules_config.get("global_file")
        files = [global_file] if global_file else []
        
        # 获取项目规则文件（支持数组）
        project_files = validation_rules_config.get("project_files", [])
        if isinstance(project_files, str):
            # 兼容旧的单字符串格式
            files.append(project_files)
        elif isinstance(project_files, list):
            # 新的数组格式
            files.extend(project_files)
            
        return files

    def _get_preprocessing_rules_files(self) -> List[str]:
        """获取预处理规则文件列表（支持数组定义多个文件）"""
        # 首先从配置元数据获取文件路径
        preprocessing_rules_config = self.config_metadata.get("preprocessing_rules", {})
        
        # 获取全局规则文件
        global_file = preprocessing_rules_config.get("global_file")
        files = [global_file] if global_file else []
        
        # 获取项目规则文件（支持数组）
        project_files = preprocessing_rules_config.get("project_files", [])
        if isinstance(project_files, str):
            # 兼容旧的单字符串格式
            files.append(project_files)
        elif isinstance(project_files, list):
            # 新的数组格式
            files.extend(project_files)
            
        return files

    def _get_cleaning_rules_files(self) -> List[str]:
        """获取清洗规则文件列表（支持数组定义多个文件）"""
        # 首先从配置元数据获取文件路径
        cleaning_rules_config = self.config_metadata.get("cleaning_rules", {})
        
        # 获取全局规则文件
        global_file = cleaning_rules_config.get("global_file")
        files = [global_file] if global_file else []
        
        # 获取项目规则文件（支持数组）
        project_files = cleaning_rules_config.get("project_files", [])
        if isinstance(project_files, str):
            # 兼容旧的单字符串格式
            files.append(project_files)
        elif isinstance(project_files, list):
            # 新的数组格式
            files.extend(project_files)
            
        return files