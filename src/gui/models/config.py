"""GUI 配置数据模型"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json


@dataclass
class DistributionConfig:
    """任务分发功能配置"""
    
    console_log_level: str = "INFO"
    file_log_level: str = "DEBUG"
    model_choice: str = "single"  # "single" 或 "all"
    selected_model: str = ""
    id_source: str = "file"  # "file" 或 "dir"
    id_file_path: str = ""
    id_dir_path: str = ""
    force_rerun: bool = False
    fresh_start: bool = False
    chunk_size: int = 1000
    enable_file_log: bool = True
    db_choice: str = "select"
    selected_db: str = ""
    
    def save(self, path: Path) -> bool:
        """保存配置到文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False
    
    @classmethod
    def load(cls, path: Path) -> 'DistributionConfig':
        """从文件加载配置"""
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 过滤未知字段
            field_names = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)
        except Exception as e:
            print(f"警告：加载配置失败，使用默认值：{e}")
            return cls()


@dataclass
class SamplingConfig:
    """随机抽样功能配置"""
    
    sample_count: int = 100
    filter_missing: bool = False
    exclude_annotated: bool = False
    model_identifier: str = ""
    sort_mode: str = "shuffle"  # "shuffle", "sort", "no-shuffle"
    output_mode: str = "dir"  # "dir" 或 "file"
    output_dir: str = ""
    output_file: str = ""
    num_files: int = 1
    db_choice: str = "select"
    selected_db: str = ""
    
    def save(self, path: Path) -> bool:
        """保存配置到文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False
    
    @classmethod
    def load(cls, path: Path) -> 'SamplingConfig':
        """从文件加载配置"""
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            field_names = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)
        except Exception as e:
            print(f"警告：加载配置失败，使用默认值：{e}")
            return cls()


@dataclass
class RecoveryConfig:
    """日志恢复功能配置"""
    
    log_path: str = ""
    log_path_type: str = "file"  # "file" 或 "dir"
    db_path: str = ""
    dry_run: bool = True
    
    def save(self, path: Path) -> bool:
        """保存配置到文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False
    
    @classmethod
    def load(cls, path: Path) -> 'RecoveryConfig':
        """从文件加载配置"""
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            field_names = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)
        except Exception as e:
            print(f"警告：加载配置失败，使用默认值：{e}")
            return cls()


@dataclass
class GUIState:
    """GUI 整体状态（包含所有选项卡配置）"""
    
    distribution: DistributionConfig = field(default_factory=DistributionConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)
    
    def save(self, path: Path) -> bool:
        """保存整体状态到文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'distribution': asdict(self.distribution),
                'sampling': asdict(self.sampling),
                'recovery': asdict(self.recovery),
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"错误：保存状态失败：{e}")
            return False
    
    @classmethod
    def load(cls, path: Path) -> 'GUIState':
        """从文件加载整体状态"""
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = cls()
            
            if 'distribution' in data:
                state.distribution = DistributionConfig.load(path)
                # 手动加载 distribution 部分
                dist_fields = {f.name for f in DistributionConfig.__dataclass_fields__.values()}
                for k, v in data['distribution'].items():
                    if k in dist_fields:
                        setattr(state.distribution, k, v)
            
            if 'sampling' in data:
                state.sampling = SamplingConfig.load(path)
                samp_fields = {f.name for f in SamplingConfig.__dataclass_fields__.values()}
                for k, v in data['sampling'].items():
                    if k in samp_fields:
                        setattr(state.sampling, k, v)
            
            if 'recovery' in data:
                state.recovery = RecoveryConfig.load(path)
                rec_fields = {f.name for f in RecoveryConfig.__dataclass_fields__.values()}
                for k, v in data['recovery'].items():
                    if k in rec_fields:
                        setattr(state.recovery, k, v)
            
            return state
        except Exception as e:
            print(f"警告：加载状态失败，使用默认值：{e}")
            return cls()
