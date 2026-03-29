"""统一配置管理器 - 集中管理所有 GUI 配置"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, field

from .config import DistributionConfig, SamplingConfig, RecoveryConfig


@dataclass
class WindowState:
    """窗口状态配置"""
    width: int = 850
    height: int = 700
    active_tab: int = 0


@dataclass
class GUIConfig:
    """
    统一 GUI 配置 - 包含所有选项卡和窗口状态
    
    单文件管理所有配置，避免分散的 JSON 文件
    """
    distribution: DistributionConfig = field(default_factory=DistributionConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)
    window: WindowState = field(default_factory=WindowState)
    
    def save(self, path: Path) -> bool:
        """保存配置到文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'distribution': asdict(self.distribution),
                'sampling': asdict(self.sampling),
                'recovery': asdict(self.recovery),
                'window': asdict(self.window),
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False
    
    @classmethod
    def load(cls, path: Path) -> 'GUIConfig':
        """从文件加载配置"""
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = cls()
            
            # 加载各部分配置
            if 'distribution' in data:
                config.distribution = cls._load_section(
                    DistributionConfig, data['distribution']
                )
            
            if 'sampling' in data:
                config.sampling = cls._load_section(
                    SamplingConfig, data['sampling']
                )
            
            if 'recovery' in data:
                config.recovery = cls._load_section(
                    RecoveryConfig, data['recovery']
                )
            
            if 'window' in data:
                config.window = cls._load_section(
                    WindowState, data['window']
                )
            
            return config
        except Exception as e:
            print(f"警告：加载配置失败，使用默认值：{e}")
            return cls()
    
    @staticmethod
    def _load_section(config_class: type, data: dict) -> Any:
        """加载配置段落，过滤未知字段"""
        field_names = set(config_class.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in field_names}
        return config_class(**filtered)


class UnifiedConfigManager:
    """
    统一配置管理器
    
    职责:
    1. 管理单一配置文件 (config/gui_config.json)
    2. 提供各功能模块的配置访问
    3. 自动保存/加载
    4. 线程安全的配置访问
    """
    
    _default_config_path = Path('config/gui_config.json')
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认使用 config/gui_config.json
        """
        self._config_path = config_path or self._default_config_path
        self._config: Optional[GUIConfig] = None
        self._load()
    
    @property
    def config(self) -> GUIConfig:
        """获取配置对象"""
        if self._config is None:
            self._load()
        return self._config
    
    @property
    def distribution(self) -> DistributionConfig:
        """获取任务分发配置"""
        return self.config.distribution
    
    @property
    def sampling(self) -> SamplingConfig:
        """获取随机抽样配置"""
        return self.config.sampling
    
    @property
    def recovery(self) -> RecoveryConfig:
        """获取日志恢复配置"""
        return self.config.recovery
    
    @property
    def window(self) -> WindowState:
        """获取窗口状态配置"""
        return self.config.window
    
    def _load(self) -> None:
        """加载配置"""
        self._config = GUIConfig.load(self._config_path)
    
    def save(self) -> bool:
        """保存配置"""
        if self._config is None:
            return False
        return self._config.save(self._config_path)
    
    def get_section(self, section: str) -> Any:
        """
        获取指定段落配置
        
        Args:
            section: 段落名称 ('distribution', 'sampling', 'recovery', 'window')
        
        Returns:
            对应段落的配置对象
        """
        if section == 'distribution':
            return self.distribution
        elif section == 'sampling':
            return self.sampling
        elif section == 'recovery':
            return self.recovery
        elif section == 'window':
            return self.window
        else:
            raise ValueError(f"未知配置段落：{section}")
    
    def update_section(self, section: str, updates: Dict[str, Any]) -> None:
        """
        更新指定段落的配置
        
        Args:
            section: 段落名称
            updates: 要更新的字段字典
        """
        config_section = self.get_section(section)
        for key, value in updates.items():
            if hasattr(config_section, key):
                setattr(config_section, key, value)
    
    def apply_window_state(self, window: Any) -> None:
        """
        应用窗口状态到实际窗口
        
        Args:
            window: Tk 窗口实例
        """
        window.geometry(f"{self.window.width}x{self.window.height}")
    
    def save_window_state(self, window: Any) -> None:
        """
        保存当前窗口状态
        
        Args:
            window: Tk 窗口实例
        """
        # 获取当前窗口尺寸
        self.window.width = window.winfo_width()
        self.window.height = window.winfo_height()
        
        # 获取当前激活的选项卡
        for child in window.winfo_children():
            if hasattr(child, 'index') and hasattr(child, 'tab'):
                # 假设是 Notebook
                try:
                    self.window.active_tab = child.index('current')
                except Exception:
                    pass
        
        self.save()
