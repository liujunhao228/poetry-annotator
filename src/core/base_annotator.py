"""
标注器抽象基类 - 定义通用标注流程模板

Annotator Abstract Base Class - defines common annotation workflow template
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor

import pybreaker
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm import tqdm

from .base_schema import BaseAnnotationSchema
from .base_prompt import BasePromptBuilder


class BaseAnnotator(ABC):
    """
    标注器抽象基类 - 使用模板方法模式
    
    定义通用的标注流程，子类实现特定的标注逻辑：
    - prompt 构建
    - 响应验证
    - 结果转换
    """
    
    def __init__(
        self,
        config_name: str,
        project_context: Any,
        max_workers: int = 5,
        max_retries: int = 3,
        retry_delay_multiplier: float = 1.0,
        retry_max_wait: float = 60.0
    ):
        """
        初始化标注器
        
        Args:
            config_name: 模型配置别名
            project_context: 项目上下文
            max_workers: 最大并发数
            max_retries: 最大重试次数
            retry_delay_multiplier: 重试延迟乘数
            retry_max_wait: 最大重试等待时间
        """
        self.config_name = config_name
        self.project_context = project_context
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.retry_delay_multiplier = retry_delay_multiplier
        self.retry_max_wait = retry_max_wait
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 从项目上下文获取依赖
        self.llm_service = self._get_llm_service()
        self.breaker = self._get_circuit_breaker()
        self.data_manager = self._get_data_manager()
        
        # 子类初始化的 hook
        self._init_custom()
    
    @abstractmethod
    def _init_custom(self) -> None:
        """
        子类自定义初始化
        
        在此方法中初始化项目特定的组件（schema、prompt_builder 等）
        """
        pass
    
    @abstractmethod
    def _get_schema(self) -> BaseAnnotationSchema:
        """获取项目特定的 schema"""
        pass
    
    @abstractmethod
    def _get_prompt_builder(self) -> BasePromptBuilder:
        """获取项目特定的 prompt 构建器"""
        pass
    
    @abstractmethod
    def _validate_response(
        self, 
        llm_output: Any, 
        input_sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证并转换 LLM 响应
        
        Args:
            llm_output: LLM 原始输出
            input_sentences: 输入句子列表
            
        Returns:
            验证后的标注结果
        """
        pass
    
    def _get_llm_service(self):
        """从项目上下文获取 LLM 服务"""
        return self.project_context.llm_factory.get_llm_service(self.config_name)
    
    def _get_circuit_breaker(self):
        """从项目上下文获取熔断器"""
        return self.project_context.llm_factory.get_breaker(self.config_name)
    
    def _get_data_manager(self):
        """从项目上下文获取数据管理器"""
        return self.project_context.get_data_manager()
    
    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """
        标注单首诗词（模板方法）
        
        包含完整的处理流程：
        1. 构建 prompt
        2. 调用 LLM（带重试和熔断）
        3. 验证响应
        4. 返回结果
        
        Args:
            poem: 诗词数据
            
        Returns:
            标注结果字典
        """
        poem_id = poem['id']
        self.logger.info(f"开始处理诗词 ID: {poem_id}")
        
        # 定义带重试的 LLM 调用
        @retry(
            wait=wait_random_exponential(
                multiplier=self.retry_delay_multiplier, 
                max=self.retry_max_wait
            ),
            stop=stop_after_attempt(self.max_retries),
            before_sleep=lambda retry_state: self.logger.warning(
                f"诗词 ID {poem_id} API 调用失败，"
                f"将在 {retry_state.next_action.sleep:.2f} 秒后重试 "
                f"(第 {retry_state.attempt_number + 1} 次)..."
            )
        )
        async def _do_llm_call():
            # 构建 prompt
            system_prompt, user_prompt = self._build_prompt(poem)
            # 调用 LLM
            return await self.llm_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        
        try:
            # 使用熔断器包装 LLM 调用
            llm_raw_output = await self.breaker.call_async(_do_llm_call)
            
            # 解析 JSON 输出
            try:
                llm_output_json = json.loads(llm_raw_output)
            except json.JSONDecodeError as e:
                self.logger.error(f"解析 LLM 输出失败 (ID {poem_id}): {e}")
                raise ValueError(f"LLM 输出不是有效的 JSON: {llm_raw_output}")
            
            # 准备输入句子（带 ID）
            paragraphs = poem.get('paragraphs', [])
            input_sentences = self._generate_sentences_with_id(paragraphs)
            
            # 验证并转换响应
            final_results = self._validate_response(llm_output_json, input_sentences)
            
            self.logger.info(f"诗词 ID {poem_id} 标注完成")
            
            return {
                'poem_id': poem_id,
                'status': 'completed',
                'annotation_result': json.dumps(final_results, ensure_ascii=False),
                'error_message': None
            }
            
        except pybreaker.CircuitBreakerError as e:
            self.logger.warning(f"诗词 ID {poem_id} 熔断器开启，跳过请求：{e}")
            return {
                'poem_id': poem_id,
                'status': 'failed',
                'annotation_result': None,
                'error_message': f"Circuit breaker is open: {e}"
            }
            
        except Exception as e:
            self.logger.error(f"诗词 ID {poem_id} 标注失败：{e}", exc_info=True)
            return {
                'poem_id': poem_id,
                'status': 'failed',
                'annotation_result': None,
                'error_message': str(e)
            }
    
    def _build_prompt(self, poem: Dict[str, Any]) -> Tuple[str, str]:
        """
        构建 prompt
        
        Args:
            poem: 诗词数据
            
        Returns:
            (system_prompt, user_prompt)
        """
        schema = self._get_schema()
        prompt_builder = self._get_prompt_builder()
        
        # 获取 schema 文本
        schema_text = schema.get_schema_text()
        
        return prompt_builder.build_prompts(
            poem_data=poem,
            schema=schema.get_schema(),
            model_config=self.llm_service.config
        )
    
    def _generate_sentences_with_id(self, paragraphs: list) -> list:
        """为句子生成 ID"""
        return [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(paragraphs)]
    
    async def run(
        self,
        limit: Optional[int] = None,
        start_id: Optional[int] = None,
        end_id: Optional[int] = None,
        force_rerun: bool = False,
        poem_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        运行标注任务（模板方法）
        
        通用标注流程：
        1. 获取待标注诗词
        2. 并发控制
        3. 执行标注
        4. 保存结果
        5. 返回统计
        
        Args:
            limit: 限制数量
            start_id: 起始 ID
            end_id: 结束 ID
            force_rerun: 是否强制重跑
            poem_ids: 指定的诗词 ID 列表
            
        Returns:
            标注任务统计结果
        """
        start_time = time.time()
        
        self.logger.info(
            f"[{self.config_name}] 开始标注任务 - "
            f"限制：{limit or '无'}, 范围：{start_id or '开始'}-{end_id or '结束'}, "
            f"强制重跑：{force_rerun}, 指定 ID: {poem_ids is not None}"
        )
        
        # 获取待标注诗词
        if poem_ids is not None:
            poems = self.data_manager.get_poems_by_ids(poem_ids)
        else:
            poems = self.data_manager.get_poems_to_annotate(
                model_identifier=self.config_name,
                limit=limit,
                start_id=start_id,
                end_id=end_id,
                force_rerun=force_rerun
            )
        
        if not poems:
            self.logger.info(f"[{self.config_name}] 没有找到待标注的诗词")
            return {'total': 0, 'completed': 0, 'failed': 0, 'model': self.config_name}
        
        total_poems = len(poems)
        self.logger.info(
            f"[{self.config_name}] 找到 {total_poems} 首待标注诗词，并发数：{self.max_workers}"
        )
        
        # 并发控制
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def work_unit(poem):
            async with semaphore:
                return await self._annotate_single_poem(poem)
        
        tasks = [work_unit(poem) for poem in poems]
        
        # 执行任务
        completed_count, failed_count = 0, 0
        
        progress_bar = tqdm(
            total=total_poems, 
            desc=f"标注中 ({self.config_name})", 
            unit="首"
        )
        
        for future in asyncio.as_completed(tasks):
            result = await future
            
            # 保存结果
            self.data_manager.save_annotation(
                poem_id=result['poem_id'],
                model_identifier=self.config_name,
                status=result['status'],
                annotation_result=result.get('annotation_result'),
                error_message=result.get('error_message')
            )
            
            if result['status'] == 'completed':
                completed_count += 1
            else:
                failed_count += 1
            
            progress_bar.set_postfix({'成功': completed_count, '失败': failed_count})
            progress_bar.update(1)
        
        progress_bar.close()
        
        # 计算统计
        execution_time = time.time() - start_time
        success_rate = (completed_count / total_poems * 100) if total_poems > 0 else 0
        avg_time_per_poem = execution_time / total_poems if total_poems > 0 else 0
        
        self.logger.info(
            f"[{self.config_name}] 任务完成! "
            f"耗时：{execution_time:.2f}秒 (平均 {avg_time_per_poem:.2f}秒/首), "
            f"总计：{total_poems}, 成功：{completed_count} ({success_rate:.1f}%), 失败：{failed_count}"
        )
        
        return {
            'total': total_poems,
            'completed': completed_count,
            'failed': failed_count,
            'model': self.config_name,
            'execution_time': execution_time,
            'success_rate': success_rate
        }
