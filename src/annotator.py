# src/annotator.py

import json
import logging
import asyncio
import time
import os
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pybreaker
from pathlib import Path

from .data import get_data_manager
from .async_data_manager import AsyncDataManager
from .llm_factory import llm_factory
from .config import config_manager
from .annotation_data_logger import AnnotationDataLogger
from .prompt_builder import prompt_builder
from .logging_config import get_log_directory # 导入获取日志目录的函数
from datetime import datetime # 导入 datetime 用于生成时间戳
from src.llm_services.schemas import PoemData # 导入 PoemData DTO

logger = logging.getLogger(__name__)

class Annotator:
    """诗词情感标注器 - 负责单个模型的并发标注任务"""

    def __init__(self, config_name: str, output_dir: str, source_dir: str, dry_run: bool = False, full_dry_run: bool = False):
        """初始化标注器"""
        self.output_dir = output_dir
        self.source_dir = source_dir
        self.dry_run = dry_run
        self.full_dry_run = full_dry_run

        if self.dry_run:
            # 在 dry-run 模式下，我们使用固定的假模型标识符
            self.model_identifier = "fake-model"
            logger.info("Dry-run mode is enabled, using 'fake-model' as identifier.")
            if self.full_dry_run:
                logger.info("Full dry-run mode is enabled: will perform full process and save to JSON.")
        else:
            if not config_name:
                raise ValueError("必须提供模型配置别名")
            self.model_identifier = config_name

        # 如果是dry_run模式，强制使用fake provider
        if self.dry_run:
            # 创建一个临时的fake配置
            fake_config = {
                'provider': 'fake',
                'model_name': 'fake-model',
                'api_key': 'fake-key',
                'response_delay': '0.1',
                'error_rate': '0.0'
            }
            from .fake_data.service import FakeDataService
            from .response_parsing.llm_response_parser import LLMResponseParser
            self.llm_service = FakeDataService(fake_config, self.model_identifier, LLMResponseParser())
            # 在dry-run模式下，不需要熔断器
            self.breaker = llm_factory.get_breaker('fake-breaker-for-dry-run', is_dummy=True)
        else:
            self.llm_service = llm_factory.get_llm_service(self.model_identifier)
            self.breaker = llm_factory.get_breaker(self.model_identifier)

        llm_config = config_manager.get_llm_config()
        self.max_workers = llm_config['max_workers']
        self.max_retries = llm_config.get('max_retries', 3)
        self.retry_delay_multiplier = llm_config.get('retry_delay', 1)  # 作为指数退避的乘数
        self.retry_backoff_factor = llm_config.get('retry_backoff_factor', 2) # Tenacity的wait_random_exponential没有直接用backoff_factor，它是隐式的2，但我们可以保留这个配置项以备将来使用更复杂的策略
        self.retry_max_wait = llm_config.get('retry_max_wait', 60)
        self.save_full_response = llm_config.get('save_full_response', False)
        
        try:
            # 通过组件系统获取标签解析器
            from .component_system import get_component_system, ComponentType
            project_root = Path(__file__).parent.parent
            component_system = get_component_system(project_root)
            label_parser = component_system.get_component(ComponentType.LABEL_PARSER)
            self.emotion_schema_text = label_parser.get_categories_text()
            # 导入EmotionSchema类
            from .llm_services.schemas import EmotionSchema
            self.emotion_schema = EmotionSchema(text=self.emotion_schema_text)
            # INFO级别：记录对用户有意义的关键流程节点
            logger.info(f"成功加载情感分类体系 - 长度: {len(self.emotion_schema_text)} 字符")
        except Exception as e:
            # ERROR级别：记录关键错误，应在控制台和文件都显示
            logger.error(f"加载情感分类体系失败: {e}")
            raise
            
        # INFO级别：初始化信息，简洁明了
        logger.info(f"初始化标注器: 模型配置='{self.model_identifier}', 并发数={self.max_workers}, 保存完整响应={self.save_full_response}, DRY RUN={self.dry_run}, FULL DRY RUN={self.full_dry_run}")
        
        # 直接使用全局日志记录器，不再尝试导入可能出错的批次日志
        self.model_logger = logger
        
        # 初始化标注数据集合日志器
        self.annotation_data_logger = AnnotationDataLogger(self.model_identifier)
        
        # 如果是 full_dry_run 模式，准备 JSON 输出文件路径
        self.dry_run_output_file: Optional[Path] = None
        if self.dry_run and self.full_dry_run:
            # 明确使用项目根目录下的 logs 文件夹
            project_root = Path(__file__).parent.parent.parent # src/annotator.py -> src -> project_root
            logs_dir = project_root / "logs"
            logs_dir.mkdir(exist_ok=True) # 确保目录存在
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.dry_run_output_file = logs_dir / f"dry_run_annotations_{self.model_identifier}_{timestamp}.jsonl"
            logger.info(f"Full dry-run output will be saved to: {self.dry_run_output_file}")
            logger.debug(f"Dry-run output file path initialized to: {self.dry_run_output_file}")

    async def async_init(self):
        """异步初始化方法，用于创建异步LLM服务"""
        if self.dry_run:
            # 在dry-run模式下，我们已经初始化了FakeDataService，不需要重新初始化
            logger.info(f"异步初始化完成: 模型配置='{self.model_identifier}' (DRY RUN模式)")
        else:
            self.llm_service = await llm_factory.get_llm_service_async(self.model_identifier)
            logger.info(f"异步初始化完成: 模型配置='{self.model_identifier}'")
    
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
            # 使用模型特定日志记录详细错误信息
            # self.model_logger.error(f"LLM输出验证失败: 输出必须是一个非空列表，但实际是: {llm_output}")  # 已注释：不再使用模型特定日志
            logger.error(f"LLM输出验证失败: 输出必须是一个非空列表，但实际是: {llm_output}")
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
            # 使用模型特定日志记录详细错误信息
            # self.model_logger.error(f"LLM输出ID验证失败: {error_msg}")  # 已注释：不再使用模型特定日志
            logger.error(f"LLM输出ID验证失败: {error_msg}")
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
        # 使用模型特定日志记录详细的验证结果，便于调试特定模型的问题
        # self.model_logger.debug(f"业务层验证与数据转换成功，已合并 {len(final_results)} 条标注。")  # 已注释：不再使用模型特定日志
        # 注释掉详细验证内容的记录，因为项目已投入正常运行
        # self.model_logger.debug(f"合并后的标注详情: {json.dumps(final_results, ensure_ascii=False, indent=2)}")
        
        return final_results

    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """标注单首诗词，包含完整的处理流程和重试逻辑"""
        poem_id = poem['id']
        # Wrap poem data in DTO
        poem_dto = PoemData(
            id=poem['id'],
            author=poem['author'],
            title=poem['title'],
            paragraphs=poem['paragraphs']
        )
        # 记录开始处理某首诗的信息到模型特定日志
        # self.model_logger.info(f"开始处理诗词ID: {poem_id}")  # 已注释：不再使用模型特定日志
        logger.info(f"开始处理诗词ID: {poem_id}")
        # 记录诗词内容到模型特定日志，便于调试
        # self.model_logger.debug(f"诗词ID {poem_id} 内容: {poem}")  # 已注释：不再使用模型特定日志
        logger.debug(f"诗词ID {poem_id} 内容: {poem}")
        
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
                poem=poem_dto,
                emotion_schema=self.emotion_schema
            )
        try:
            # [关键修改] 使用 pybreaker.call_async 来包装带有 tenacity 重试的函数。
            # - 如果 _do_llm_call_with_retry 成功, breaker 自动记录成功。
            # - 如果 _do_llm_call_with_retry 失败 (所有重试后), breaker 自动记录失败并重新抛出异常。
            # - 如果 breaker 已开启, call_async 会直接抛出 CircuitBreakerError。
            llm_output_validated = await self.breaker.call_async(_do_llm_call_with_retry)
            
            # 记录LLM原始输出到模型特定日志
            # self.model_logger.debug(f"诗词ID {poem_id} LLM原始输出: {llm_output_validated}")  # 已注释：不再使用模型特定日志
            logger.debug(f"诗词ID {poem_id} LLM原始输出: {llm_output_validated}")
            
            sentences_with_id = self.llm_service._generate_sentences_with_id(poem['paragraphs'])
            final_results = self._validate_and_transform_response(sentences_with_id, llm_output_validated)
            
            # 记录最终结果到模型特定日志
            # self.model_logger.info(f"诗词ID {poem_id} 标注完成")  # 已注释：不再使用模型特定日志
            logger.info(f"诗词ID {poem_id} 标注完成")
            # [已移除] 不再将详细的标注结果记录到主日志文件，因为 AnnotationDataLogger 已负责此项工作。
            # logger.debug(f"诗词ID {poem_id} 最终标注结果: {final_results}")
            
            # [修改] 如果配置要求保存完整响应，则在集合日志中记录完整响应
            annotation_data = {
                "results": final_results
            }
            
            # 记录即将保存的标注数据到集合日志
            self.annotation_data_logger.log_annotation_data(poem_id, annotation_data)
            
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
            # 记录熔断器错误到模型特定日志
            # self.model_logger.warning(  # 已注释：不再使用模型特定日志
            #     f"诗词ID {poem_id} 因熔断器开启而跳过请求。 "
            #     f"错误: {e}"
            # )
            logger.warning(
                f"诗词ID {poem_id} 因熔断器开启而跳过请求。 "
                f"错误: {e}"
            )
            
            # 记录失败的标注数据到集合日志
            error_info = {
                "status": "failed",
                "error_message": f"Circuit breaker is open: {e}"
            }
            self.annotation_data_logger.log_annotation_data(poem_id, error_info)
            
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
            # 记录详细错误到模型特定日志
            # self.model_logger.error(  # 已注释：不再使用模型特定日志
            #     f"诗词ID {poem_id} 标注流程在所有重试后最终失败: {str(e)}",
            #     exc_info=True
            # )
            logger.error(
                f"诗词ID {poem_id} 标注流程在所有重试后最终失败: {str(e)}",
                exc_info=True
            )
            
            # 记录失败的标注数据到集合日志
            error_info = {
                "status": "failed",
                "error_message": str(e)
            }
            self.annotation_data_logger.log_annotation_data(poem_id, error_info)
            
            return {
                'poem_id': poem_id, 
                'status': 'failed',
                'annotation_result': None, 
                'error_message': str(e)
            }
    
    async def stream_annotation_for_poem(self, poem_id: int) -> List[Dict[str, Any]]:
        """
        [修改] 为单首诗词流式传输并验证标注结果。
        这是一个交互式方法，不会将结果保存到数据库。
        调用者负责保存最终结果。

        Args:
            poem_id: 要标注的诗词ID。

        Returns:
            验证后的标注结果列表

        Raises:
            ValueError: 如果找不到指定ID的诗词。
        """
        logger.info(f"[{self.model_identifier}] 开始为诗词ID流式传输并验证标注: {poem_id}")

        try:
            data_manager = AsyncDataManager(self.output_dir, self.source_dir)
            poems = await data_manager.get_poems_by_ids([poem_id])
            if not poems:
                raise ValueError(f"未找到ID为 {poem_id} 的诗词。")
            poem = poems[0]

            poem_dto = PoemData(
                id=str(poem['id']),
                author=poem['author'],
                title=poem['title'],
                paragraphs=poem['paragraphs']
            )

            # 使用新的带验证的流式方法
            validated_result = await self.llm_service.annotate_poem_stream_with_validation(
                poem=poem_dto,
                emotion_schema=self.emotion_schema
            )

            logger.info(f"[{self.model_identifier}] 完成诗词ID的流式标注和验证: {poem_id}")
            return validated_result

        except ValueError as ve:
            logger.error(f"[{self.model_identifier}] 流式标注失败: {ve}")
            raise
        except Exception as e:
            logger.error(f"[{self.model_identifier}] 为诗词ID {poem_id} 进行流式标注时发生意外错误: {e}", exc_info=True)
            # 抛出异常以通知调用者
            raise

    async def run(self, limit: Optional[int] = None, 
                  start_id: Optional[int] = None, 
                  end_id: Optional[int] = None,
                  force_rerun: bool = False,
                  poem_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """异步运行指定模型的所有标注任务"""
        start_time = time.time()
        
        # INFO级别：任务启动信息，对用户清晰展示任务参数。
        logger.info(f"[{self.model_identifier}] 开始标注任务 - 限制: {limit or '无'}, 范围: {start_id or '开始'}-{end_id or '结束'}, 强制重跑: {force_rerun}, 指定ID: {poem_ids is not None}")
        # 在模型特定日志中也记录任务启动信息
        # self.model_logger.info(f"开始标注任务 - 限制: {limit or '无'}, 范围: {start_id or '开始'}-{end_id or '结束'}, 强制重跑: {force_rerun}, 指定ID: {poem_ids is not None}")  # 已注释：不再使用模型特定日志
        logger.info(f"开始标注任务 - 限制: {limit or '无'}, 范围: {start_id or '开始'}-{end_id or '结束'}, 强制重跑: {force_rerun}, 指定ID: {poem_ids is not None}")
        
        data_manager = AsyncDataManager(self.output_dir, self.source_dir)
        
        # 移除 async with 语句，因为 AsyncDataManager 不再是异步上下文管理器
        # async with AsyncDataManager(db_path) as data_manager:
        if poem_ids is not None:
            # 如果指定了ID列表，但不是强制重跑，需要过滤掉已经标注过的诗词
            if not force_rerun:
                poems = await data_manager.get_poems_by_ids_filtered(poem_ids, self.model_identifier)
            else:
                poems = await data_manager.get_poems_by_ids(poem_ids)
        else:
            poems = await data_manager.get_poems_to_annotate(
                model_identifier=self.model_identifier,
                limit=limit, start_id=start_id, end_id=end_id, force_rerun=force_rerun
            )
            
        total_poems = len(poems) # Initialize total_poems here
        
        if not poems:
            # INFO级别：告知用户没有待处理项，是重要的流程状态。
            logger.info(f"[{self.model_identifier}] 没有找到待标注的诗词。")
            # self.model_logger.info("没有找到待标注的诗词。")  # 已注释：不再使用模型特定日志
            return {'total': 0, 'completed': 0, 'failed': 0, 'model': self.model_identifier}
            
        # INFO级别：告知用户待处理项总数，是重要的流程状态。
        logger.info(f"[{self.model_identifier}] 找到 {total_poems} 首待标注诗词，并发数: {self.max_workers}")
        # self.model_logger.info(f"找到 {total_poems} 首待标注诗词，并发数: {self.max_workers}")  # 已注释：不再使用模型特定日志
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def work_unit(poem):
            async with semaphore:
                return await self._annotate_single_poem(poem)

        tasks = [work_unit(poem) for poem in poems]
        
        completed_count, failed_count = 0, 0 # Initialize completed_count and failed_count here
        
        progress_bar = tqdm(total=total_poems, desc=f"标注中 ({self.model_identifier})", unit="首")
        for future in asyncio.as_completed(tasks):
            result = await future
            
            # 处理 dry-run 模式下的数据保存逻辑
            if self.dry_run:
                if self.full_dry_run:
                    # 在 full dry-run 模式下，执行完整流程并保存到 JSON 文件
                    logger.info(f"[Full Dry-run] 保存结果到JSON文件 for poem_id: {result['poem_id']}")
                    await self._save_dry_run_annotation_to_json(
                        poem_id=result['poem_id'],
                        model_identifier=self.model_identifier,
                        status=result['status'],
                        annotation_result=result.get('annotation_result'),
                        error_message=result.get('error_message')
                    )
                else:
                    # 传统 dry-run 模式，模拟保存并跳过实际保存
                    logger.info(f"[Dry-run] 模拟保存结果 for poem_id: {result['poem_id']}")
                
                if result['status'] == 'completed':
                    completed_count += 1
                else:
                    failed_count += 1
                progress_bar.set_postfix({'成功': completed_count, '失败': failed_count})
                progress_bar.update(1)
                continue # 跳过数据库保存

            # 非 dry-run 模式，保存结果到数据库
            await data_manager.save_annotation(
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
        # 在模型特定日志中也记录任务总结
        # self.model_logger.info(  # 已注释：不再使用模型特定日志
        #     f"任务完成! "
        #     f"耗时: {execution_time:.2f}秒 (平均 {avg_time_per_poem:.2f}秒/首), "
        #     f"总计: {total_poems}, 成功: {completed_count} ({success_rate:.1f}%), 失败: {failed_count}"
        # )
        logger.info(
            f"任务完成! "
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

    async def _save_dry_run_annotation_to_json(self, 
                                                poem_id: int, 
                                                model_identifier: str, 
                                                status: str, 
                                                annotation_result: Optional[str], 
                                                error_message: Optional[str]):
        """
        在 full dry-run 模式下，将标注结果保存到 JSONL 文件。
        """
        if not self.dry_run_output_file:
            logger.error("Dry-run output file path is not set. Cannot save dry-run annotation.")
            return

        data_to_save = {
            "timestamp": datetime.now().isoformat(),
            "poem_id": poem_id,
            "model_identifier": model_identifier,
            "status": status,
            "annotation_result": json.loads(annotation_result) if annotation_result else None,
            "error_message": error_message
        }

        try:
            # 确保目录存在
            self.dry_run_output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 以追加模式写入 JSONL 文件
            async with asyncio.Lock(): # 使用锁确保并发写入时的文件完整性
                with open(self.dry_run_output_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(data_to_save, ensure_ascii=False) + '\n')
            logger.debug(f"Dry-run annotation for poem_id {poem_id} saved to {self.dry_run_output_file}")
        except Exception as e:
            logger.error(f"Failed to save dry-run annotation for poem_id {poem_id} to JSON file: {e}", exc_info=True)
