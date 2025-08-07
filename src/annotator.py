import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed

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
        
        llm_config = config_manager.get_llm_config()
        self.max_workers = llm_config['max_workers']
        self.max_retries = llm_config.get('max_retries', 3)
        self.retry_delay = llm_config.get('retry_delay', 1)
        
        try:
            self.emotion_schema = label_parser.get_categories_text()
            logger.info(f"成功加载情感分类体系 - 长度: {len(self.emotion_schema)} 字符")
        except Exception as e:
            logger.error(f"加载情感分类体系失败: {e}")
            raise
        
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

        此方法负责业务层/内容层的验证，它假设 `llm_output` 已经通过了 `llm_response_parser` 的结构验证。

        主要职责:
        1.  **内容一致性验证**: 确保LLM为输入的每个句子都提供了标注，不多也不少。
        2.  **数据转换与合并**: 将原始句子文本与LLM的标注结果合并，形成最终的数据结构。
        """
        logger.debug(f"开始业务层验证与转换 - 输入句子数: {len(original_sentences)}")
        
        # 防御性检查: 尽管 llm_response_parser 已保证格式，这里的检查是最后一道防线。
        if not isinstance(llm_output, list) or not llm_output:
            raise ValueError(f"LLM输出必须是一个非空列表，但实际是: {llm_output}")
        
        # 核心业务验证：比对输入和输出的句子ID集合。
        # 这是 Annotator 的关键职责，因为只有它同时拥有输入和输出的上下文。
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
        
        # 数据转换与合并
        # 此处不再需要 try-except KeyError，因为 llm_response_parser 已保证了键的存在。
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
        
        logger.debug("业务层验证与数据转换成功")
        return final_results

    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """标注单首诗词，包含完整的处理流程和重试逻辑"""
        poem_id = poem['id']

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_delay)
        )
        async def _do_llm_call_with_retry():
            # 此内部函数封装了对LLM服务的核心调用，以便tenacity可以重试
            return await self.llm_service.annotate_poem(
                poem=poem,
                emotion_schema=self.emotion_schema
            )

        try:
            # 步骤 1: 调用LLM（带重试逻辑）并获取经过结构验证的响应
            llm_output_validated = await _do_llm_call_with_retry()
            
            # 步骤 2: 进行内容一致性验证并转换数据格式
            sentences_with_id = self._generate_sentences_with_id(poem['paragraphs'])
            # 确保 llm_output_validated 是列表类型
            if isinstance(llm_output_validated, dict):
                llm_output_validated = [llm_output_validated]
            final_results = self._validate_and_transform_response(sentences_with_id, llm_output_validated)
            
            return {
                'poem_id': poem_id, 
                'status': 'completed', 
                'annotation_result': json.dumps(final_results, ensure_ascii=False),
                'error_message': None
            }
            
        except Exception as e:
            logger.error(f"诗词ID {poem_id} (模型: {self.model_identifier}) 标注流程最终失败: {str(e)}")
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
        
        logger.info(f"[{self.model_identifier}] 开始标注任务 - 限制: {limit or '无'}, 范围: {start_id or '开始'}-{end_id or '结束'}, 强制重跑: {force_rerun}, 指定ID: {poem_ids is not None}")
        
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
