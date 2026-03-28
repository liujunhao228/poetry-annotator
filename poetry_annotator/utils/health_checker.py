"""
健康检查器 - 负责执行任务前健康检查
"""

import logging
import asyncio
from typing import List, Tuple
from pathlib import Path

from ..config import ConfigManager
from ..label_parser import LabelParser

logger = logging.getLogger(__name__)


class HealthChecker:
    """负责执行全面的任务前健康检查"""

    def __init__(self, config_manager: ConfigManager, label_parser: LabelParser):
        self.config_manager = config_manager
        self.label_parser = label_parser

    async def run_all_checks(self, models_to_check: List[str], llm_factory) -> bool:
        """
        执行所有必要的健康检查。

        Args:
            models_to_check: 将要用于任务的模型配置名称列表。
            llm_factory: LLMFactory 实例用于创建服务

        Returns:
            True 如果所有检查都通过，否则返回 False。
        """
        logger.info("=" * 60)
        logger.info("🚀 开始执行任务前健康检查...")

        all_ok = True

        if not self._check_shared_resources():
            all_ok = False

        if models_to_check:
            model_results = await self._check_models(models_to_check, llm_factory)
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
        """检查所有任务共享的资源"""
        logger.info("\n--- 检查共享资源 ---")
        passed = True

        try:
            self.label_parser.get_categories_text()
            logger.info(f"[✓] 情感分类体系文件加载成功")
        except Exception as e:
            logger.error(f"[✗] 情感分类体系文件加载失败：{e}", exc_info=True)
            passed = False

        try:
            data_config = self.config_manager.get_data_config()
            source_dir = Path(data_config['source_dir'])
            output_dir = Path(data_config['output_dir'])
            if source_dir.exists() and source_dir.is_dir():
                logger.info(f"[✓] 数据源目录存在：{source_dir}")
            else:
                logger.warning(f"[!] 数据源目录不存在：{source_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[✓] 输出目录已确保存在：{output_dir}")
        except Exception as e:
            logger.error(f"[✗] 检查数据路径时出错：{e}")
            passed = False

        return passed

    async def _check_models(self, model_names: List[str], llm_factory) -> List[bool]:
        """并发检查指定的模型服务"""
        logger.info("\n--- 检查模型服务 ---")
        tasks = []
        for model_name in model_names:
            tasks.append(self._check_single_model(model_name, llm_factory))
        results = await asyncio.gather(*tasks)
        return list(results)

    async def _check_single_model(self, model_name: str, llm_factory) -> bool:
        """检查单个模型的配置和服务连通性"""
        try:
            service = llm_factory.get_llm_service(model_name)
            logger.info(f"[✓] [{model_name}] 服务实例创建成功 (Provider: {service.provider}, Model: {service.model})")

            is_healthy, message = await service.health_check()
            if is_healthy:
                logger.info(f"[✓] [{model_name}] API 连通性测试通过。")
                return True
            else:
                logger.error(f"[✗] [{model_name}] API 连通性测试失败：{message}")
                return False
        except Exception as e:
            logger.error(f"[✗] [{model_name}] 检查失败：{e}", exc_info=False)
            return False
