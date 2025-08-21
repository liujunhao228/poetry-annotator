# src/rate_control_manager.py
"""
速率控制管理器，提供统一的速率控制配置和管理接口
"""

from typing import Dict, Any, Optional
import logging
from .utils.rate_controller import RateLimitConfig, create_rate_controller
from .utils.rate_monitor import rate_monitor

logger = logging.getLogger(__name__)


class RateControlManager:
    """速率控制管理器"""
    
    def __init__(self):
        self.controllers: Dict[str, Any] = {}
    
    async def create_controller(self, name: str, config_dict: Dict[str, Any]) -> None:
        """创建速率控制器"""
        try:
            # 解析配置
            qps = float(config_dict.get('qps')) if config_dict.get('qps') else None
            rpm = float(config_dict.get('rpm')) if config_dict.get('rpm') else None
            max_concurrent = int(config_dict.get('max_concurrent')) if config_dict.get('max_concurrent') else None
            burst = int(config_dict.get('burst')) if config_dict.get('burst') else None
            window_size = int(config_dict.get('window_size')) if config_dict.get('window_size') else None
            
            config = RateLimitConfig(
                qps=qps,
                rpm=rpm,
                max_concurrent=max_concurrent,
                burst=burst,
                window_size=window_size
            )
            
            # 创建控制器
            controller = create_rate_controller(config)
            
            # 保存控制器
            self.controllers[name] = controller
            
            # 注册到监控器
            await rate_monitor.register_controller(name, controller)
            
            logger.info(f"成功创建速率控制器: {name}")
        except Exception as e:
            logger.error(f"创建速率控制器 {name} 失败: {e}")
            raise
    
    def get_controller(self, name: str):
        """获取速率控制器"""
        return self.controllers.get(name)
    
    async def remove_controller(self, name: str) -> bool:
        """移除速率控制器"""
        if name in self.controllers:
            del self.controllers[name]
            await rate_monitor.unregister_controller(name)
            logger.info(f"已移除速率控制器: {name}")
            return True
        return False
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有控制器的统计信息"""
        return rate_monitor.get_stats()


# 全局速率控制管理器实例
rate_control_manager = RateControlManager()