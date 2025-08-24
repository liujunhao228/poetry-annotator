"""项目系统模块，负责协调插件、数据管理和标注流程

该模块现在使用新的组件系统来管理插件和组件。组件系统提供了更严格和明确的组件类型机制，
确保插件配置参数不会意外传递给插件构造函数。
"""

import os
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, Union
from src.config.plugin_loader import ProjectPluginConfigLoader # 导入新的加载器
from src.config.schema import GlobalPluginConfig, PluginConfig # 导入配置 Schema
from src.annotator import Annotator
from src.data import get_data_manager
from src.component_system import get_component_system, ComponentType

# 配置日志
logger = logging.getLogger(__name__)

class ProjectSystem:
    """项目系统，负责与插件系统交互并管理标注流程"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化项目系统，加载插件配置"""
        # self.config = config_manager # 可能不再需要，或用于其他目的
        self.project_root = project_root or Path(".") # 默认项目根目录
        # 使用新的组件系统
        self.component_system = get_component_system(self.project_root)
        
    @property
    def _plugin_configs(self):
        """为了向后兼容，提供对插件配置的访问"""
        return self.component_system._plugin_configs
        
    def get_component(self, component_type: str, **kwargs) -> Union[Annotator, object]:
        """
        工厂方法：根据插件配置获取组件实例。
        
        Args:
            component_type: 组件类型字符串 (例如 'annotator', 'data_manager')。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            组件实例（可能是插件实例，也可能是默认实例）。
        """
        # 委托给新的组件系统处理
        return self.component_system.get_component(component_type, **kwargs)
    
    def _get_default_component(self, component_type: str, **kwargs):
        """
        获取默认组件实例。
        
        Args:
            component_type: 组件类型。
            **kwargs: 传递给组件构造函数的参数。
            
        Returns:
            默认组件实例。
        """
        # 委托给新的组件系统处理
        try:
            comp_type = ComponentType.from_string(component_type)
            return self.component_system._get_default_component(comp_type, **kwargs)
        except ValueError:
            raise ValueError(f"未知的组件类型: {component_type}")

    # --- 任务执行方法 (待实现) ---
    async def run_annotation_task(self, 
                                  model_config_name: str,
                                  limit: Optional[int] = None,
                                  start_id: Optional[int] = None,
                                  end_id: Optional[int] = None,
                                  force_rerun: bool = False,
                                  poem_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        运行标注任务 (占位符)
        """
        # TODO: 实现具体的任务执行逻辑
        pass

# 全局项目系统实例
# 假设 main.py 会设置 project_root 或我们在这里获取它
# 为了简单起见，我们在这里也计算 project_root
import sys
from pathlib import Path

# 尝试从 sys.path 或 __file__ 推断项目根目录
# 这可能需要根据实际情况调整
def _infer_project_root():
    # 方法1: 假设 src 在项目根目录下
    try:
        current_file = Path(__file__).resolve()
        src_dir = current_file.parent
        project_root = src_dir.parent
        project_dir = project_root / "project"
        if project_dir.exists():
            return project_root
    except:
        pass
    
    # 方法2: 遍历 sys.path
    for p in sys.path:
        try:
            path_obj = Path(p).resolve()
            project_dir = path_obj / "project"
            if project_dir.exists():
                return path_obj
        except:
            pass
            
    # 默认
    return Path(".")

# 全局项目系统实例
project_system = ProjectSystem(project_root=_infer_project_root())