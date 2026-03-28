"""
诗词情感标注器 - 负责单个模型的并发标注任务
"""

import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pybreaker

from ..annotation_data_logger import AnnotationDataLogger

logger = logging.getLogger(__name__)


class Annotator:
    """诗词情感标注器"""

    def __init__(self, config_name: str, project_context):
        if not config_name:
            raise ValueError("必须提供模型配置别名")
        if not project_context:
            raise ValueError("必须提供项目上下文")

        self.model_identifier = config_name
        self.project_context = project_context

        llm_factory_instance = self.project_context.llm_factory
        self.llm_service = llm_factory_instance.get_llm_service(self.model_identifier)
        self.breaker = llm_factory_instance.get_breaker(self.model_identifier)

        config_manager_instance = self.project_context.config_manager
        llm_config = config_manager_instance.get_llm_config()
        self.max_workers = llm_config['max_workers']
        self.max_retries = llm_config.get('max_retries', 3)
        self.retry_delay_multiplier = llm_config.get('retry_delay', 1)
        self.retry_max_wait = llm_config.get('retry_max_wait', 60)

        label_parser_instance = self.project_context.label_parser
        self.emotion_schema = label_parser_instance.get_categories_text()
        logger.info(f"成功加载情感分类体系 - 长度：{len(self.emotion_schema)} 字符")

        logger.info(f"初始化标注器：模型配置='{self.model_identifier}', 并发数={self.max_workers}")

        self.annotation_data_logger = AnnotationDataLogger(self.model_identifier)

    def _generate_sentences_with_id(self, paragraphs: List[str]) -> List[Dict[str, str]]:
        """为句子生成 ID 并构建 JSON 格式"""
        return [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(paragraphs)]

    def _validate_and_transform_response(
        self,
        original_sentences: List[Dict[str, str]],
        llm_output: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """验证 LLM 响应与输入的一致性，并转换为最终存储格式"""
        logger.debug(f"开始业务层验证与转换 - 输入句子数：{len(original_sentences)}")

        if not isinstance(llm_output, list) or not llm_output:
            logger.error(f"LLM 输出验证失败：输出必须是一个非空列表")
            raise ValueError(f"LLM 输出必须是一个非空列表")

        input_ids = {item['id'] for item in original_sentences}
        output_ids = {item['id'] for item in llm_output}

        if input_ids != output_ids:
            missing = sorted(list(input_ids - output_ids))
            extra = sorted(list(output_ids - input_ids))
            error_msg = "LLM 返回的句子 ID 与输入不匹配!"
            if missing:
                error_msg += f" 缺失 ID: {missing}."
            if extra:
                error_msg += f" 多余 ID: {extra}."
            logger.error(f"LLM 输出 ID 验证失败：{error_msg}")
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

        logger.debug(f"业务层验证与数据转换成功，已合并 {len(final_results)} 条标注。")
        return final_results

    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """标注单首诗词，包含完整的处理流程和重试逻辑"""
        poem_id = poem['id']
        logger.info(f"开始处理诗词 ID: {poem_id}")
        logger.debug(f"诗词 ID {poem_id} 内容：{poem}")

        @retry(
            wait=wait_random_exponential(multiplier=self.retry_delay_multiplier, max=self.retry_max_wait),
            stop=stop_after_attempt(self.max_retries),
            before_sleep=lambda retry_state: logger.warning(
                f"诗词 ID {poem_id} API 调用失败，将在 {retry_state.next_action.sleep:.2f} 秒后重试..."
            )
        )
        async def _do_llm_call_with_retry():
            return await self.llm_service.annotate_poem(
                poem=poem,
                emotion_schema=self.emotion_schema
            )

        try:
            llm_output_validated = await self.breaker.call_async(_do_llm_call_with_retry)
            logger.debug(f"诗词 ID {poem_id} LLM 原始输出：{llm_output_validated}")

            sentences_with_id = self._generate_sentences_with_id(poem['paragraphs'])
            final_results = self._validate_and_transform_response(sentences_with_id, llm_output_validated)

            logger.info(f"诗词 ID {poem_id} 标注完成")
            self.annotation_data_logger.log_annotation_data(poem_id, final_results)

            return {
                'poem_id': poem_id,
                'status': 'completed',
                'annotation_result': json.dumps(final_results, ensure_ascii=False),
                'error_message': None
            }

        except pybreaker.CircuitBreakerError as e:
            logger.warning(f"诗词 ID {poem_id} 因熔断器开启而跳过请求。错误：{e}")
            error_info = {"status": "failed", "error_message": f"Circuit breaker is open: {e}"}
            self.annotation_data_logger.log_annotation_data(poem_id, error_info)
            return {
                'poem_id': poem_id,
                'status': 'failed',
                'annotation_result': None,
                'error_message': f"Circuit breaker is open: {e}"
            }

        except Exception as e:
            logger.error(f"诗词 ID {poem_id} 标注流程失败：{str(e)}", exc_info=True)
            error_info = {"status": "failed", "error_message": str(e)}
            self.annotation_data_logger.log_annotation_data(poem_id, error_info)
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

        logger.info(f"[{self.model_identifier}] 开始标注任务 - 限制：{limit or '无'}, 范围：{start_id or '开始'}-{end_id or '结束'}")

        data_manager = self.project_context.get_data_manager()
        if poem_ids is not None:
            poems = data_manager.get_poems_by_ids(poem_ids)
        else:
            poems = data_manager.get_poems_to_annotate(
                model_identifier=self.model_identifier,
                limit=limit, start_id=start_id, end_id=end_id, force_rerun=force_rerun
            )

        if not poems:
            logger.info(f"[{self.model_identifier}] 没有找到待标注的诗词。")
            return {'total': 0, 'completed': 0, 'failed': 0, 'model': self.model_identifier}

        total_poems = len(poems)
        logger.info(f"[{self.model_identifier}] 找到 {total_poems} 首待标注诗词，并发数：{self.max_workers}")

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

        logger.info(f"[{self.model_identifier}] 任务完成！耗时：{execution_time:.2f}秒，总计：{total_poems}, 成功：{completed_count}, 失败：{failed_count}")

        return {
            'total': total_poems,
            'completed': completed_count,
            'failed': failed_count,
            'model': self.model_identifier,
            'execution_time': execution_time,
            'success_rate': success_rate
        }
