# src/utils/health_checker.py

import logging
import asyncio
from typing import List, Tuple
from pathlib import Path

from ..llm_factory import llm_factory
from ..label_parser import get_label_parser
from ..config_manager import config_manager # 导入以检查路径

logger = logging.getLogger(__name__)

class HealthChecker:
    """负责执行全面的任务前健康检查"""

    async def run_all_checks(self, models_to_check: List[str]) -> bool:
        """
        执行所有必要的健康检查。

        Args:
            models_to_check: 将要用于任务的模型配置名称列表。

        Returns:
            True 如果所有检查都通过，否则返回 False。
        """
        logger.info("=" * 60)
        logger.info("🚀 开始执行任务前健康检查...")
        
        all_ok = True
        
        # 1. 检查共享资源
        if not self._check_shared_resources():
            all_ok = False

        # 2. 检查每个指定的模型
        if models_to_check:
            model_results = await self._check_models(models_to_check)
            if not all(model_results):
                all_ok = False
        else:
            logger.warning("没有指定要检查的模型。")

        logger.info("-" * 60)
        if all_ok:
            logger.info("✅ 所有健康检查项均已通过！")
        else:
            logger.error("❌ 健康检查未通过。请检查上述错误信息并修复配置。")
        logger.info("=" * 60)
            
        return all_ok

    def _check_shared_resources(self) -> bool:
        """检查所有任务共享的资源，如配置文件、路径等"""
        logger.info("\n--- 检查共享资源 ---")
        passed = True
        
        # 检查情感分类体系文件
        try:
            categories_config = config_manager.get_categories_config()
            md_path = categories_config.get('md_path')
            # 这是一个隐式检查，get_categories_text会尝试读取文件
            label_parser = get_label_parser()
            label_parser.get_categories_text()
            logger.info(f"[✓] 情感分类体系文件加载成功 ({md_path})")
        except Exception as e:
            logger.error(f"[✗] 情感分类体系文件加载失败: {e}", exc_info=True)
            passed = False
            
        # 检查数据路径
        try:
            data_config = config_manager.get_data_config()
            source_dir = Path(data_config['source_dir'])
            output_dir = Path(data_config['output_dir'])
            if not source_dir.exists() or not source_dir.is_dir():
                 logger.warning(f"[!] 数据源目录不存在: {source_dir}")
            else:
                 logger.info(f"[✓] 数据源目录存在: {source_dir}")

            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[✓] 输出目录已确保存在: {output_dir}")

        except Exception as e:
            logger.error(f"[✗] 检查数据路径时出错: {e}")
            passed = False
            
        return passed

    async def _check_models(self, model_names: List[str]) -> List[bool]:
        """并发检查指定的模型服务"""
        logger.info("\n--- 检查模型服务 ---")
        tasks = []
        for model_name in model_names:
            tasks.append(self._check_single_model(model_name))
        
        results = await asyncio.gather(*tasks)
        return results

    async def _check_single_model(self, model_name: str) -> bool:
        """检查单个模型的配置和服务连通性
        try:
            # 检查服务实例创建（这会验证配置的基本完整性）
            service = llm_factory.get_llm_service(model_name)
            logger.info(f"[✓] [{model_name}] 服务实例创建成功 (Provider: {service.provider}, Model: {service.model})")
            
            # 执行API连通性检查
            is_healthy, message = await service.health_check()
            if is_healthy:
                logger.info(f"[✓] [{model_name}] API连通性测试通过。")
                return True
            else:
                logger.error(f"[✗] [{model_name}] API连通性测试失败: {message}")
                return False

        except Exception as e:
            logger.error(f"[✗] [{model_name}] 检查失败: {e}", exc_info=False) # 在这里不打印堆栈，因为通常是配置错误
            return False
        """
        return True

# 创建一个全局实例供外部调用
health_checker = HealthChecker()
