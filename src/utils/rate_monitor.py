# src/utils/rate_monitor.py
"""
速率控制监控模块，用于收集和报告速率控制统计信息
"""

import asyncio
import time
from typing import Dict, Any, List
from .rate_controller import RateController
import logging

logger = logging.getLogger(__name__)


class RateMonitor:
    """速率控制监控器"""
    
    def __init__(self):
        self.controllers: Dict[str, RateController] = {}
        self.stats_history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
    
    async def register_controller(self, name: str, controller: RateController) -> None:
        """注册速率控制器"""
        async with self._lock:
            self.controllers[name] = controller
            self.stats_history[name] = []
    
    async def unregister_controller(self, name: str) -> None:
        """注销速率控制器"""
        async with self._lock:
            if name in self.controllers:
                del self.controllers[name]
            if name in self.stats_history:
                del self.stats_history[name]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取所有控制器的当前统计信息"""
        stats = {}
        async with self._lock:
            for name, controller in self.controllers.items():
                try:
                    stats[name] = controller.get_stats()
                except Exception as e:
                    logger.warning(f"获取控制器 {name} 的统计信息时出错: {e}")
                    stats[name] = {"error": str(e)}
        return stats
    
    async def get_history(self, name: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取历史统计信息"""
        async with self._lock:
            if name:
                return {name: self.stats_history.get(name, [])}
            return self.stats_history.copy()
    
    async def start_monitoring(self, interval: float = 10.0) -> None:
        """开始定期监控"""
        logger.info(f"开始监控速率控制器，间隔: {interval}秒")
        while True:
            try:
                await asyncio.sleep(interval)
                current_stats = await self.get_stats()
                timestamp = time.time()
                
                async with self._lock:
                    for name, stats in current_stats.items():
                        self.stats_history[name].append({
                            "timestamp": timestamp,
                            "stats": stats
                        })
                        # 保留最近100条记录
                        if len(self.stats_history[name]) > 100:
                            self.stats_history[name] = self.stats_history[name][-100:]
            except asyncio.CancelledError:
                logger.info("监控任务被取消")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}", exc_info=True)


# 全局监控器实例
rate_monitor = RateMonitor()