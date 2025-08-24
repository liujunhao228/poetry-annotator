"""
数据模型序列化插件实现
"""
import json
from typing import Dict, Any, List
from src.data.model_serialization_plugin_interface import ModelSerializationPlugin
from dataclasses import fields, is_dataclass


class DataModelSerializationPlugin(ModelSerializationPlugin):
    """数据模型序列化插件"""
    
    def get_name(self) -> str:
        return "data_model_serialization"
    
    def get_description(self) -> str:
        return "数据模型序列化插件，提供诗词、作者、标注等相关数据模型的序列化和反序列化功能"
    
    def serialize_model(self, model_instance: Any) -> Dict[str, Any]:
        """将模型实例序列化为字典"""
        if not is_dataclass(model_instance):
            raise ValueError("模型实例必须是dataclass类型")
        
        # 获取模型类名
        model_name = type(model_instance).__name__
        
        # 根据模型类型进行特殊处理
        if model_name == "Poem":
            return self._serialize_poem(model_instance)
        elif model_name == "Author":
            return self._serialize_author(model_instance)
        elif model_name == "StrategyCategory":
            return self._serialize_strategy_category(model_instance)
        elif model_name == "Annotation":
            return self._serialize_annotation(model_instance)
        elif model_name == "SentenceAnnotation":
            return self._serialize_sentence_annotation(model_instance)
        elif model_name == "SentenceStrategyLink":
            return self._serialize_sentence_strategy_link(model_instance)
        else:
            # 默认序列化
            return {field.name: getattr(model_instance, field.name) for field in fields(model_instance)}
    
    def deserialize_model(self, model_class: type, data: Dict[str, Any]) -> Any:
        """从字典反序列化为模型实例"""
        # 根据模型类型进行特殊处理
        model_name = model_class.__name__
        if model_name == "Poem":
            return self._deserialize_poem(model_class, data)
        elif model_name == "Author":
            return self._deserialize_author(model_class, data)
        elif model_name == "StrategyCategory":
            return self._deserialize_strategy_category(model_class, data)
        elif model_name == "Annotation":
            return self._deserialize_annotation(model_class, data)
        elif model_name == "SentenceAnnotation":
            return self._deserialize_sentence_annotation(model_class, data)
        elif model_name == "SentenceStrategyLink":
            return self._deserialize_sentence_strategy_link(model_class, data)
        else:
            # 默认反序列化
            return model_class(**data)
    
    def get_model_fields(self, model_class: type) -> List[str]:
        """获取模型字段列表"""
        if not is_dataclass(model_class):
            raise ValueError("模型类必须是dataclass类型")
        
        return [field.name for field in fields(model_class)]
    
    def _serialize_poem(self, poem) -> Dict[str, Any]:
        """序列化Poem实例"""
        return {
            'id': poem.id,
            'title': poem.title,
            'author': poem.author,
            'paragraphs': poem.paragraphs,
            'full_text': poem.full_text,
            'author_desc': poem.author_desc,
            'data_status': poem.data_status,
            'pre_classification': poem.pre_classification,
            'created_at': poem.created_at,
            'updated_at': poem.updated_at
        }
    
    def _serialize_author(self, author) -> Dict[str, Any]:
        """序列化Author实例"""
        return {
            'name': author.name,
            'description': author.description,
            'short_description': author.short_description,
            'created_at': author.created_at
        }
    
    def _serialize_strategy_category(self, category) -> Dict[str, Any]:
        """序列化StrategyCategory实例"""
        return {
            'id': category.id,
            'name_zh': category.name_zh,
            'name_en': category.name_en,
            'category_type': category.category_type,
            'parent_id': category.parent_id,
            'level': category.level
        }
    
    def _serialize_annotation(self, annotation) -> Dict[str, Any]:
        """序列化Annotation实例"""
        return {
            'id': annotation.id,
            'poem_id': annotation.poem_id,
            'model_identifier': annotation.model_identifier,
            'status': annotation.status,
            'annotation_result': annotation.annotation_result,
            'error_message': annotation.error_message,
            'created_at': annotation.created_at,
            'updated_at': annotation.updated_at
        }
    
    def _serialize_sentence_annotation(self, sentence_annotation) -> Dict[str, Any]:
        """序列化SentenceAnnotation实例"""
        return {
            'id': sentence_annotation.id,
            'annotation_id': sentence_annotation.annotation_id,
            'poem_id': sentence_annotation.poem_id,
            'sentence_uid': sentence_annotation.sentence_uid,
            'sentence_text': sentence_annotation.sentence_text
        }
    
    def _serialize_sentence_strategy_link(self, link) -> Dict[str, Any]:
        """序列化SentenceStrategyLink实例"""
        return {
            'sentence_annotation_id': link.sentence_annotation_id,
            'strategy_id': link.strategy_id,
            'strategy_type': link.strategy_type,
            'is_primary': link.is_primary
        }
    
    def _deserialize_poem(self, model_class, data: Dict[str, Any]):
        """从字典创建Poem实例"""
        # 处理title/rhythmic字段差异
        if 'rhythmic' in data and 'title' not in data:
            data['title'] = data['rhythmic']
        elif 'title' in data and 'rhythmic' not in data:
            data['rhythmic'] = data['title']
        
        # 处理paragraphs JSON字符串
        if isinstance(data.get('paragraphs'), str):
            try:
                data['paragraphs'] = json.loads(data['paragraphs'])
            except json.JSONDecodeError:
                data['paragraphs'] = [data['paragraphs']]
        
        # 确保必要的字段存在
        if 'full_text' not in data:
            data['full_text'] = ""
        if 'author_desc' not in data:
            data['author_desc'] = ""
        if 'data_status' not in data:
            data['data_status'] = "active"
        
        return model_class(**data)
    
    def _deserialize_author(self, model_class, data: Dict[str, Any]):
        """从字典创建Author实例"""
        return model_class(**data)
    
    def _deserialize_strategy_category(self, model_class, data: Dict[str, Any]):
        """从字典创建StrategyCategory实例"""
        return model_class(**data)
    
    def _deserialize_annotation(self, model_class, data: Dict[str, Any]):
        """从字典创建Annotation实例"""
        return model_class(**data)
    
    def _deserialize_sentence_annotation(self, model_class, data: Dict[str, Any]):
        """从字典创建SentenceAnnotation实例"""
        return model_class(**data)
    
    def _deserialize_sentence_strategy_link(self, model_class, data: Dict[str, Any]):
        """从字典创建SentenceStrategyLink实例"""
        return model_class(**data)