"""
统一数据库配置管理模块
提供统一的数据库配置获取和管理功能
"""

import os
import sys
from typing import Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



def extract_project_name_from_output_dir(output_dir: str) -> str:
    """
    从 output_dir 中提取项目名称。
    例如：如果 output_dir 是 'data/SocialPoemAnalysis'，则项目名称为 'SocialPoemAnalysis'。
    """
    return Path(output_dir).name


def get_separate_database_paths(project_name: str) -> Dict[str, str]:
    """
    获取分离数据库路径配置，根据项目名称动态生成。
    
    Args:
        project_name: 当前项目的名称。
        
    Returns:
        Dict[str, str]: 分离数据库路径配置
    """
    base_data_dir = Path("data")
    project_data_dir = base_data_dir / project_name

    # 动态生成数据库路径
    resolved_paths = {
        'raw_data': str(project_data_dir / "raw_data.db"),
        'annotation': str(project_data_dir / "annotation.db"),
        'emotion': str(project_data_dir / "emotion.db")
    }
    
    # 确保所有路径都是绝对路径
    for name, path in resolved_paths.items():
        if not Path(path).is_absolute():
            resolved_paths[name] = str(Path(path).resolve())

    return resolved_paths


from pathlib import Path

def ensure_database_directory_exists(db_path: Path) -> None:
    """
    确保数据库目录存在
    
    Args:
        db_path: 数据库文件路径
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
