"""
数据模型定义插件实现
"""
from typing import Type, Dict, Any, List
from dataclasses import make_dataclass, field
from src.data.model_plugin_interface import ModelDefinitionPlugin
from src.data.model_serialization_plugin import DataModelSerializationPlugin


class DataModelDefinitionPlugin(ModelDefinitionPlugin):
    """数据模型定义插件"""
    
    def __init__(self):
        # 初始化序列化插件
        self.serialization_plugin = DataModelSerializationPlugin()
        # 缓存已创建的模型类
        self._model_classes = {}
    
    def get_name(self) -> str:
        return "data_model_definition"
    
    def get_description(self) -> str:
        return "数据模型定义插件，提供诗词、作者、标注等相关数据模型"
    
    def get_model_classes(self) -> Dict[str, Type]:
        """获取模型类字典"""
        # 如果还未创建模型类，则创建它们
        if not self._model_classes:
            self._create_all_model_classes()
        return self._model_classes
    
    def _create_all_model_classes(self):
        """创建所有模型类"""
        # 定义模型字段
        model_fields = {
            "Poem": [
                ("id", int),
                ("title", str),
                ("author", str),
                ("paragraphs", List[str]),
                ("full_text", str),
                ("author_desc", str, field(default="")),
                ("data_status", str, field(default="active")),
                ("pre_classification", str, field(default=None)),
                ("created_at", str, field(default=None)),
                ("updated_at", str, field(default=None))
            ],
            "Author": [
                ("name", str),
                ("description", str, field(default="")),
                ("short_description", str, field(default="")),
                ("created_at", str, field(default=None))
            ],
            "StrategyCategory": [
                ("id", str),
                ("name_zh", str),
                ("name_en", str, field(default=None)),
                ("category_type", str),  # relationship_action, emotional_strategy, communication_scene, risk_level
                ("parent_id", str, field(default=None)),
                ("level", int)
            ],
            "Annotation": [
                ("id", int, field(default=None)),
                ("poem_id", int),
                ("model_identifier", str),
                ("status", str),  # 'completed' or 'failed'
                ("annotation_result", str, field(default=None)),
                ("error_message", str, field(default=None)),
                ("created_at", str, field(default=None)),
                ("updated_at", str, field(default=None))
            ],
            "SentenceAnnotation": [
                ("id", int, field(default=None)),
                ("annotation_id", int),
                ("poem_id", int),
                ("sentence_uid", str),
                ("sentence_text", str)
            ],
            "SentenceStrategyLink": [
                ("sentence_annotation_id", int),
                ("strategy_id", str),
                ("strategy_type", str),  # relationship_action, emotional_strategy, communication_scene, risk_level
                ("is_primary", bool)
            ]
        }
        
        # 创建模型类
        for model_name, fields in model_fields.items():
            self._model_classes[model_name] = make_dataclass(model_name, fields)
    
    def create_model_instance(self, model_name: str, data: Dict[str, Any]):
        """创建模型实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get(model_name)
        
        if model_class:
            # 使用序列化插件来创建实例
            return self.serialization_plugin.deserialize_model(model_class, data)
        else:
            raise ValueError(f"未知的模型名称: {model_name}")
    
    def get_model_fields(self, model_name: str) -> List[str]:
        """获取模型字段列表"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get(model_name)
        
        if model_class:
            # 使用序列化插件来获取字段信息
            return self.serialization_plugin.get_model_fields(model_class)
        else:
            raise ValueError(f"未知的模型名称: {model_name}")