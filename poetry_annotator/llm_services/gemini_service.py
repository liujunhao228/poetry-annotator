"""
Google Gemini API 服务实现
"""

from typing import Dict, Any, Tuple
import httpx

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    from google.api_core import exceptions as google_exceptions
except ImportError:
    genai = None
    google_exceptions = None

from .base_service import BaseLLMService


class GeminiService(BaseLLMService):
    """Google Gemini API 服务实现"""

    def __init__(self, config: Dict[str, Any], model_config_name: str):
        super().__init__(config, model_config_name)
        self._parse_and_validate_config()
        self._initialize_gemini_model()
        self._log_initialization()

    def _parse_and_validate_config(self):
        self.temperature = float(self.config.get('temperature', 0.3))
        self.max_tokens = int(self.config.get('max_tokens', 65535))
        self.timeout = int(self.config.get('timeout', 120))
        self.top_p = float(self.config.get('top_p', 1.0))
        self.top_k = int(self.config.get('top_k', 40))
        self.candidate_count = int(self.config.get('candidate_count', 1))

        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature 必须在 0.0 和 2.0 之间。")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0。")
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于 0。")

        stop_raw = self.config.get('stop_sequences')
        self.stop_sequences = [s.strip() for s in stop_raw.split(',') if s.strip()] if stop_raw else None

        self.thinking_budget = self.config.get('thinking_budget')
        if self.thinking_budget:
            self.thinking_budget = int(self.thinking_budget)

    def _initialize_gemini_model(self):
        if genai is None:
            raise ImportError("google.generativeai 库未安装，请运行 pip install google-generativeai")

        genai.configure(api_key=self.api_key)

        self.generation_config_dict = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "candidate_count": self.candidate_count,
        }
        if self.stop_sequences:
            self.generation_config_dict["stop_sequences"] = self.stop_sequences

        self.generation_config = genai.types.GenerationConfig(**self.generation_config_dict)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        self.safety_settings_dict = {k.name: v.name for k, v in safety_settings.items()}

        self.genai_model = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.generation_config,
            safety_settings=safety_settings
        )

    def _log_initialization(self):
        self.logger.info(f"[Gemini] 服务初始化完成 - 模型：{self.model}")

    async def health_check(self) -> Tuple[bool, str]:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:countTokens?key={self.api_key}"
                response = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": "hello"}]}]},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                return True, "API connection and key are valid."
        except httpx.HTTPStatusError as e:
            return False, f"HTTP {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    async def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        try:
            request_options = {'timeout': self.timeout}
            if self.thinking_budget:
                request_options['thinking_budget'] = self.thinking_budget

            await self._ensure_rate_limiter()
            if self.rate_limiter:
                await self.rate_limiter.acquire()

            response = await self.genai_model.generate_content_async(
                [system_prompt, user_prompt],
                request_options=request_options
            )

            return response.text

        except (google_exceptions.RetryError, google_exceptions.DeadlineExceeded) as e:
            self.log_error_details(e, None, full_prompt)
            raise
        except (google_exceptions.GoogleAPICallError, google_exceptions.InvalidArgument) as e:
            self.log_error_details(e, None, full_prompt)
            raise ValueError(f"Gemini API Error: {e}") from e
        except Exception as e:
            self.log_error_details(e, None, full_prompt)
            raise

    def get_service_info(self) -> Dict[str, Any]:
        info = super().get_service_info()
        info.update({
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "candidate_count": self.candidate_count,
            "stop_sequences": self.stop_sequences,
            "thinking_budget": self.thinking_budget,
            "safety_settings": self.safety_settings_dict,
        })
        return self._mask_sensitive_data(info)
