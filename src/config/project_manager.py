"""
项目配置管理器，用于管理项目配置。
"""

import os
from typing import List


class ProjectConfigManager:
    """项目配置管理器"""
    
    def __init__(self):
        """初始化项目配置管理器"""
        # 不再需要加载配置文件，直接使用默认值
        pass
    
    def get_active_project(self) -> str:
        """获取当前激活的项目配置文件"""
        # 直接返回默认项目配置文件名
        return "project.ini"
    
    def set_active_project(self, project_name: str):
        """设置当前激活的项目配置文件"""
        # 不再需要设置激活项目，直接忽略
        pass
    
    def get_available_projects(self) -> List[str]:
        """获取所有可用的项目配置文件"""
        # 返回默认的项目配置文件列表
        return ["project.ini"]
    
    def add_project(self, project_name: str):
        """添加新的项目配置文件到可用列表"""
        # 不再需要维护项目列表，直接忽略
        pass
    
    def remove_project(self, project_name: str):
        """从可用列表中移除项目配置文件"""
        # 不再需要维护项目列表，直接忽略
        pass