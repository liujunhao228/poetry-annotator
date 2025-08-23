"""
项目配置管理器，用于管理当前激活的项目配置文件 (active_project.json)。
"""

import os
import json
from typing import Dict, Any, List, Optional

from src.config.config_metadata import load_config_metadata


class ProjectConfigManager:
    """项目配置管理器，用于管理当前激活的项目配置文件"""
    
    def __init__(self, config_file: Optional[str] = None, 
                 config_metadata_path: str = "config/metadata/config_metadata.json"):
        """初始化项目配置管理器"""
        # 读取配置元数据
        self.config_metadata_path = config_metadata_path
        self.config_metadata = load_config_metadata(config_metadata_path)
        
        # 确定项目配置管理器的配置文件路径
        if config_file is None:
            # 从 config_metadata.json 读取 active_project_config_file
            # 如果没有定义，则使用默认路径
            self.config_file = self.config_metadata.get(
                "active_project_config_file", 
                "config/system/active_project.json"
            )
        else:
            self.config_file = config_file
            
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载项目配置文件"""
        if not os.path.exists(self.config_file):
            # 创建默认配置
            default_config = {
                "active_project": "tangshi/project.ini",
                "available_projects": [
                    "default/project.ini",
                    "tangshi/project.ini",
                    "songci/project.ini"
                ]
            }
            self._save_config(default_config)
            return default_config
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_config(self, config: Dict[str, Any]):
        """保存项目配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_active_project(self) -> str:
        """获取当前激活的项目配置文件"""
        return self.config.get("active_project", "project.ini")
    
    def set_active_project(self, project_name: str):
        """设置当前激活的项目配置文件"""
        if project_name not in self.config.get("available_projects", []):
            raise ValueError(f"项目配置文件 '{project_name}' 不在可用项目列表中")
        
        self.config["active_project"] = project_name
        self._save_config(self.config)
    
    def get_available_projects(self) -> List[str]:
        """获取所有可用的项目配置文件"""
        return self.config.get("available_projects", [])
    
    def add_project(self, project_name: str):
        """添加新的项目配置文件到可用列表"""
        if "available_projects" not in self.config:
            self.config["available_projects"] = []
        
        if project_name not in self.config["available_projects"]:
            self.config["available_projects"].append(project_name)
            self._save_config(self.config)
    
    def remove_project(self, project_name: str):
        """从可用列表中移除项目配置文件"""
        if "available_projects" in self.config:
            if project_name in self.config["available_projects"]:
                self.config["available_projects"].remove(project_name)
                # 如果删除的是当前激活的项目，设置为默认项目
                if self.config.get("active_project") == project_name:
                    self.config["active_project"] = "project.ini"
                self._save_config(self.config)


# 创建全局项目配置管理器实例
project_config_manager = ProjectConfigManager()