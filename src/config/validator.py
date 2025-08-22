"""
配置验证器，处理配置的验证逻辑。
"""

import configparser
import os
from typing import Dict, Any


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, global_config_path: str):
        self.global_config_path = global_config_path

    def validate_config(self, project_config_path: str = None) -> bool:
        """验证配置的完整性"""
        try:
            # 检查必要的全局配置
            if not os.path.exists(self.global_config_path):
                print(f"错误: 全局配置文件不存在: {self.global_config_path}")
                return False

            global_config = configparser.ConfigParser(interpolation=None)
            global_config.read(self.global_config_path, encoding='utf-8')

            required_sections = ['LLM', 'Database', 'Data', 'Categories', 'Prompt']
            for section in required_sections:
                if not global_config.has_section(section):
                    print(f"警告: 全局配置缺少节 [{section}]")
                    return False

            # 检查LLM配置
            # llm_config = self.get_llm_config()  # 这里需要传入GlobalConfig对象

            # 检查数据库配置
            db_config = self._get_global_database_config()
            if not db_config:
                print("错误: 未设置全局数据库路径 (db_path 或 db_paths)")
                return False

            # 检查数据路径配置
            data_config = self._get_global_data_config()
            if not data_config.get('source_dir') or not data_config.get('output_dir'):
                print("错误: 未设置全局数据路径")
                return False

            # 如果有项目配置，也进行检查
            if project_config_path:
                if not os.path.exists(project_config_path):
                    print(f"警告: 项目配置文件不存在: {project_config_path}")
                    # 不强制要求项目配置文件存在
                else:
                    project_config = configparser.ConfigParser(interpolation=None)
                    project_config.read(project_config_path, encoding='utf-8')

                    # 可以添加项目配置的验证逻辑

            return True

        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
            
    def _get_global_database_config(self) -> Dict[str, Any]:
        """获取全局数据库配置（默认），支持主数据库和分离数据库"""
        # 这里需要从全局配置文件中读取实际的路径
        if not os.path.exists(self.global_config_path):
            return {}

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        if not config.has_section('Database'):
            return {}

        result = {}

        # 尝试获取新的多数据库配置
        db_paths_str = config.get('Database', 'db_paths', fallback=None)
        if db_paths_str:
            # 解析 "name1=path1,name2=path2" 格式
            db_paths = {}
            for item in db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    db_paths[name.strip()] = path.strip()
            result['db_paths'] = db_paths

        # 尝试获取分离数据库配置
        separate_db_paths_str = config.get('Database', 'separate_db_paths', fallback=None)
        if separate_db_paths_str:
            # 解析 "name1=path1,name2=path2" 格式
            separate_db_paths = {}
            for item in separate_db_paths_str.split(','):
                if '=' in item:
                    name, path = item.split('=', 1)
                    separate_db_paths[name.strip()] = path.strip()
            result['separate_db_paths'] = separate_db_paths

        # 回退到旧的单数据库配置
        if not result.get('db_paths'):
            db_path = config.get('Database', 'db_path', fallback=None)
            if db_path:
                result['db_path'] = db_path

        return result

    def _get_global_data_config(self) -> Dict[str, str]:
        """获取全局数据路径配置（默认）"""
        if not os.path.exists(self.global_config_path):
            return {}

        config = configparser.ConfigParser(interpolation=None)
        config.read(self.global_config_path, encoding='utf-8')

        if not config.has_section('Data'):
            return {}

        return {
            'source_dir': config.get('Data', 'source_dir', fallback=None),
            'output_dir': config.get('Data', 'output_dir', fallback=None)
        }