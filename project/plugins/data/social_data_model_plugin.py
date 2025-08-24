"""
《交际诗分析》项目专用数据模型定义插件
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import make_dataclass, field
from src.data.model_plugin_interface import ModelDefinitionPlugin
from src.data.model_serialization_plugin_interface import ModelSerializationPlugin


class SocialPoemAnalysisDataModelPlugin(ModelDefinitionPlugin, ModelSerializationPlugin):
    """《交际诗分析》项目专用数据模型定义插件"""
    
    def __init__(self):
        # 缓存已创建的模型类
        self._model_classes = {}
        # 缓存模型定义
        self._model_definitions = None
        # 缓存序列化器
        self._serializers = None
    
    def get_name(self) -> str:
        return "social_poem_analysis_data_model"
        
    def get_description(self) -> str:
        return "《交际诗分析》项目专用数据模型定义插件"
    
    def _get_model_definitions(self) -> Dict[str, Any]:
        """获取数据模型定义"""
        if self._model_definitions is None:
            self._model_definitions = {
                "Poem": [
                    ("id", int),
                    ("title", str),
                    ("author", str),
                    ("dynasty", str),
                    ("content", List[str]),
                    ("created_at", str, field(default=None))
                ],
                "Author": [
                    ("id", int),
                    ("name", str),
                    ("dynasty", str),
                    ("bio", str),
                    ("created_at", str, field(default=None))
                ],
                "StrategyCategory": [
                    ("id", str),
                    ("dimension", str),  # 维度名称
                    ("name_zh", str),    # 中文名称
                    ("name_en", str),    # 英文名称
                    ("description", str), # 描述
                    ("created_at", str, field(default=None))
                ],
                "Annotation": [
                    ("id", int),
                    ("poem_id", int),
                    ("annotator", str),
                    ("status", str),
                    ("created_at", str, field(default=None)),
                    ("updated_at", str, field(default=None))
                ],
                "SentenceAnnotation": [
                    ("id", int),
                    ("annotation_id", int),
                    ("sentence_id", str),  # 句子ID，如"S1", "S2"
                    ("relationship_action", str),  # RA编码
                    ("emotional_strategy", str),   # ES编码
                    ("communication_scene", List[str]),  # SC编码列表
                    ("risk_level", str),   # RS编码
                    ("rationale", str),    # 理由
                    ("created_at", str, field(default=None))
                ],
                "SentenceStrategyLink": [
                    ("id", int),
                    ("sentence_annotation_id", int),
                    ("strategy_code", str),  # 策略编码，如"RA01", "ES02"等
                    ("dimension", str),      # 维度，如"relationship_action"
                    ("created_at", str, field(default=None))
                ]
            }
        return self._model_definitions
    
    def _get_serializers(self) -> Dict[str, Any]:
        """获取数据模型序列化器"""
        if self._serializers is None:
            self._serializers = {
                "Poem": {
                    "serialize": self._serialize_poem,
                    "deserialize": self._deserialize_poem
                },
                "Author": {
                    "serialize": self._serialize_author,
                    "deserialize": self._deserialize_author
                },
                "StrategyCategory": {
                    "serialize": self._serialize_strategy_category,
                    "deserialize": self._deserialize_strategy_category
                },
                "Annotation": {
                    "serialize": self._serialize_annotation,
                    "deserialize": self._deserialize_annotation
                },
                "SentenceAnnotation": {
                    "serialize": self._serialize_sentence_annotation,
                    "deserialize": self._deserialize_sentence_annotation
                },
                "SentenceStrategyLink": {
                    "serialize": self._serialize_sentence_strategy_link,
                    "deserialize": self._deserialize_sentence_strategy_link
                }
            }
        return self._serializers
    
    def get_model_classes(self) -> Dict[str, Type]:
        """获取模型类字典"""
        if not self._model_classes:
            model_definitions = self._get_model_definitions()
            for model_name, fields in model_definitions.items():
                self._model_classes[model_name] = make_dataclass(model_name, fields)
        return self._model_classes
    
    def create_model_instance(self, model_name: str, data: Dict[str, Any]):
        """创建模型实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get(model_name)
        
        if model_class:
            # 使用反序列化器创建实例
            serializers = self._get_serializers()
            deserializer = serializers.get(model_name, {}).get("deserialize")
            if deserializer:
                return deserializer(data)
            else:
                # 默认创建
                return model_class(**data)
        else:
            raise ValueError(f"未知的模型名称: {model_name}")
    
    def get_model_fields(self, model_name: str) -> List[str]:
        """获取模型字段列表"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get(model_name)
        
        if model_class:
            from dataclasses import fields
            return [f.name for f in fields(model_class)]
        else:
            raise ValueError(f"未知的模型名称: {model_name}")
    
    def serialize_model(self, model_instance) -> Dict[str, Any]:
        """将模型实例序列化为字典"""
        from dataclasses import is_dataclass
        if not is_dataclass(model_instance):
            raise ValueError("模型实例必须是dataclass类型")
        
        # 获取模型类名
        model_name = type(model_instance).__name__
        
        # 使用序列化器进行序列化
        serializers = self._get_serializers()
        serializer = serializers.get(model_name, {}).get("serialize")
        if serializer:
            return serializer(model_instance)
        else:
            # 默认序列化
            from dataclasses import fields
            return {field.name: getattr(model_instance, field.name) for field in fields(model_instance)}
    
    def deserialize_model(self, model_class: type, data: Dict[str, Any]):
        """从字典反序列化为模型实例"""
        model_name = model_class.__name__
        
        # 使用反序列化器进行反序列化
        serializers = self._get_serializers()
        deserializer = serializers.get(model_name, {}).get("deserialize")
        if deserializer:
            return deserializer(data)
        else:
            # 默认反序列化
            return model_class(**data)
    
    def get_model_fields_for_serialization(self, model_class: type) -> List[str]:
        """获取模型字段列表（用于序列化）"""
        from dataclasses import is_dataclass, fields
        if not is_dataclass(model_class):
            raise ValueError("模型类必须是dataclass类型")
        
        return [field.name for field in fields(model_class)]
    
    # 序列化方法
    def _serialize_poem(self, instance) -> Dict[str, Any]:
        """序列化Poem实例"""
        return {
            "id": instance.id,
            "title": instance.title,
            "author": instance.author,
            "dynasty": instance.dynasty,
            "content": instance.content,
            "created_at": instance.created_at
        }
    
    def _serialize_author(self, instance) -> Dict[str, Any]:
        """序列化Author实例"""
        return {
            "id": instance.id,
            "name": instance.name,
            "dynasty": instance.dynasty,
            "bio": instance.bio,
            "created_at": instance.created_at
        }
    
    def _serialize_strategy_category(self, instance) -> Dict[str, Any]:
        """序列化StrategyCategory实例"""
        return {
            "id": instance.id,
            "dimension": instance.dimension,
            "name_zh": instance.name_zh,
            "name_en": instance.name_en,
            "description": instance.description,
            "created_at": instance.created_at
        }
    
    def _serialize_annotation(self, instance) -> Dict[str, Any]:
        """序列化Annotation实例"""
        return {
            "id": instance.id,
            "poem_id": instance.poem_id,
            "annotator": instance.annotator,
            "status": instance.status,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at
        }
    
    def _serialize_sentence_annotation(self, instance) -> Dict[str, Any]:
        """序列化SentenceAnnotation实例"""
        return {
            "id": instance.id,
            "annotation_id": instance.annotation_id,
            "sentence_id": instance.sentence_id,
            "relationship_action": instance.relationship_action,
            "emotional_strategy": instance.emotional_strategy,
            "communication_scene": instance.communication_scene,
            "risk_level": instance.risk_level,
            "rationale": instance.rationale,
            "created_at": instance.created_at
        }
    
    def _serialize_sentence_strategy_link(self, instance) -> Dict[str, Any]:
        """序列化SentenceStrategyLink实例"""
        return {
            "id": instance.id,
            "sentence_annotation_id": instance.sentence_annotation_id,
            "strategy_code": instance.strategy_code,
            "dimension": instance.dimension,
            "created_at": instance.created_at
        }
    
    # 反序列化方法
    def _deserialize_poem(self, data: Dict[str, Any]):
        """反序列化Poem实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("Poem")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            return model_class(**data)
        return None
    
    def _deserialize_author(self, data: Dict[str, Any]):
        """反序列化Author实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("Author")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            return model_class(**data)
        return None
    
    def _deserialize_strategy_category(self, data: Dict[str, Any]):
        """反序列化StrategyCategory实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("StrategyCategory")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            return model_class(**data)
        return None
    
    def _deserialize_annotation(self, data: Dict[str, Any]):
        """反序列化Annotation实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("Annotation")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            if "updated_at" not in data:
                data["updated_at"] = None
            return model_class(**data)
        return None
    
    def _deserialize_sentence_annotation(self, data: Dict[str, Any]):
        """反序列化SentenceAnnotation实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("SentenceAnnotation")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            return model_class(**data)
        return None
    
    def _deserialize_sentence_strategy_link(self, data: Dict[str, Any]):
        """反序列化SentenceStrategyLink实例"""
        model_classes = self.get_model_classes()
        model_class = model_classes.get("SentenceStrategyLink")
        if model_class:
            # 处理默认值
            if "created_at" not in data:
                data["created_at"] = None
            return model_class(**data)
        return None