# 基类
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import json
import logging
import os
from pathlib import Path
from ..llm_response_parser import llm_response_parser
from ..config_manager import config_manager

class BaseLLMService(ABC):
    """LLM服务抽象基类 (已重构)"""
    def __init__(self, config: Dict[str, Any], model_config_name: str):
        """
        [修改] 构造函数现在接收完整的配置字典
        """
        self.config = config
        self.model_config_name = model_config_name
        self.logger = logging.getLogger(self.__class__.__name__)

        # [修改] 从配置字典中提取基础信息
        self.provider = self.config.get('provider', 'unknown')
        self.model = self.config.get('model_name')
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url')

        if not self.model or not self.api_key:
            raise ValueError(f"模型配置 '{model_config_name}' 必须包含 'model_name' 和 'api_key' 字段。")

        if self.api_key in ['your_gemini_api_key_here', 'your_siliconflow_api_key_here', '']:
            raise ValueError(f"模型配置 '{model_config_name}' 的API密钥未正确配置。 ")

        # 初始化模板变量
        self.system_prompt_template: Optional[str] = None
        self.user_prompt_template: Optional[str] = None

        # 加载提示词模板
        self._load_prompt_templates()

    def _load_prompt_templates(self):
        """
        [重构] 统一加载提示词模板的逻辑。
        """
        try:
            # 优先使用模型特定的模板配置
            prompt_config = config_manager.get_model_prompt_config(self.model_config_name)
            self.logger.info(f"为模型 '{self.model_config_name}' 加载提示词模板... ")
        except Exception as e:
            self.logger.warning(f"无法获取模型 '{self.model_config_name}' 的特定提示词配置，将回退到全局默认配置: {e} ")
            prompt_config = config_manager.get_prompt_config()

        system_path = prompt_config.get('system_prompt_template')
        user_path = prompt_config.get('user_prompt_template')

        if system_path:
            self.system_prompt_template = self._load_template_file(system_path)
            self.logger.info(f"系统提示词模板加载成功: {system_path} ")
        else:
            raise ValueError("系统提示词模板路径未配置 ")

        if user_path:
            self.user_prompt_template = self._load_template_file(user_path)
            self.logger.info(f"用户提示词模板加载成功: {user_path} ")
        else:
            raise ValueError("用户提示词模板路径未配置 ")

    def _load_template_file(self, template_path: str) -> str:
        """
        加载模板文件内容
        """
        # (此方法保持不变，但为便于完整性而包含)
        try:
            if not os.path.isabs(template_path):
                project_root = Path(__file__).parent.parent.parent
                template_path_abs = project_root / template_path
            else:
                template_path_abs = Path(template_path)

            if not template_path_abs.exists():
                raise FileNotFoundError(f"模板文件不存在: {template_path_abs}")

            content = template_path_abs.read_text(encoding='utf-8')

            if not content.strip():
                raise ValueError(f"模板文件为空: {template_path_abs} ")
            self.logger.debug(f"成功加载模板文件: {template_path_abs} (大小: {len(content)} 字符) ")
            return content

        except Exception as e:
            self.logger.error(f"加载模板文件失败 '{template_path}': {e} ")
            raise

    # [已移除] build_system_prompt 和 build_user_prompt 方法
    # 它们的功能被下面的 _build_* 方法和 prepare_prompts 取代

    def _build_system_prompt(self, emotion_schema: str) -> str:
        """
        [新] 构建系统提示词的内部方法
        """
        if self.system_prompt_template is None:
            raise RuntimeError("系统提示词模板未加载。 ")
        return self.system_prompt_template.replace("{emotion_schema} ", emotion_schema)

    def _build_user_prompt(self, author: str, rhythmic: str, sentences_with_id_json: str) -> str:
        """
        [新] 构建用户提示词的内部方法
        """
        if self.user_prompt_template is None:
            raise RuntimeError("用户提示词模板未加载。 ")
        return self.user_prompt_template.format(
            author=author,
            rhythmic=rhythmic,
            sentences_with_id_json=sentences_with_id_json
        )

    def _generate_sentences_with_id(self, paragraphs: List[str]) -> List[Dict[str, str]]:
        """
        [新] 为句子生成ID并构建JSON格式（从Annotator迁移而来）
        """
        return [{"id": f"S{i+1} ", "sentence": sentence} for i, sentence in enumerate(paragraphs)]

    def prepare_prompts(self, poem_data: Dict[str, Any], emotion_schema: str) -> Tuple[str, str]:
        """
        [新] 集中化的提示词构建逻辑。
        这是服务类提供给外部的核心能力之一。
        """
        sentences_with_id = self._generate_sentences_with_id(poem_data['paragraphs'])
        sentences_json = json.dumps(sentences_with_id, ensure_ascii=False, indent=2)

        system_prompt = self._build_system_prompt(emotion_schema)
        user_prompt = self._build_user_prompt(
            author=poem_data['author'],
            rhythmic=poem_data['rhythmic'],
            sentences_with_id_json=sentences_json
        )
        return system_prompt, user_prompt

    @abstractmethod
    async def annotate_poem(self, poem: Dict[str, Any], emotion_schema: str) -> Dict[str, Any]:
        """
        [修改] 抽象方法签名已更新。
        现在接收原始诗词数据和情感体系，负责完整的标注流程。

        Args:
            poem: 包含诗词信息的字典。
            emotion_schema: 情感分类体系的文本。

        Returns:
            包含标注结果的字典。
        """
        pass

    def log_request_details(self, request_data: Dict[str, Any], prompt: str):
        """记录完整的请求详情"""
        log_data = request_data.copy()
        if 'headers' in log_data and 'Authorization' in log_data['headers']:
            auth_header = log_data['headers']['Authorization']
            if auth_header.startswith('Bearer '):
                log_data['headers']['Authorization'] = f"Bearer {'*' * 20}"
        self.logger.debug("=" * 80)
        self.logger.debug(f"[{self.provider.upper()}] 完整请求详情:")
        self.logger.debug(f"API端点: {self.base_url}")
        self.logger.debug(f"模型: {self.model}")
        self.logger.debug(f"完整提示词内容（变量替换后）: {prompt}")
        self.logger.debug(f"请求数据: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
        self.logger.debug("=" * 80)

    def log_response_details(self, response_data: Dict[str, Any], usage: Optional[Dict[str, Any]] = None):
        """记录完整的响应详情"""
        self.logger.debug("=" * 80)
        self.logger.debug(f"[{self.provider.upper()}] 完整响应详情:")
        self.logger.debug(f"响应状态: 成功")
        if usage:
            self.logger.debug(f"Token使用情况: {usage}")
        self.logger.debug(f"完整原始响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        self.logger.debug("=" * 80)

    def log_error_details(self, error: Exception, request_data: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None):
        """记录错误详情"""
        self.logger.debug("=" * 80)
        self.logger.debug(f"[{self.provider.upper()}] 错误详情:")
        self.logger.debug(f"错误类型: {type(error).__name__}")
        self.logger.debug(f"错误信息: {str(error)}")
        if request_data:
            log_data = request_data.copy()
            if 'headers' in log_data and 'Authorization' in log_data['headers']:
                auth_header = log_data['headers']['Authorization']
                if auth_header.startswith('Bearer '):
                    log_data['headers']['Authorization'] = f"Bearer {'*' * 20}"
            self.logger.debug(f"请求数据: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
        if prompt:
            self.logger.debug(f"用户提示词: {prompt}")
        self.logger.debug("=" * 80)

    def validate_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        [已重构] 使用集成了验证逻辑的解析器，对LLM响应进行原子化的解析与验证。
        此方法现在完全委托 `llm_response_parser` 来完成所有工作。
        解析器会尝试多种策略从文本中提取一个JSON数组，并立即验证其内容
        是否符合业务规范（包含'id', 'primary', 'secondary'等字段和正确类型）。
        只有完全通过验证的结果才会被返回。
        Args:
            response_text: LLM的原始响应文本。
        Returns:
            一个经过完全验证的、包含标注信息的字典列表。
        Raises:
            ValueError: 如果响应无法被解析，或者解析后的所有内容都不符合业务规范。
        """
        try:
            self.logger.debug("开始使用LLMResponseParser统一解析并验证响应...")
            # 只需要调用一次 parse，它会处理所有解析和验证的复杂逻辑
            validated_list = llm_response_parser.parse(response_text)
            self.logger.info(f"响应解析及内容验证成功，共 {len(validated_list)} 条标注记录。")
            return validated_list
        except (ValueError, TypeError) as e:
            # 捕获解析器抛出的最终错误
            self.logger.error(f"响应统一解析验证失败: {e}", exc_info=True)
            self.logger.debug(f"导致失败的原始响应内容: {response_text}")
            raise # 将异常向上抛出，由调用方(例如 Annotator)捕获并处理

    # [已移除] _validate_annotation_list_content 方法已被移除，
    # 其功能已完全整合进 llm_response_parser.py 中，实现了解析与验证的统一。

    def format_error_response(self, error: str) -> Dict[str, Any]:
        """
        格式化标准化的错误响应。
        Args:
            error: 错误信息。
        Returns:
            一个包含错误信息的字典。
        """
        return {
            "error": str(error)
        }

    def log_annotation(self, poem_id: int, success: bool,
                      result: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None):
        """记录标注日志"""
        if success:
            primary_emotion = result.get('primary_emotion', '未知') if result is not None else '未知'
            self.logger.info(f"诗词 {poem_id} 标注成功: {primary_emotion}")
        else:
            self.logger.error(f"诗词 {poem_id} 标注失败: {error}")

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url
        }
