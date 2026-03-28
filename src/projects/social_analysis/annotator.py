"""
社会分析项目标注器

Social Analysis Project Annotator
"""

import json
import logging
from typing import Dict, Any, List

from src.core.base_annotator import BaseAnnotator
from .schema import SocialAnalysisSchema
from .prompts import SocialAnalysisPromptBuilder
from poetry_annotator.annotation_data_logger import AnnotationDataLogger


class SocialAnalysisAnnotator(BaseAnnotator):
    """
    社会分析项目专用标注器
    
    继承通用标注框架，实现社会分析特定的：
    - Schema 定义
    - Prompt 构建
    - 响应验证
    """
    
    def __init__(self, config_name: str, project_context: Any):
        # 从项目上下文获取配置
        config_manager = project_context.config_manager
        llm_config = config_manager.get_llm_config()
        
        super().__init__(
            config_name=config_name,
            project_context=project_context,
            max_workers=llm_config.get('max_workers', 5),
            max_retries=llm_config.get('max_retries', 3),
            retry_delay_multiplier=llm_config.get('retry_delay', 1.0),
            retry_max_wait=llm_config.get('retry_max_wait', 60.0)
        )
    
    def _init_custom(self) -> None:
        """初始化社会分析特定组件"""
        self.schema = SocialAnalysisSchema()
        self.prompt_builder = SocialAnalysisPromptBuilder()
        self.annotation_data_logger = AnnotationDataLogger(self.config_name)
        self.logger.info("社会分析标注器初始化完成")
    
    def _get_schema(self) -> SocialAnalysisSchema:
        """获取社会分析 schema"""
        return self.schema
    
    def _get_prompt_builder(self) -> SocialAnalysisPromptBuilder:
        """获取社会分析 prompt 构建器"""
        return self.prompt_builder
    
    def _validate_response(
        self, 
        llm_output: List[Dict[str, Any]], 
        input_sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证并转换社会分析响应
        
        Args:
            llm_output: LLM 原始输出
            input_sentences: 输入句子列表
            
        Returns:
            验证后的标注结果
        """
        return self.schema.validate_response(llm_output, input_sentences)
    
    async def _annotate_single_poem(self, poem: Dict[str, Any]) -> Dict[str, Any]:
        """
        标注单首诗词（社会分析特定实现）
        
        在通用流程基础上，添加社会分析特定的日志记录
        """
        poem_id = poem['id']
        self.logger.info(f"开始处理诗词 ID: {poem_id}")
        self.logger.debug(f"诗词 ID {poem_id} 内容：{poem}")
        
        # 调用父类的标注逻辑
        result = await super()._annotate_single_poem(poem)
        
        # 记录标注数据到集合日志
        if result['status'] == 'completed' and result.get('annotation_result'):
            try:
                annotation_data = json.loads(result['annotation_result'])
                self.annotation_data_logger.log_annotation_data(poem_id, annotation_data)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"记录标注数据失败 (ID {poem_id}): {e}")
                self.annotation_data_logger.log_annotation_data(
                    poem_id, 
                    {"status": "failed", "error_message": str(e)}
                )
        else:
            self.annotation_data_logger.log_annotation_data(
                poem_id,
                {"status": "failed", "error_message": result.get('error_message')}
            )
        
        return result
