"""假数据工厂"""

from typing import Dict, Any, Optional, Callable
from .service import FakeDataService
from src.llm_services.schemas import PoemData, EmotionSchema


class FakeDataFactory:
    """假数据工厂类"""
    
    @staticmethod
    def create_fake_service(config: Dict[str, Any], model_config_name: str, 
                          response_parser=None, 
                          annotation_generator: Optional[Callable[[PoemData, EmotionSchema], list]] = None) -> FakeDataService:
        """创建假数据服务实例"""
        service = FakeDataService(config, model_config_name, response_parser)
        if annotation_generator:
            service.set_annotation_generator(annotation_generator)
        return service