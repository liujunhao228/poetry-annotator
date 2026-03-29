"""依赖注入容器 - 轻量级 DI 实现"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, Generic
from pathlib import Path


T = TypeVar('T')


class ServiceDescriptor(Generic[T]):
    """服务描述符 - 存储服务类型和工厂函数"""
    
    def __init__(self, service_type: Type[T], factory: Callable[[], T], singleton: bool = True):
        self.service_type = service_type
        self.factory = factory
        self.singleton = singleton
        self._instance: Optional[T] = None
    
    def get_instance(self) -> T:
        """获取服务实例"""
        if self.singleton and self._instance is not None:
            return self._instance
        
        instance = self.factory()
        if self.singleton:
            self._instance = instance
        return instance
    
    def clear(self) -> None:
        """清除单例实例"""
        self._instance = None


class Container:
    """
    依赖注入容器
    
    支持:
    - 单例/瞬态服务
    - 自动依赖解析
    - 服务生命周期管理
    
    使用示例:
        container = Container()
        container.register(ConfigService, lambda: ConfigService(project))
        container.register_singleton(UnifiedConfigManager)
        
        config_service = container.get(ConfigService)
    """
    
    _global_container: Optional['Container'] = None
    
    def __init__(self):
        self._services: Dict[type, ServiceDescriptor] = {}
        self._instances: Dict[type, Any] = {}
    
    @classmethod
    def get_global(cls) -> 'Container':
        """获取全局容器实例"""
        if cls._global_container is None:
            cls._global_container = Container()
        return cls._global_container
    
    @classmethod
    def set_global(cls, container: 'Container') -> None:
        """设置全局容器实例"""
        cls._global_container = container
    
    def register(
        self,
        service_type: Type[T],
        factory: Optional[Callable[[], T]] = None,
        implementation: Optional[Type[T]] = None,
        singleton: bool = False
    ) -> 'Container':
        """
        注册服务
        
        Args:
            service_type: 服务类型
            factory: 工厂函数
            implementation: 实现类型（可选，如果提供则使用默认构造函数）
            singleton: 是否为单例
        
        Returns:
            容器实例（支持链式调用）
        """
        if factory is None and implementation is None:
            raise ValueError("必须提供 factory 或 implementation")
        
        if implementation is not None:
            factory = lambda: implementation()  # noqa: E731
        
        self._services[service_type] = ServiceDescriptor(service_type, factory, singleton)
        return self
    
    def register_singleton(
        self,
        service_type: Type[T],
        factory: Optional[Callable[[], T]] = None,
        implementation: Optional[Type[T]] = None
    ) -> 'Container':
        """注册单例服务"""
        return self.register(service_type, factory, implementation, singleton=True)
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'Container':
        """
        注册已有实例
        
        Args:
            service_type: 服务类型
            instance: 实例对象
        
        Returns:
            容器实例
        """
        self._instances[service_type] = instance
        return self
    
    def get(self, service_type: Type[T]) -> T:
        """
        获取服务实例
        
        Args:
            service_type: 服务类型
        
        Returns:
            服务实例
        """
        # 先检查已注册的实例
        if service_type in self._instances:
            return self._instances[service_type]
        
        # 再检查服务描述符
        if service_type not in self._services:
            raise KeyError(f"未注册服务：{service_type}")
        
        return self._services[service_type].get_instance()
    
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """
        获取服务实例，如果不存在返回 None
        
        Args:
            service_type: 服务类型
        
        Returns:
            服务实例或 None
        """
        try:
            return self.get(service_type)
        except KeyError:
            return None
    
    def has(self, service_type: type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services or service_type in self._instances
    
    def clear(self) -> None:
        """清除所有注册和实例"""
        self._services.clear()
        self._instances.clear()
    
    def clear_singletons(self) -> None:
        """清除所有单例实例"""
        for descriptor in self._services.values():
            descriptor.clear()
        self._instances.clear()


# 便捷函数
def create_container() -> Container:
    """创建新容器"""
    return Container()


def get_global_container() -> Container:
    """获取全局容器"""
    return Container.get_global()


# GUI 专用的容器构建器
def build_gui_container(project: Any, config_service: Any = None) -> Container:
    """
    构建 GUI 模块的标准容器

    Args:
        project: Project 实例
        config_service: 可选的 ConfigService 实例

    Returns:
        配置好的容器实例
    """
    from .services.config_service import ConfigService
    
    container = Container()

    # 注册 Project
    container.register_instance(type(project), project)

    # 注册 ConfigService
    if config_service is not None:
        container.register_instance(ConfigService, config_service)
    else:
        container.register_singleton(
            ConfigService,
            lambda: ConfigService(project)
        )

    # 注册统一配置管理器
    from .models.config_manager import UnifiedConfigManager
    container.register_singleton(UnifiedConfigManager, lambda: UnifiedConfigManager())

    # 注册日志服务
    from .services.log_service import LogService
    container.register_singleton(LogService)

    # 注册异步任务执行器工厂
    from .services.async_task_executor import AsyncTaskExecutor
    container.register(AsyncTaskExecutor, lambda: AsyncTaskExecutor())

    return container
