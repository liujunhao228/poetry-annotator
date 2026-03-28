# src/utils/health_checker.py

import logging
import asyncio
from typing import List, Tuple, Optional
from pathlib import Path

from ..label_parser import LabelParser
from ..config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 延迟初始化 LabelParser 实例
_label_parser_instance: Optional[LabelParser] = None

def get_label_parser() -> LabelParser:
    """获取 LabelParser 单例实例"""
    global _label_parser_instance
    if _label_parser_instance is None:
        _label_parser_instance = LabelParser()
    return _label_parser_instance

class HealthChecker:
    """负责执行全面的任务前健康检查"""

    def __init__(self, llm_factory_instance=None, config_manager_instance=None):
        """初始化健康检查器

        Args:
            llm_factory_instance: LLMFactory 实例，用于创建模型服务
            config_manager_instance: ConfigManager 实例，用于获取配置
        """
        self._llm_factory = llm_factory_instance
        self._config_manager = config_manager_instance

    def set_llm_factory(self, llm_factory_instance):
        """设置 LLMFactory 实例"""
        self._llm_factory = llm_factory_instance

    def set_config_manager(self, config_manager_instance: ConfigManager):
        """设置 ConfigManager 实例"""
        self._config_manager = config_manager_instance

    async def run_all_checks(self, models_to_check: List[str], llm_factory_instance: Optional = None, config_manager_instance: Optional[ConfigManager] = None) -> bool:
        """
        执行所有必要的健康检查。

        Args:
            models_to_check: 将要用于任务的模型配置名称列表。
            llm_factory_instance: LLMFactory 实例，用于创建模型服务
            config_manager_instance: ConfigManager 实例，用于获取配置

        Returns:
            True 如果所有检查都通过，否则返回 False。
        """
        # 如果传入了 llm_factory_instance，则更新
        if llm_factory_instance is not None:
            self.set_llm_factory(llm_factory_instance)
        
        # 如果传入了 config_manager_instance，则更新
        if config_manager_instance is not None:
            self.set_config_manager(config_manager_instance)

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

        # 检查 ConfigManager 是否已设置
        if self._config_manager is None:
            logger.error("[✗] ConfigManager 实例未设置")
            return False

        # 检查情感分类体系文件
        try:
            categories_config = self._config_manager.get_categories_config()
            md_path = categories_config.get('md_path')
            xml_path = categories_config.get('xml_path')
            
            # 将相对路径转换为绝对路径（相对于配置文件所在目录）
            # ConfigManager 的配置文件路径最后一个通常是项目配置文件
            if self._config_manager.config_paths:
                config_dir = Path(self._config_manager.config_paths[-1]).parent
            else:
                config_dir = Path.cwd()
            
            # 转换相对路径为绝对路径
            if md_path and not Path(md_path).is_absolute():
                md_path = str(config_dir / md_path)
            if xml_path and not Path(xml_path).is_absolute():
                xml_path = str(config_dir / xml_path)
            
            # 使用配置文件中的路径创建 LabelParser 实例
            label_parser_instance = LabelParser(xml_path=xml_path, md_path=md_path)
            label_parser_instance.get_categories_text()
            logger.info(f"[✓] 情感分类体系文件加载成功 ({md_path})")
        except Exception as e:
            logger.error(f"[✗] 情感分类体系文件加载失败：{e}", exc_info=True)
            passed = False

        # 检查数据路径
        try:
            data_config = self._config_manager.get_data_config()
            source_dir = Path(data_config['source_dir'])
            output_dir = Path(data_config['output_dir'])
            
            # 将相对路径转换为绝对路径（相对于配置文件所在目录）
            if self._config_manager.config_paths:
                config_dir = Path(self._config_manager.config_paths[-1]).parent
            else:
                config_dir = Path.cwd()
            
            if not source_dir.is_absolute():
                source_dir = config_dir / source_dir
            if not output_dir.is_absolute():
                output_dir = config_dir / output_dir
            
            if not source_dir.exists() or not source_dir.is_dir():
                 logger.warning(f"[!] 数据源目录不存在：{source_dir}")
            else:
                 logger.info(f"[✓] 数据源目录存在：{source_dir}")

            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[✓] 输出目录已确保存在：{output_dir}")

        except Exception as e:
            logger.error(f"[✗] 检查数据路径时出错：{e}")
            passed = False

        return passed

    async def _check_models(self, model_names: List[str]) -> List[bool]:
        """并发检查指定的模型服务"""
        logger.info("\n--- 检查模型服务 ---")
        tasks = []
        for model_name in model_names:
            tasks.append(self._check_single_model(model_name))

        results = await asyncio.gather(*tasks)
        return list(results)

    async def _check_single_model(self, model_name: str) -> bool:
        """检查单个模型的配置和服务连通性"""
        if self._llm_factory is None:
            logger.error(f"[✗] [{model_name}] LLMFactory 实例未设置，跳过检查")
            return False

        try:
            service = self._llm_factory.get_llm_service(model_name)
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

# 创建一个全局实例供外部调用
health_checker = HealthChecker()
