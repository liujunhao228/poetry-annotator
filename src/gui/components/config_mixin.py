"""配置加载/保存混入类"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import asdict, dataclass, fields, is_dataclass


class ConfigMixin:
    """
    配置加载/保存混入类
    
    为 GUI 组件提供统一的配置持久化功能。
    支持 dataclass 配置对象的保存和加载。
    """
    
    config_file: Optional[Path] = None
    
    def save_config(self, config_obj: Any, config_file: Optional[Path] = None) -> bool:
        """
        保存配置到 JSON 文件
        
        Args:
            config_obj: 配置对象（dataclass 或 dict）
            config_file: 配置文件路径，如果为 None 则使用类的 config_file
            
        Returns:
            保存是否成功
        """
        file_path = config_file or self.config_file
        if not file_path:
            print("错误：未指定配置文件路径")
            return False
        
        try:
            # 转换为字典
            if is_dataclass(config_obj) and not isinstance(config_obj, type):
                config_dict = asdict(config_obj)
            elif isinstance(config_obj, dict):
                config_dict = config_obj
            else:
                # 尝试直接序列化
                config_dict = config_obj.__dict__ if hasattr(config_obj, '__dict__') else vars(config_obj)
            
            # 确保目录存在
            config_dir = file_path.parent
            if config_dir and not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为 JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            print(f"配置已保存到 {file_path}")
            return True
            
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False
    
    def load_config(self, config_class: type, config_file: Optional[Path] = None) -> Optional[Any]:
        """
        从 JSON 文件加载配置
        
        Args:
            config_class: 配置类（dataclass）
            config_file: 配置文件路径，如果为 None 则使用类的 config_file
            
        Returns:
            配置对象，加载失败返回 None
        """
        file_path = config_file or self.config_file
        if not file_path or not file_path.exists():
            print(f"未找到配置文件 {file_path}，将使用默认值")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # 如果是 dataclass，创建实例
            if is_dataclass(config_class) and isinstance(config_class, type):
                # 获取 dataclass 的字段
                field_names = {f.name for f in fields(config_class)}
                # 只传递 dataclass 中定义的字段
                filtered_dict = {k: v for k, v in config_dict.items() if k in field_names}
                return config_class(**filtered_dict)
            else:
                return config_class(**config_dict)
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"警告：加载配置失败，将使用默认值：{e}")
            return None
    
    def load_config_dict(
        self, 
        target_obj: Any, 
        config_dict: Dict[str, Any],
        ignore_unknown: bool = True
    ) -> None:
        """
        将配置字典应用到目标对象
        
        Args:
            target_obj: 目标对象（通常是 self）
            config_dict: 配置字典
            ignore_unknown: 是否忽略未知字段
        """
        for key, value in config_dict.items():
            # 检查目标对象是否有对应的属性
            if hasattr(target_obj, key):
                attr = getattr(target_obj, key)
                # 如果是 Variable 包装器，使用 set 方法
                if hasattr(attr, 'set'):
                    try:
                        attr.set(value)
                    except Exception:
                        pass
                else:
                    try:
                        setattr(target_obj, key, value)
                    except Exception:
                        pass
            elif not ignore_unknown:
                print(f"警告：未知配置项 '{key}'")
