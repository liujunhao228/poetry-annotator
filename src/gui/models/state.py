"""响应式状态管理 - 观察者模式实现"""

from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field


class Observable:
    """
    可观察对象基类 - 观察者模式实现
    
    当状态改变时自动通知所有订阅者。
    
    使用示例:
        class CounterState(Observable):
            count: int = 0
            
            def increment(self):
                self.count += 1
                self.notify()
        
        state = CounterState()
        state.subscribe(lambda: print(f"Count: {state.count}"))
        state.increment()  # 自动打印 "Count: 1"
    """
    
    def __init__(self):
        self._observers: List[Callable[[], None]] = []
        self._conditional_observers: List[Callable[[str, Any], None]] = []
    
    def subscribe(self, callback: Callable[[], None]) -> None:
        """
        订阅状态变化
        
        Args:
            callback: 无参数的回调函数，当任何状态变化时调用
        """
        self._observers.append(callback)
    
    def subscribe_conditional(
        self,
        callback: Callable[[str, Any], None]
    ) -> None:
        """
        订阅特定字段的状态变化
        
        Args:
            callback: 接收 (字段名，新值) 的回调函数
        """
        self._conditional_observers.append(callback)
    
    def unsubscribe(self, callback: Callable[[], None]) -> None:
        """
        取消订阅
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def notify(self, field_name: Optional[str] = None, value: Any = None) -> None:
        """
        通知所有订阅者状态已变化
        
        Args:
            field_name: 变化的字段名（可选）
            value: 新值（可选）
        """
        # 通知通用订阅者
        for observer in self._observers:
            try:
                observer()
            except Exception as e:
                print(f"观察者回调失败：{e}")
        
        # 通知条件订阅者
        if field_name is not None:
            for observer in self._conditional_observers:
                try:
                    observer(field_name, value)
                except Exception as e:
                    print(f"条件观察者回调失败：{e}")
    
    def set_field(self, name: str, value: Any, notify: bool = True) -> None:
        """
        设置字段值并可选地通知订阅者
        
        Args:
            name: 字段名
            value: 新值
            notify: 是否通知订阅者
        """
        setattr(self, name, value)
        if notify:
            self.notify(name, value)


@dataclass
class TaskState(Observable):
    """
    任务状态 - 跟踪任务执行状态
    
    字段:
        is_running: 任务是否正在运行
        progress: 进度百分比 (0-100)
        status_message: 状态消息
        error_message: 错误消息（如果有）
    """
    is_running: bool = False
    progress: int = 0
    status_message: str = "空闲"
    error_message: str = ""
    
    def __post_init__(self):
        super().__init__()
    
    def start(self, message: str = "任务开始...") -> None:
        """标记任务开始"""
        self.is_running = True
        self.progress = 0
        self.status_message = message
        self.error_message = ""
        self.notify("is_running", True)
    
    def update_progress(self, progress: int, message: str = "") -> None:
        """
        更新任务进度
        
        Args:
            progress: 进度百分比
            message: 状态消息
        """
        self.progress = min(100, max(0, progress))
        if message:
            self.status_message = message
        self.notify("progress", self.progress)
    
    def complete(self, message: str = "任务完成") -> None:
        """标记任务完成"""
        self.is_running = False
        self.progress = 100
        self.status_message = message
        self.notify("is_running", False)
    
    def fail(self, error: str) -> None:
        """标记任务失败"""
        self.is_running = False
        self.error_message = error
        self.status_message = "任务失败"
        self.notify("is_running", False)


@dataclass
class DistributionTabState(Observable):
    """任务分发选项卡状态"""
    is_running: bool = False
    console_log_level: str = "INFO"
    file_log_level: str = "DEBUG"
    model_choice: str = "single"
    selected_model: str = ""
    id_source: str = "file"
    id_file_path: str = ""
    id_dir_path: str = ""
    force_rerun: bool = False
    fresh_start: bool = False
    chunk_size: int = 1000
    enable_file_log: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def update_from_config(self, config: Any) -> None:
        """从配置对象更新状态"""
        self.console_log_level = config.console_log_level
        self.file_log_level = config.file_log_level
        self.model_choice = config.model_choice
        self.selected_model = config.selected_model
        self.id_source = config.id_source
        self.id_file_path = config.id_file_path
        self.id_dir_path = config.id_dir_path
        self.force_rerun = config.force_rerun
        self.fresh_start = config.fresh_start
        self.chunk_size = config.chunk_size
        self.enable_file_log = config.enable_file_log
        self.notify()


@dataclass
class SamplingTabState(Observable):
    """随机抽样选项卡状态"""
    is_running: bool = False
    sample_count: int = 100
    filter_missing: bool = False
    exclude_annotated: bool = False
    model_identifier: str = ""
    sort_mode: str = "shuffle"
    output_mode: str = "dir"
    output_dir: str = ""
    output_file: str = ""
    num_files: int = 1
    
    def __post_init__(self):
        super().__init__()
    
    def update_from_config(self, config: Any) -> None:
        """从配置对象更新状态"""
        self.sample_count = config.sample_count
        self.filter_missing = config.filter_missing
        self.exclude_annotated = config.exclude_annotated
        self.model_identifier = config.model_identifier
        self.sort_mode = config.sort_mode
        self.output_mode = config.output_mode
        self.output_dir = config.output_dir
        self.output_file = config.output_file
        self.num_files = config.num_files
        self.notify()


@dataclass
class RecoveryTabState(Observable):
    """日志恢复选项卡状态"""
    is_running: bool = False
    log_path: str = ""
    log_path_type: str = "file"
    db_path: str = ""
    dry_run: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def update_from_config(self, config: Any) -> None:
        """从配置对象更新状态"""
        self.log_path = config.log_path
        self.log_path_type = config.log_path_type
        self.db_path = config.db_path
        self.dry_run = config.dry_run
        self.notify()


class StateManager:
    """
    状态管理器 - 管理所有选项卡的状态
    
    使用示例:
        state_manager = StateManager()
        dist_state = state_manager.get_distribution_state()
        dist_state.subscribe(lambda: update_ui())
    """
    
    def __init__(self):
        self._distribution_state = DistributionTabState()
        self._sampling_state = SamplingTabState()
        self._recovery_state = RecoveryTabState()
    
    def get_distribution_state(self) -> DistributionTabState:
        """获取任务分发状态"""
        return self._distribution_state
    
    def get_sampling_state(self) -> SamplingTabState:
        """获取随机抽样状态"""
        return self._sampling_state
    
    def get_recovery_state(self) -> RecoveryTabState:
        """获取日志恢复状态"""
        return self._recovery_state
    
    def sync_from_config(self, config_manager: Any) -> None:
        """
        从配置管理器同步所有状态
        
        Args:
            config_manager: UnifiedConfigManager 实例
        """
        if config_manager:
            self._distribution_state.update_from_config(
                config_manager.distribution
            )
            self._sampling_state.update_from_config(
                config_manager.sampling
            )
            self._recovery_state.update_from_config(
                config_manager.recovery
            )
