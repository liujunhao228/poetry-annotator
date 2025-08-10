# src/annotator.py

import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pybreaker

from .data_manager import data_manager
from .llm_factory import llm_factory
from .config_manager import config_manager
from .label_parser import label_parser

logger = logging.getLogger(__name__)

class Annotator:
    """诗词情感标注器 - 负责单个模型的并发标注任务"""

    def __init__(self, config_name: str):
        """初始化标注器"""
        if not config_name:
            raise ValueError("必须提供模型配置别名")
            
        self.model_identifier = config_name
        self.llm_service = llm_factory.get_llm_service(self.model_identifier)
        self.breaker = llm_factory.get_breaker(self.model_identifier)

        llm_config = config_manager.get_llm_config()
        self.max_workers = llm_config['max_workers']
        self.max_retries = llm_config.get('max_retries', 3)
        self.retry_delay_multiplier = llm_config.get('retry_delay', 1)  # 作为指数退避的乘数
        self.retry_backoff_factor = llm_config.get('retry_backoff_factor', 2) # Tenacity的wait_random_exponential没有直接用backoff_factor，它是隐式的2，但我们可以保留这个配置项以备将来使用更复杂的策略
        self.retry_max_wait = llm_config.get('retry_max_wait', 60)
        
        try:
            self.emotion_schema = label_parser.get_categories_text()
            # INFO级别：记录对用户有意义的关键流程节点
            logger.info(f"成功加载情感分类体系 - 长度: {len(self.emotion_schema)} 字符")
        except Exception as e:
            # ERROR级别：记录关键错误，应在控制台和文件都显示
            logger.error(f"加载情感分类体系失败: {e}")
            raise
        
        # INFO级别：初始化信息，简洁明了
        logger.info(f"初始化标注器: 模型配置='{self.model_identifier}', 并发数={self.max_workers}")
    
    def _generate_sentences_with_id(self, paragraphs: List[str]) -> List[Dict[str, str]]:
        """为句子生成ID并构建JSON格式"""
        return [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(paragraphs)]
    
    def _validate_and_transform_response(
        self, 
        original_sentences: List[Dict[str, str]], 
        llm_output: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        [已重构] 验证LLM响应与输入的一致性，并将其转换为最终存储格式。
        """
        # DEBUG级别：记录函数进入和内部状态，对用户无感，对调试有用。
        logger.debug(f"开始业务层验证与转换 - 输入句子数: {len(original_sentences)}")
        
        if not isinstance(llm_output, list) or not llm_output:
            raise ValueError(f"LLM输出必须是一个非空列表，但实际是: {llm_output}")
        
        input_ids = {item['id'] for item in original_sentences}
        output_ids = {item['id'] for item in llm_output}
        
        if input_ids != output_ids:
            missing = sorted(list(input_ids - output_ids))
            extra = sorted(list(output_ids - input_ids))
            error_msg = "LLM返回的句子ID与输入不匹配!"
            if missing:
                error_msg += f" 缺失ID: {missing}."
            if extra:
                error_msg += f" 多余ID: {extra}."
            raise ValueError(error_msg)
        
        annotations_by_id = {item['id']: item for item in llm_output}
        final_results = []
        for original_item in original_sentences:
            anno = annotations_by_id[original_item['id']]
            final_results.append({
                "sentence_id": original_item['id'],
                "sentence_text": original_item['sentence'],
                "primary_emotion": anno['primary'],
                "secondary_emotions": anno['secondary']
            })
        
        # [调整] DEBUG级别：将详细的、结构化的调试信息记录在DEBUG级别，仅输出到文件。
        logger.debug(f"业务层验证与数据转换成功，已合并 {len(final_results)} 条标注。")
        logger.debug(f"合并后的标注详情: {json.dumps(final_results, ensure_ascii=False, indent=2)}")
        
        return final_results

    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """标注单首诗词，包含完整的处理流程和重试逻辑"""
        poem_id = poem['id']
        # --- Tenacity 重试策略保持不变 ---
        @retry(
            wait=wait_random_exponential(multiplier=self.retry_delay_multiplier, max=self.retry_max_wait),
            stop=stop_after_attempt(self.max_retries),
            before_sleep=lambda retry_state: logger.warning(
                f"诗词ID {poem_id} (模型: {self.model_identifier}) API调用失败，"
                f"将在 {retry_state.next_action.sleep:.2f} 秒后进行第 {retry_state.attempt_number + 1} 次重试..."
            )
        )
        async def _do_llm_call_with_retry():
            return await self.llm_service.annotate_poem(
                poem=poem,
                emotion_schema=self.emotion_schema
            )
        try:
            # [关键修改] 使用 pybreaker.call_async 来包装带有 tenacity 重试的函数。
            # - 如果 _do_llm_call_with_retry 成功, breaker 自动记录成功。
            # - 如果 _do_llm_call_with_retry 失败 (所有重试后), breaker 自动记录失败并重新抛出异常。
            # - 如果 breaker 已开启, call_async 会直接抛出 CircuitBreakerError。
            llm_output_validated = await self.breaker.call_async(_do_llm_call_with_retry)
            
            sentences_with_id = self._generate_sentences_with_id(poem['paragraphs'])
            final_results = self._validate_and_transform_response(sentences_with_id, llm_output_validated)
            
            return {
                'poem_id': poem_id, 
                'status': 'completed', 
                'annotation_result': json.dumps(final_results, ensure_ascii=False),
                'error_message': None
            }
            
        except pybreaker.CircuitBreakerError as e:
            # 这个块会捕获 call_async 因为熔断器开启而抛出的异常
            logger.warning(
                f"诗词ID {poem_id} (模型: {self.model_identifier}) 因熔断器开启而跳过请求。 "
                f"错误: {e}"
            )
            return {
                'poem_id': poem_id, 
                'status': 'failed',
                'annotation_result': None, 
                'error_message': f"Circuit breaker is open: {e}"
            }
        except Exception as e:
            # 这个块会捕获从 _do_llm_call_with_retry (通过 tenacity 和 pybreaker) 抛出的最终异常
            logger.error(
                f"诗词ID {poem_id} (模型: {self.model_identifier}) 标注流程在所有重试后最终失败: {str(e)}",
                exc_info=True
            )
            return {
                'poem_id': poem_id, 
                'status': 'failed',
                'annotation_result': None, 
                'error_message': str(e)
            }

    async def run(self, limit: Optional[int] = None, 
                  start_id: Optional[int] = None, 
                  end_id: Optional[int] = None,
                  force_rerun: bool = False,
                  poem_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """异步运行指定模型的所有标注任务"""
        start_time = time.time()
        
        # INFO级别：任务启动信息，对用户清晰展示任务参数。
        logger.info(f"[{self.model_identifier}] 开始标注任务 - 限制: {limit or '无'}, 范围: {start_id or '开始'}-{end_id or '结束'}, 强制重跑: {force_rerun}, 指定ID: {poem_ids is not None}")
        
        if poem_ids is not None:
            poems = data_manager.get_poems_by_ids(poem_ids)
        else:
            poems = data_manager.get_poems_to_annotate(
                model_identifier=self.model_identifier,
                limit=limit, start_id=start_id, end_id=end_id, force_rerun=force_rerun
            )
            
        if not poems:
            # INFO级别：告知用户没有待处理项，是重要的流程状态。
            logger.info(f"[{self.model_identifier}] 没有找到待标注的诗词。")
            return {'total': 0, 'completed': 0, 'failed': 0, 'model': self.model_identifier}
        
        total_poems = len(poems)
        # INFO级别：告知用户待处理项总数，是重要的流程状态。
        logger.info(f"[{self.model_identifier}] 找到 {total_poems} 首待标注诗词，并发数: {self.max_workers}")
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def work_unit(poem):
            async with semaphore:
                return await self._annotate_single_poem(poem)

        tasks = [work_unit(poem) for poem in poems]
        
        completed_count, failed_count = 0, 0
        
        progress_bar = tqdm(total=total_poems, desc=f"标注中 ({self.model_identifier})", unit="首")
        for future in asyncio.as_completed(tasks):
            result = await future
            
            data_manager.save_annotation(
                poem_id=result['poem_id'],
                model_identifier=self.model_identifier,
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
        execution_time = time.time() - start_time
        
        success_rate = (completed_count / total_poems * 100) if total_poems > 0 else 0
        avg_time_per_poem = execution_time / total_poems if total_poems > 0 else 0
        
        # INFO级别：最终的任务总结报告，是用户最关心的信息。
        logger.info(
            f"[{self.model_identifier}] 任务完成! "
            f"耗时: {execution_time:.2f}秒 (平均 {avg_time_per_poem:.2f}秒/首), "
            f"总计: {total_poems}, 成功: {completed_count} ({success_rate:.1f}%), 失败: {failed_count}"
        )
        
        return {
            'total': total_poems,
            'completed': completed_count,
            'failed': failed_count,
            'model': self.model_identifier,
            'execution_time': execution_time,
            'success_rate': success_rate
        }